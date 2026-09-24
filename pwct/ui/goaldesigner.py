"""RPWI Environment (Goal Designer) - port of rpwi.scx.

The steps tree, the left tool bar (New / Edit / Delete / Up / Down / Interact /
Modify), the Time Machine and the Steps Tree / Step Code views.
"""

import copy
import tkinter as tk
from tkinter import ttk, messagebox

from .. import codegen
from ..engine import InteractionError
from ..model import Interaction, Step
from ..rules import ALLOW_SUB_LEAF, LEAF
from .browser import ComponentsBrowser
from .common import (Gradient, ScrolledText, ToolTip, ask_string, highlight_python,
                     icon_button, image, PURPLE, UI_BOLD, UI_FONT, Dialog)
from .interaction import InteractionWindow



class GoalDesigner(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg="#ffffff")
        self.app = app
        self.goal = None
        self.frame_no = None        # Time Machine: None = the last time frame (live)
        self.collapsed = set()
        self.clipboard = None
        self.last_domain = None
        self.view = tk.StringVar(value="tree")
        self.movie_job = None
        self._build()

    # ================================================================ UI
    def _build(self):
        s = self.app.settings
        # ---------------------------------------------------------- header
        h = self.header = Gradient(self, height=100)
        h.pack(fill="x")
        h.create_text(0, 16, text="Goal Designer", font=("Segoe UI", 11, "bold"), tags="title")
        h.create_line(0, 33, 4000, 33, fill="#808080")
        h.create_line(0, 34, 4000, 34, fill="#ffffff")
        h.bind("<Configure>", lambda e: h.coords("title", e.width // 2, 16), add="+")

        h.create_text(47, 50, text="Active Goal :", anchor="w", font=UI_BOLD)
        self.goal_combo = ttk.Combobox(h, state="readonly", width=16, font=UI_FONT)
        self.goal_combo.bind("<<ComboboxSelected>>", lambda e: self.select_goal(self.goal_combo.get()))
        h.create_window(128, 50, window=self.goal_combo, anchor="w")

        self.sde = tk.IntVar(value=1 if s.syntax_directed else 0)
        cb = tk.Checkbutton(h, text="Syntax Directed Editor", variable=self.sde, indicatoron=False,
                            command=self.toggle_sde, font=UI_FONT, bg="#f0f0f0", selectcolor="#c9dcf5",
                            relief="raised", padx=8, pady=2, cursor="hand2")
        h.create_window(262, 50, window=cb, anchor="w")
        ToolTip(cb, "Syntax directed editor: generated steps can be changed only using Modify")
        x = 262 + 160
        for text, cmd in (("Steps Colors", self.app.steps_colors), ("VPL Compiler", self.app.vpl_compiler),
                          ("New Goal", self.app.new_goal)):
            b = ttk.Button(h, text=text, command=cmd)
            h.create_window(x, 50, window=b, anchor="w")
            x += 104

        # row 3 : Steps Tree / Step Code  +  tools  +  Time Machine
        vf = tk.Frame(h, bg=PURPLE, padx=4, pady=4)
        for text, val in (("Steps Tree", "tree"), ("Step Code", "code")):
            tk.Radiobutton(vf, text=text, value=val, variable=self.view, indicatoron=False, width=10,
                           command=self.switch_view, font=UI_FONT, selectcolor="#ffffff", bg="#e0e0e0",
                           cursor="hand2").pack(side="left", padx=1)
        h.create_window(43, 82, window=vf, anchor="w")
        x = 43 + 190
        tools = [("largesteps", "Larger Steps (Font)", lambda: self.font_size(1)),
                 ("smallsteps", "Smaller Steps (Font)", lambda: self.font_size(-1)),
                 ("cut", "Cut (Ctrl+X)", self.cut), ("copy", "Copy (Ctrl+C)", self.copy),
                 ("paste", "Paste (Ctrl+V)", self.paste), ("browse", "Search (Ctrl+Shift+F / F3)", self.search)]
        self.tool_buttons = {}
        for img, tip, cmd in tools:
            b = icon_button(h, img, tip, cmd, width=34, height=26)
            h.create_window(x, 82, window=b, anchor="w")
            self.tool_buttons[img] = b
            x += 40
        tm = ttk.Button(h, text="The Time Machine", command=self.time_machine_menu)
        h.create_window(x + 6, 82, window=tm, anchor="w")
        ToolTip(tm, "Move in the history of the interactions (time frames)")
        self.slider = ttk.Scale(h, from_=0, to=0, orient="horizontal", length=130, command=self._slider_moved)
        h.create_window(x + 136, 82, window=self.slider, anchor="w")
        self.frame_label = h.create_text(x + 274, 82, text="", anchor="w", font=UI_FONT)

        # ---------------------------------------------------------- middle
        mid = tk.Frame(self, bg="#ffffff")
        mid.pack(fill="both", expand=True)
        bar = tk.Frame(mid, bg="#ffffff", width=44, bd=0)
        bar.pack(side="left", fill="y")
        tk.Frame(mid, bg="#c0c0c0", width=1).pack(side="left", fill="y")
        self.btn = {}
        spec = [("new", "new", "New Step (Comment/Organization)  Ctrl+N", self.new_step, 6),
                ("edit", "wzedit", "Edit Step  F2", self.edit_step, 1),
                ("delete", "wzdelete", "Delete Step  Del", self.delete_step, 1),
                ("up", "uparrow", "Move Step Up  Ctrl+Up", lambda: self.move_step(-1), 14),
                ("down", "dnarrow", "Move Step Down  Ctrl+Down", lambda: self.move_step(1), 1),
                ("interact", "btn_interact", "Interact with components to generate/add new steps to Steps Tree  Ctrl+T",
                 self.interact, 14),
                ("modify", "btn_modify", "Modify Step  Enter", self.modify, 4),
                ("form", "form", "Form Designer - design the windows  Ctrl+F", self.form_designer, 14),
                ("code", "btn_code", "Source Code (Goal Viewer Window)", self.app.show_code, 14)]
        for key, img, tip, cmd, pad in spec:
            b = icon_button(bar, img, tip, cmd, width=36, height=34 if key in ("interact", "modify") else 28)
            b.pack(pady=(pad, 0))
            self.btn[key] = b
        self.ignore_var = tk.IntVar()
        self.ignore_cb = tk.Checkbutton(bar, text="X", variable=self.ignore_var, command=self.toggle_ignore,
                                        bg="#ffffff", font=UI_BOLD, activebackground="#ffffff", cursor="hand2")
        self.ignore_cb.pack(pady=(14, 0))
        ToolTip(self.ignore_cb, "Ignore (Disable) Step")

        self.center = tk.Frame(mid, bg="#ffffff")
        self.center.pack(side="left", fill="both", expand=True)
        tf = tk.Frame(self.center, bg="#ffffff")
        self.tree_frame = tf
        self.style = ttk.Style(self)
        self.tree = ttk.Treeview(tf, show="tree", selectmode="browse", style="Steps.Treeview")
        ys = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        xs = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=(4, 0))
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)
        tf.pack(fill="both", expand=True)
        self.code_view = ScrolledText(self.center, font=("Consolas", 11), bg="#ffffff")
        self.apply_style()

        # ---------------------------------------------------------- bottom
        b = Gradient(self, height=38)
        b.pack(fill="x", side="bottom")
        b.create_text(50, 19, text="Component", anchor="w", font=UI_FONT)
        self.comp_var = tk.StringVar()
        self.dom_var = tk.StringVar()
        e1 = ttk.Entry(b, textvariable=self.comp_var, state="readonly", width=28)
        b.create_window(124, 19, window=e1, anchor="w")
        b.create_text(310, 19, text="Domain", anchor="w", font=UI_FONT)
        e2 = ttk.Entry(b, textvariable=self.dom_var, state="readonly", width=40)
        b.create_window(362, 19, window=e2, anchor="w")
        close = icon_button(b, "wzclose", "Close the visual source file (Ctrl+W)", self.app.close_file,
                            text=" Close", padx=6)
        b.create_window(0, 19, window=close, anchor="e", tags="close")
        b.bind("<Configure>", lambda e: b.coords("close", e.width - 8, 19), add="+")

        # ---------------------------------------------------------- events
        t = self.tree
        t.bind("<<TreeviewSelect>>", lambda e: self.on_select())
        t.bind("<<TreeviewOpen>>", lambda e: self.collapsed.discard(t.focus()))
        t.bind("<<TreeviewClose>>", lambda e: self.collapsed.add(t.focus()))
        t.bind("<Double-Button-1>", self._double_click)
        t.bind("<Button-3>", self._context_menu)
        t.bind("<Control-t>", lambda e: self._key(self.interact))
        t.bind("<Control-n>", lambda e: self._key(self.new_step))
        t.bind("<Return>", lambda e: self._key(self.modify if self._can("modify") else self.edit_step))
        t.bind("<F2>", lambda e: self._key(self.edit_step))
        t.bind("<Delete>", lambda e: self._key(self.delete_step))
        t.bind("<Control-Up>", lambda e: self._key(lambda: self.move_step(-1)))
        t.bind("<Control-Down>", lambda e: self._key(lambda: self.move_step(1)))
        t.bind("<Control-x>", lambda e: self._key(self.cut))
        t.bind("<Control-c>", lambda e: self._key(self.copy))
        t.bind("<Control-v>", lambda e: self._key(self.paste))
        t.bind("<Control-f>", lambda e: self._key(self.form_designer))
        t.bind("<Control-F>", lambda e: self._key(self.search))
        t.bind("<F3>", lambda e: self._key(self.search))
        t.bind("<KeyPress>", self._letter)

    def apply_style(self):
        s = self.app.settings
        font = (s.tree_font, s.tree_font_size)
        rh = int(s.tree_font_size * 1.9) + 4
        self.style.configure("Steps.Treeview", font=font, rowheight=rh, background="#ffffff",
                             fieldbackground="#ffffff", indent=24)
        self.style.map("Steps.Treeview", background=[("selected", "#0a64ad")],
                       foreground=[("selected", "#ffffff")])
        for t, (fg, bg) in s.colors.items():
            self.tree.tag_configure("t%d" % t, foreground=fg, background=bg)
        self.tree.tag_configure("disabled", foreground="#909090")

    # ============================================================ state
    @property
    def project(self):
        return self.app.project

    @property
    def rules(self):
        return self.app.rules

    def load_project(self):
        self.frame_no = None
        self.collapsed = set()
        self.stop_movie()
        self.goal_combo["values"] = [g.name for g in self.project.goals]
        self.select_goal(self.project.goals[0].name)

    def select_goal(self, name):
        g = self.project.goal(name) or self.project.goals[0]
        self.goal = g
        self.goal_combo["values"] = [x.name for x in self.project.goals]
        self.goal_combo.set(g.name)
        self.frame_no = None
        self.refresh(select=g.root.id)

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.project.find_step(sel[0])

    def live(self):
        return self.frame_no is None

    # ========================================================== refresh
    def frames(self):
        return self.project.goal_interactions(self.goal)

    def refresh(self, select=None):
        t = self.tree
        if select is None:
            sel = t.selection()
            select = sel[0] if sel else None
        yview = t.yview()
        t.delete(*t.get_children())
        frames = self.frames()
        visible = None
        if self.frame_no is not None:
            visible = {i.id for i in frames[:self.frame_no]}
        root = self.goal.root
        t.insert("", "end", iid=root.id, text="  %s  " % root.name, image=image("tree_app") or "", open=True)
        colors = self.app.settings.colors
        rules = self.rules

        def add(step):
            for c in step.children:
                if visible is not None and c.interaction_id and c.interaction_id not in visible:
                    continue
                st = rules.step_type(c)
                fg, bg = colors.get(st, ("#000000", "#ffffff"))
                if st in (LEAF, ALLOW_SUB_LEAF) and fg.lower() == bg.lower():
                    continue  # hidden by the steps colors (Read Mode)
                img = "tree_ignore" if c.disabled else ("tree_cmd" if c.interaction_id else "tree_person")
                tags = ("t%d" % st,) + (("disabled",) if c.disabled else ())
                t.insert(step.id, "end", iid=c.id, text="  %s  " % c.name, image=image(img) or "",
                         tags=tags, open=c.id not in self.collapsed)
                add(c)

        add(root)
        if select and t.exists(select):
            t.selection_set(select)
            t.focus(select)
            t.see(select)
        else:
            t.selection_set(root.id)
            t.focus(root.id)
            t.yview_moveto(yview[0])
        self._update_slider(frames)
        self.on_select()

    def _update_slider(self, frames):
        n = len(frames)
        self.slider.configure(to=max(n, 0))
        value = n if self.frame_no is None else self.frame_no
        self._slider_lock = True
        self.slider.set(value)
        self._slider_lock = False
        txt = "%d / %d" % (value, n)
        if self.frame_no is not None:
            txt += "   (Read Only)"
        self.header.itemconfigure(self.frame_label, text=txt)

    # ======================================================== selection
    def _can(self, what):
        s = self.selected()
        if s is None:
            return False
        live = self.live()
        start = s.parent is None
        locked = self.rules.locked(s)
        can_add = live and (start or self.rules.allow_sub(s))
        if what in ("new", "interact"):
            return can_add
        if what == "paste":
            return can_add and self.clipboard is not None
        if what == "edit":
            return live and not start and not s.generated
        if what == "modify":
            return live and s.generated
        if what in ("delete", "cut", "ignore"):
            return live and not start and not locked
        if what == "copy":
            return not start and not locked
        if what in ("up", "down"):
            if not live or start or locked:
                return False
            sib = s.parent.children
            i = sib.index(s)
            return i > 0 if what == "up" else i < len(sib) - 1
        return True

    def on_select(self):
        s = self.selected()
        for key in ("new", "edit", "delete", "up", "down", "interact", "modify"):
            self.btn[key].configure(state="normal" if self._can(key) else "disabled")
        for key, what in (("cut", "cut"), ("copy", "copy"), ("paste", "paste")):
            self.tool_buttons[key].configure(state="normal" if self._can(what) else "disabled")
        self.ignore_cb.configure(state="normal" if self._can("ignore") else "disabled")
        self.ignore_var.set(1 if (s is not None and s.disabled) else 0)
        comp_name, dom = "", ""
        if s is not None and s.generated:
            it = self.project.interaction(s.interaction_id)
            comp = self.rules.component_of(s)
            if comp is not None:
                comp_name, dom = comp.name, comp.domain
            elif it is not None:
                comp_name, dom = it.component + " (not found)", ""
        elif s is not None and s.parent is not None:
            comp_name = "(Comment / Organization step)"
        self.comp_var.set(comp_name)
        self.dom_var.set(dom)
        if self.view.get() == "code":
            self.show_step_code()

    def _key(self, fn):
        fn()
        return "break"

    def _double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        if self._can("modify"):
            self.modify()
            return "break"
        if self._can("edit"):
            self.edit_step()
            return "break"

    def _letter(self, event):
        # typing a letter opens the Components Browser searching for it (Timer4 in rpwi.scx)
        if event.state & 0x0004 or event.state & 0x20000:
            return
        ch = event.char
        if ch and ch.isalpha() and self._can("interact"):
            self.interact(search=ch)
            return "break"

    def _context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
        m = tk.Menu(self, tearoff=False)
        entries = [("Interact  (Ctrl+T)", "interact", self.interact),
                   ("Modify Step  (Enter)", "modify", self.modify), None,
                   ("New Step  (Ctrl+N)", "new", self.new_step),
                   ("Edit Step  (F2)", "edit", self.edit_step),
                   ("Delete Step  (Del)", "delete", self.delete_step), None,
                   ("Cut", "cut", self.cut), ("Copy", "copy", self.copy), ("Paste", "paste", self.paste), None,
                   ("Move Up", "up", lambda: self.move_step(-1)), ("Move Down", "down", lambda: self.move_step(1)),
                   ("Ignore (Disable) / Enable Step", "ignore", self.toggle_ignore_menu), None,
                   ("Form Designer  (Ctrl+F)", None, self.form_designer), None,
                   ("Expand All", None, lambda: self.expand_all(True)),
                   ("Collapse All", None, lambda: self.expand_all(False))]
        for e in entries:
            if e is None:
                m.add_separator()
            else:
                m.add_command(label=e[0], command=e[2], state="normal" if (e[1] is None or self._can(e[1])) else "disabled")
        m.tk_popup(event.x_root, event.y_root)

    def expand_all(self, flag):
        for s in self.goal.root.walk():
            if self.tree.exists(s.id):
                self.tree.item(s.id, open=flag)
                if flag:
                    self.collapsed.discard(s.id)
                elif s.parent is not None:
                    self.collapsed.add(s.id)

    # ============================================================ views
    def switch_view(self):
        if self.view.get() == "tree":
            self.code_view.pack_forget()
            self.tree_frame.pack(fill="both", expand=True)
            self.tree.focus_set()
        else:
            self.tree_frame.pack_forget()
            self.code_view.pack(fill="both", expand=True)
            self.show_step_code()

    def show_step_code(self):
        s = self.selected()
        if s is None:
            self.code_view.set("", readonly=True)
            return
        if s.parent is None:
            files = {}
            code, _ = codegen.generate(self.project, [self.goal], header=False, files=files, lang=self.app.language)
            code = codegen.with_files(code, files)
        else:
            lines = []

            def visit(st, dis):
                dis = dis or st.disabled
                if not dis and st.code:
                    lines.extend((ln, st) for ln in st.code.splitlines())
                for c in st.children:
                    visit(c, dis)
            visit(s, False)
            parts = {}
            code = "\n".join(t for t, _ in codegen.level2(lines, parts, self.app.language))
            code = codegen.with_files(code, {n: ("\n".join(t for t, _ in v) + "\n", None) for n, v in parts.items()})
            if not code.strip():
                code = "# This step doesn't contain code" if not s.generated else "# No code"
        self.code_view.set(code, readonly=True)
        highlight_python(self.code_view.text, self.app.language)

    def font_size(self, delta):
        s = self.app.settings
        s.tree_font_size = max(8, min(30, s.tree_font_size + delta))
        self.apply_style()
        s.save()

    def toggle_sde(self):
        self.app.settings.syntax_directed = bool(self.sde.get())
        self.rules.syntax_directed = self.app.settings.syntax_directed
        self.app.settings.save()
        self.refresh()
        self.app.status("Syntax Directed Editor : " + ("On" if self.sde.get() else "Off"))

    # ========================================================= editing
    def _changed(self, select=None):
        self.project.modified = True
        self.app.update_title()
        self.refresh(select=select)

    def new_step(self):
        if not self._can("new"):
            return
        parent = self.selected()
        name = ask_string(self, "New Step", "Step Name :")
        if not name:
            return
        step = parent.add(Step(self.project.new_id(), name))
        self.collapsed.discard(parent.id)
        self._changed(select=step.id)
        self.app.status("New step : " + name)

    def edit_step(self):
        if not self._can("edit"):
            return
        s = self.selected()
        name = ask_string(self, "Edit Step", "Step Name :", s.name)
        if name:
            s.name = name
            self._changed(select=s.id)

    def _interaction_block(self, s):
        """The steps that go with s: all the steps of its interaction (for generated roots)."""
        if s.generated:
            return [x for x in self.project.interaction_steps(s.interaction_id) if x.parent is not None]
        return [s]

    def delete_step(self):
        if not self._can("delete"):
            return
        s = self.selected()
        if not messagebox.askyesno("Delete", "Are you sure that you want to delete this step?\n\n" + s.name,
                                   parent=self):
            return
        parent = s.parent
        for x in self._interaction_block(s):
            x.detach()
        self.project.purge_interactions()
        self._changed(select=parent.id)
        self.app.status("Step deleted")

    def move_step(self, delta):
        if not self._can("up" if delta < 0 else "down"):
            return
        s = self.selected()
        sib = s.parent.children
        i = sib.index(s)
        sib[i], sib[i + delta] = sib[i + delta], sib[i]
        self._changed(select=s.id)

    def toggle_ignore_menu(self):
        self.ignore_var.set(0 if self.ignore_var.get() else 1)
        self.toggle_ignore()

    def toggle_ignore(self):
        if not self._can("ignore"):
            return
        s = self.selected()
        flag = bool(self.ignore_var.get())
        for x in self._interaction_block(s):
            for y in x.walk():
                y.disabled = flag
        self._changed(select=s.id)
        self.app.status("Step ignored (disabled)" if flag else "Step enabled")

    # ------------------------------------------------------------ clipboard
    def copy(self):
        if not self._can("copy"):
            return
        s = self.selected()
        block = self._interaction_block(s)
        block = [x for x in block if not any(a in block for a in x.ancestors())]
        steps = [x.to_dict() for x in block]
        iids = set()
        for x in block:
            iids.update(y.interaction_id for y in x.walk() if y.interaction_id)
        its = [self.project.interaction(i).to_dict() for i in iids if self.project.interaction(i)]
        self.clipboard = {"steps": copy.deepcopy(steps), "interactions": copy.deepcopy(its)}
        self.on_select()
        self.app.status("Copy Process Done")

    def cut(self):
        if not self._can("cut"):
            return
        self.copy()
        s = self.selected()
        parent = s.parent
        for x in self._interaction_block(s):
            x.detach()
        self.project.purge_interactions()
        self._changed(select=parent.id)
        self.app.status("Cut Process Done")

    def paste(self):
        if not self._can("paste"):
            return
        target = self.selected()
        p = self.project
        idmap = {}
        for d in self.clipboard["interactions"]:
            it = Interaction.from_dict(d)
            idmap[it.id] = p.new_id()
            it.id = idmap[it.id]
            it.parent_step_id = target.id
            it.goal = self.goal.name
            p.interactions.append(it)

        def clone(d):
            st = Step.from_dict(d)
            for x in st.walk():
                x.id = p.new_id()
                if x.interaction_id:
                    x.interaction_id = idmap.get(x.interaction_id, "")
            return st

        first = None
        for d in self.clipboard["steps"]:
            st = target.add(clone(d))
            first = first or st
        self.collapsed.discard(target.id)
        self._changed(select=first.id if first else target.id)
        self.app.status("Insert Process Done")

    # ------------------------------------------------------------- form designer
    def form_designer(self):
        from .formdesigner import open_form_designer
        open_form_designer(self.app)

    # ------------------------------------------------------------- search
    def search(self):
        SearchDialog(self).show(modal=False)

    def goto_step(self, sid):
        if self.frame_no is not None:
            self.frame_no = None
        self.view.set("tree")
        self.switch_view()
        step = self.project.find_step(sid)
        if step is None:
            return
        g = self.project.goal_of(step)
        if g is not None and g is not self.goal:
            self.select_goal(g.name)
        for a in step.ancestors():
            self.collapsed.discard(a.id)
        self.refresh(select=sid)
        self.tree.focus_set()

    # ======================================================= interaction
    def interact(self, search=""):
        if not self._can("interact"):
            s = self.selected()
            if s is not None and self.live():
                self.app.status("Sorry, you can't add steps under this step (Syntax Directed Editor)")
            return
        parent = self.selected()
        comp = ComponentsBrowser(self, self.app.library,
                                 allowed=lambda c: self.rules.component_allowed(c, parent),
                                 search=search, last_domain=self.last_domain,
                                 root_name=self.app.language.name).show()
        if comp is None:
            self.app.status("Operation canceled at selecting component")
            return
        self.last_domain = comp.domain or self.last_domain
        self.run_interaction(comp, parent)

    def run_interaction(self, comp, parent, interaction=None):
        created_all = []
        state = {"it": interaction}

        def on_ok(values, again):
            try:
                it, created = self.app.generator.run(comp, values, self.goal, parent, state["it"])
            except InteractionError as e:
                messagebox.showwarning("Sorry", str(e), parent=win)
                return False
            created_all.extend(created)
            self.collapsed.discard(parent.id)
            self.project.modified = True
            self.app.update_title()
            self.refresh(select=parent.id)
            self.app.status("Interaction done : " + comp.name)
            return True

        win = InteractionWindow(self, comp, self.project, on_ok,
                                values=interaction.values if interaction else None,
                                allow_again=interaction is None,
                                names_provider=self.app.program_names,
                                title_suffix=" - " + comp.name)
        win.show()
        if interaction is not None:
            root = self.project.interaction_root(interaction.id)
            self.refresh(select=root.id if root else parent.id)
        elif created_all:
            target = next((s for s in created_all if s.parent is not None and self.rules.allow_sub(s)
                           and s.internum != 1), None)
            self.refresh(select=target.id if target else parent.id)
        self.tree.focus_set()

    def modify(self):
        if not self._can("modify"):
            return
        s = self.selected()
        it = self.project.interaction(s.interaction_id)
        comp = self.app.library.get(it.component) if it else None
        if comp is None:
            messagebox.showerror("Sorry", "Component file not found : %s" % (it.component if it else "?"),
                                 parent=self)
            return
        root = self.project.interaction_root(it.id)
        parent = root.parent if root is not None and root.parent is not None else \
            (self.project.find_step(it.parent_step_id) or self.goal.root)
        self.run_interaction(comp, parent, it)

    # ===================================================== time machine
    def _slider_moved(self, value):
        if getattr(self, "_slider_lock", False):
            return
        v = int(round(float(value)))
        n = len(self.frames())
        self.set_frame(v if v < n else None)

    def set_frame(self, k):
        n = len(self.frames())
        if k is not None and k >= n:
            k = None
        if k == self.frame_no:
            return
        self.frame_no = k
        self.refresh()
        if k is None:
            self.app.status("The Time Machine : the last time frame (%d interactions)" % n)
        else:
            frames = self.frames()
            info = ""
            if k > 0:
                it = frames[k - 1]
                comp = self.app.library.get(it.component)
                info = " - %s (%s %s)" % (comp.name if comp else it.component, it.date, it.time)
            self.app.status("The Time Machine : time frame %d of %d%s" % (k, n, info))

    def current_frame(self):
        return len(self.frames()) if self.frame_no is None else self.frame_no

    def time_machine_menu(self):
        n = len(self.frames())
        k = self.current_frame()
        playing = self.movie_job is not None
        m = tk.Menu(self, tearoff=False)
        st = lambda ok: "normal" if ok else "disabled"
        m.add_command(label=" Play as Movie (Steps only) from the first time frame ",
                      command=lambda: self.play_movie(True), state=st(not playing and n > 0))
        m.add_command(label=" Play as Movie (Steps only) from the current time frame ",
                      command=lambda: self.play_movie(False), state=st(not playing and k < n))
        m.add_separator()
        m.add_command(label=" Pause ", command=self.stop_movie, state=st(playing))
        m.add_separator()
        m.add_command(label=" Goto the first time frame ", command=lambda: self.set_frame(0), state=st(k > 0))
        m.add_command(label=" Goto the previous time frame ", command=lambda: self.set_frame(k - 1), state=st(k > 0))
        m.add_command(label=" Goto the next time frame ", command=lambda: self.set_frame(k + 1), state=st(k < n))
        m.add_command(label=" Goto the last time frame ", command=lambda: self.set_frame(None), state=st(k < n))
        m.add_separator()
        m.add_command(label=" Order time frames by the latest order of steps ", command=self.order_frames,
                      state=st(n > 1 and not playing))
        m.add_separator()
        m.add_command(label=" Refresh Steps based on current components updates ", command=self.refresh_steps,
                      state=st(n > 0 and not playing and k == n))
        m.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def play_movie(self, from_first):
        self.stop_movie()
        if from_first:
            self.set_frame(0)

        def tick():
            k = self.current_frame()
            n = len(self.frames())
            if k >= n:
                self.movie_job = None
                self.app.status("The Time Machine : end of the movie")
                return
            self.set_frame(k + 1)
            self.movie_job = self.after(1200, tick)

        self.movie_job = self.after(800, tick)

    def stop_movie(self):
        if self.movie_job is not None:
            self.after_cancel(self.movie_job)
            self.movie_job = None

    def order_frames(self):
        order = []
        for s in self.goal.root.walk():
            if s.interaction_id and s.interaction_id not in order:
                order.append(s.interaction_id)
        mine = [self.project.interaction(i) for i in order]
        it = iter(mine)
        ids = set(order)
        self.project.interactions = [next(it) if x.id in ids else x for x in self.project.interactions]
        self.project.modified = True
        self.app.update_title()
        self.frame_no = None
        self.refresh()
        self.app.status("Time frames ordered by the latest order of steps")

    def refresh_steps(self):
        """Regenerate all the steps using the current version of the components."""
        errors = 0
        for it in list(self.frames()):
            comp = self.app.library.get(it.component)
            root = self.project.interaction_root(it.id)
            if comp is None or root is None or root.parent is None:
                errors += 1
                continue
            try:
                self.app.generator.run(comp, it.values, self.goal, root.parent, it)
            except InteractionError:
                errors += 1
        self._changed()
        self.app.status("Steps refreshed based on the current components (%d errors)" % errors)


class SearchDialog(Dialog):
    """Search in the steps of the visual source (searchrpwi.scx)."""

    def __init__(self, gd):
        super().__init__(gd, "Search", size=(520, 400))
        self.gd = gd
        f = tk.Frame(self.body, bg="#ffffff")
        f.pack(fill="x", padx=10, pady=8)
        tk.Label(f, text="String :", bg="#ffffff", font=UI_BOLD).pack(side="left")
        self.var = tk.StringVar()
        e = ttk.Entry(f, textvariable=self.var)
        e.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(f, text="Search", command=self.do_search).pack(side="left")
        tk.Label(self.body, text="Results :", bg="#ffffff", font=UI_BOLD).pack(anchor="w", padx=10)
        self.list = tk.Listbox(self.body, font=("Segoe UI", 10), activestyle="none")
        self.list.pack(fill="both", expand=True, padx=10, pady=(2, 8))
        self.button_bar([("Goto", self.goto), ("Close", self.cancel)])
        e.bind("<Return>", lambda ev: self.do_search())
        self.list.bind("<Double-Button-1>", lambda ev: self.goto())
        self.found = []
        self.after(60, e.focus_set)

    def do_search(self):
        text = self.var.get().strip().lower()
        self.list.delete(0, "end")
        self.found = []
        if not text:
            return
        for g in self.gd.project.goals:
            for s in g.root.walk():
                if s.parent is not None and (text in s.name.lower() or text in s.code.lower()):
                    self.found.append(s)
                    self.list.insert("end", "  [%s]  %s" % (g.name, s.name))
        if not self.found:
            self.list.insert("end", "  There is no result")

    def goto(self):
        sel = self.list.curselection()
        if sel and sel[0] < len(self.found):
            self.gd.goto_step(self.found[sel[0]].id)
