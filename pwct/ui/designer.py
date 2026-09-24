"""Component Designer = Interaction Designer (interd.scx) + Transporter Designer (transd.scx).

Tabs: Interaction Pages (visual page designer), Code Mask, Matching, Rules.
"""

import copy
import os
import re
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox

from .. import codegen
from ..components import Component, new_page, MASK_VAR_RE, TOKEN_RE
from ..engine import Generator, InteractionError
from ..model import Project
from .common import (Gradient, ScrolledText, ToolTip, ask_string, center, icon_button, image,
                     UI_BOLD, UI_FONT, Dialog, highlight_python)
from .interaction import InteractionWindow, build_page, _short_path

# (menu text, inserted text before the cursor, inserted text after the cursor, help) - transd.scx order
RPWI_TAGS = [
    ("<RPWI:POSITIVE>", "<RPWI:POSITIVE>\n", "", "TEST keeps the block when the value is found"),
    ("<RPWI:NEGATIVE>", "<RPWI:NEGATIVE>\n", "", "TEST keeps the block when the value is NOT found (default)"),
    ("<RPWI:VALUE>", "<RPWI:VALUE> ", "", "The value searched for by the next tests (default 0, empty = test for empty text)"),
    ("<RPWI:TEST> ... <RPWI:ENDTEST>", "<RPWI:TEST> ", "\n<RPWI:ENDTEST>", "Conditional block (see VALUE / POSITIVE / NEGATIVE)"),
    ("<RPWI:PUTMARK>", "<RPWI:PUTMARK> ", "", "Remember the last created step as mark n (2..30)"),
    ("<RPWI:SETMARK>", "<RPWI:SETMARK> ", "", "The marked step becomes the parent of the next steps (mark 1 = selected step)"),
    ("<RPWI:NEWSTEP>", "<RPWI:NEWSTEP> ", "", "Create a new step (the next code lines are stored in this step)"),
    ("<RPWI:SELECTSTEPBYNAME>", "<RPWI:SELECTSTEPBYNAME> ", "", "Select a step by its name to be the parent of the next steps"),
    ("<RPWI:TABPUSH>", "<RPWI:TABPUSH>\n", "", "Increase the indentation of the next code lines"),
    ("<RPWI:TABPOP>", "<RPWI:TABPOP>\n", "", "Decrease the indentation (empty blocks get 'pass')"),
    ("<RPWI:NOTE>", "<RPWI:NOTE> ", "", "Comment (ignored)"),
    ("<RPWI:NEWVAR>", "<RPWI:NEWVAR> ", "", "New temporary variable (it becomes the active variable)"),
    ("<RPWI:SETVARVALUE>", "<RPWI:SETVARVALUE> ", "", "Set the value of the active temporary variable"),
    ("<RPWI:SELECTVAR>", "<RPWI:SELECTVAR> ", "", "Select the active temporary variable by its name"),
    ("<RPWI:REPLACEVARSWITHVALUES>", "<RPWI:REPLACEVARSWITHVALUES>\n", "",
     "Replace <NAME> of the temporary variables with their values in the next lines"),
    ("<RPWI:IGNORELAST>", "<RPWI:IGNORELAST> ", "", "Remove the last character (example ,) from the generated code"),
    ("<RPWI:IGNORELEVEL>", "<RPWI:IGNORELEVEL> ", "", "IGNORELAST level: 1 = steps of this interaction, 2 = all the childs"),
    ("<RPWI:INFORMATION>", "<RPWI:INFORMATION> ", "", "Information text stored with the step"),
    ("<PWCT:TOFILE> ... <PWCT:ENDFILE>", "<PWCT:TOFILE> ", "\n<PWCT:ENDFILE>",
     "The lines between them are written to another file (in the folder of the generated source)"),
    ("<PWCT:ADDVAR>", "<PWCT:ADDVAR> ", "", "Start a code generator variable (a text to be replaced)"),
    ("<PWCT:SETVAR>", "<PWCT:SETVAR> ", "", "The value of the code generator variable (replaced at the end)"),
    ("<PWCT:MERGENEXTTOPREV>", "<PWCT:MERGENEXTTOPREV>", "", "Merge the next line with the previous line"),
    ("<PWCT:IGNORELAST>", "<PWCT:IGNORELAST> ", "", "Remove a text from the end of the previous generated line"),
    ("<PWCT:NEWLINE>", "<PWCT:NEWLINE> ", "", "Empty line in the generated code"),
    ("<PWCT:MERGENEXTTOPREVBYSPACEORSTAR>", "<PWCT:MERGENEXTTOPREVBYSPACEORSTAR> ", "",
     "Merge the next line with the previous line (no space when the previous line ends with *)"),
    ("Variable <T_>", "<T_", ">", "Code mask variable (Automatic Matching: <T_NAME> = page variable NAME)"),
    ("Variable <T_INPUT>", "<T_INPUT>", "", "Code mask variable INPUT"),
    ("Variable <T_OUTPUT>", "<T_OUTPUT>", "", "Code mask variable OUTPUT"),
    ("Variable <T_TB_>", "<T_TB_", ">", "Code mask variable of a TextBox"),
    ("Variable <T_CB_>", "<T_CB_", ">", "Code mask variable of a CheckBox"),
    ("Variable <T_LB_>", "<T_LB_", ">", "Code mask variable of a ListBox"),
]
KINDS = ["any", "expr", "target", "name", "params", "args", "module", "stmt"]


class ComponentDesigner(tk.Toplevel):
    def __init__(self, app, component=None, domain=None, tab=0):
        super().__init__(app.root)
        self.app = app
        self.title("Component Designer (Interaction Designer + Transporter Designer)")
        ic = image("app_icon")
        if ic:
            self.iconphoto(False, ic)
        self.configure(bg="#ffffff")
        self.comp = None
        self.dirty = False
        self.page_index = 0
        self.sel = None           # selected control dict
        self.widgets = []         # (control, widget) of the rendered page
        self.drag = None
        self._build()
        self.load(copy.deepcopy(component.to_dict()) if component else None,
                  component.path if component else None, domain or (component.domain if component else ""))
        self.nb.select(tab)
        center(self, None, 1180, 720)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Control-s>", lambda e: (self.save(), "break")[1])

    # ================================================================ UI
    def _build(self):
        tb = self.tb = Gradient(self, height=38)
        tb.pack(fill="x")
        x = 8
        for img, tip, cmd in (("new", "New Component", self.new), ("open", "Open Component", self.open),
                              ("save", "Save", self.save), (None, "Save As", self.save_as)):
            b = icon_button(tb, img, tip, cmd, text="" if img else "Save As", width=30 if img else None)
            tb.create_window(x, 19, window=b, anchor="w")
            x += 36 if img else 70
        b = ttk.Button(tb, text="Test (Preview)", command=self.test)
        tb.create_window(x + 10, 19, window=b, anchor="w")
        ToolTip(b, "Try the interaction pages and see the generated steps and code")
        self.file_text = tb.create_text(x + 130, 19, text="File : (NO NAME)", anchor="w", font=UI_FONT)
        tk.Frame(self, height=1, bg="#808080").pack(fill="x")

        info = tk.Frame(self, bg="#ffffff")
        info.pack(fill="x", padx=8, pady=6)
        self.v_name = tk.StringVar()
        self.v_domain = tk.StringVar()
        self.v_desc = tk.StringVar()
        self.v_order = tk.StringVar()
        tk.Label(info, text="Name :", bg="#ffffff", font=UI_BOLD).pack(side="left")
        ttk.Entry(info, textvariable=self.v_name, width=24).pack(side="left", padx=(4, 12))
        tk.Label(info, text="Domain :", bg="#ffffff", font=UI_BOLD).pack(side="left")
        doms = [d.key for d in self.app.library.root.walk() if d.key]
        ttk.Combobox(info, textvariable=self.v_domain, values=doms, width=20).pack(side="left", padx=(4, 12))
        tk.Label(info, text="Order :", bg="#ffffff", font=UI_BOLD).pack(side="left")
        ttk.Spinbox(info, textvariable=self.v_order, from_=0, to=9999, width=5).pack(side="left", padx=(4, 12))
        tk.Label(info, text="Description :", bg="#ffffff", font=UI_BOLD).pack(side="left")
        ttk.Entry(info, textvariable=self.v_desc).pack(side="left", fill="x", expand=True, padx=4)
        for v in (self.v_name, self.v_domain, self.v_desc, self.v_order):
            v.trace_add("write", lambda *a: self.set_dirty())

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.tab_changed())
        self._build_pages_tab()
        self._build_mask_tab()
        self._build_matching_tab()
        self._build_rules_tab()

    # ------------------------------------------------ Interaction Pages tab
    def _build_pages_tab(self):
        tab = tk.Frame(self.nb, bg="#ffffff")
        self.nb.add(tab, text="  Interaction Pages  ")
        left = tk.Frame(tab, bg="#ffffff", width=170)
        left.pack(side="left", fill="y", padx=6, pady=6)
        tk.Label(left, text="Pages List :", bg="#ffffff", font=UI_BOLD).pack(anchor="w")
        self.pages_list = tk.Listbox(left, width=22, height=10, exportselection=False, font=UI_FONT)
        self.pages_list.pack(fill="y", expand=True)
        self.pages_list.bind("<<ListboxSelect>>", self.page_selected)
        for text, cmd in (("Add", self.add_page), ("Delete", self.delete_page), ("Rename", self.rename_page),
                          ("Move Up", lambda: self.move_page(-1)), ("Move Down", lambda: self.move_page(1))):
            ttk.Button(left, text=text, command=cmd).pack(fill="x", pady=1)

        mid = tk.Frame(tab, bg="#ffffff")
        mid.pack(side="left", fill="both", expand=True, pady=6)
        tools = tk.Frame(mid, bg="#ffffff")
        tools.pack(fill="x")
        for text, t in (("Label", "label"), ("TextBox", "textbox"), ("ListBox", "listbox"), ("CheckBox", "checkbox")):
            ttk.Button(tools, text="+ " + text, command=lambda tt=t: self.add_control(tt)).pack(side="left", padx=2)
        ttk.Button(tools, text="Delete Control", command=self.delete_control).pack(side="left", padx=(12, 2))
        ttk.Button(tools, text="Duplicate", command=self.duplicate_control).pack(side="left", padx=2)
        tk.Label(tools, text="  Drag to move, drag the black square to resize, arrows to move",
                 bg="#ffffff", fg="#707070", font=UI_FONT).pack(side="left")
        area = tk.Frame(mid, bg="#d8d8d8")
        area.pack(fill="both", expand=True, pady=(4, 0))
        self.canvas = tk.Canvas(area, bg="#d8d8d8", highlightthickness=0)
        ys = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        xs = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)
        self.page_item = None
        self.page_frame = None
        self.bind("<KeyPress>", self._arrow)

        self.props = tk.Frame(tab, bg="#f7f7f7", width=290, bd=1, relief="solid")
        self.props.pack(side="right", fill="y", padx=6, pady=6)
        self.props.pack_propagate(False)

    # --------------------------------------------------------- Code Mask
    def _build_mask_tab(self):
        tab = tk.Frame(self.nb, bg="#ffffff")
        self.nb.add(tab, text="  Code Mask  ")
        right = tk.Frame(tab, bg="#ffffff", width=300)
        right.pack(side="right", fill="y", padx=6, pady=6)
        right.pack_propagate(False)
        tk.Label(right, text="Variables From Interaction Pages", bg="#ffffff", font=UI_BOLD).pack(anchor="w")
        self.mask_vars = tk.Listbox(right, height=8, font=("Consolas", 10))
        self.mask_vars.pack(fill="x")
        self.mask_vars.bind("<Double-Button-1>", self._insert_var)
        tk.Label(right, text="RPWI Statements  (or right click)", bg="#ffffff",
                 font=UI_BOLD).pack(anchor="w", pady=(8, 0))
        self.tags_list = tk.Listbox(right, height=15, font=("Consolas", 9))
        self.tags_list.pack(fill="both", expand=True)
        for tag in RPWI_TAGS:
            self.tags_list.insert("end", tag[0])
        self.tags_list.bind("<Double-Button-1>", self._insert_tag)
        self.tags_list.bind("<<ListboxSelect>>", lambda e: self._tag_help())
        self.tag_help = tk.Label(right, text="Double click to insert", bg="#ffffff", fg="#505050",
                                 wraplength=280, justify="left", font=UI_FONT)
        self.tag_help.pack(fill="x", pady=4)
        self.mask = ScrolledText(tab, font=("Consolas", 11), bg="#ffffff")
        self.mask.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        t = self.mask.text
        t.tag_configure("tag", foreground="#0000c0", font=("Consolas", 11, "bold"))
        t.tag_configure("var", foreground="#c00000")
        t.tag_configure("note", foreground="#008000")
        t.bind("<KeyRelease>", lambda e: (self._highlight_mask(), self.set_dirty()))
        t.bind("<Button-3>", self._mask_menu)

    def _mask_menu(self, event):
        """Right click menu of the code mask (like transd.scx)."""
        t = self.mask.text
        t.mark_set("insert", "@%d,%d" % (event.x, event.y))
        m = tk.Menu(self, tearoff=False)
        for k, tag in enumerate(RPWI_TAGS):
            if k in (18, 25):
                m.add_separator()
            m.add_command(label=tag[0], command=lambda i=k: self._insert_tag_at(i))
        m.tk_popup(event.x_root, event.y_root)

    def _insert_tag_at(self, i):
        _, before, after, _ = RPWI_TAGS[i]
        t = self.mask.text
        t.insert("insert", before)
        if after:
            pos = t.index("insert")
            t.insert("insert", after)
            t.mark_set("insert", pos)
        t.focus_set()
        self._highlight_mask()
        self.set_dirty()

    def _highlight_mask(self):
        t = self.mask.text
        for tag in ("tag", "var", "note"):
            t.tag_remove(tag, "1.0", "end")
        content = t.get("1.0", "end-1c")
        for m in re.finditer(r"<(RPWI|pwct):[A-Za-z]+>", content, flags=re.I):
            t.tag_add("tag", "1.0+%dc" % m.start(), "1.0+%dc" % m.end())
        for m in TOKEN_RE.finditer(content):
            t.tag_add("var", "1.0+%dc" % m.start(), "1.0+%dc" % m.end())
        for m in MASK_VAR_RE.finditer(content):
            t.tag_add("var", "1.0+%dc" % m.start(), "1.0+%dc" % m.end())
        for m in re.finditer(r"^\s*(<RPWI:NOTE>|<\*>).*$", content, flags=re.I | re.M):
            t.tag_add("note", "1.0+%dc" % m.start(), "1.0+%dc" % m.end())

    def _insert_var(self, _e=None):
        sel = self.mask_vars.curselection()
        if sel:
            self.mask.text.insert("insert", "#{%s}" % self.mask_vars.get(sel[0]).split()[0])
            self._highlight_mask()
            self.set_dirty()

    def _insert_tag(self, _e=None):
        sel = self.tags_list.curselection()
        if sel:
            self._insert_tag_at(sel[0])

    def _tag_help(self):
        sel = self.tags_list.curselection()
        if sel:
            self.tag_help.configure(text=RPWI_TAGS[sel[0]][3])

    # ---------------------------------------------------------- Matching
    def _build_matching_tab(self):
        tab = tk.Frame(self.nb, bg="#ffffff")
        self.nb.add(tab, text="  Matching  ")
        top = tk.Frame(tab, bg="#ffffff")
        top.pack(fill="both", expand=True, padx=8, pady=8)
        for col, text in enumerate(("Variables From Interaction Pages", "Variables From Code Mask")):
            tk.Label(top, text=text, bg="#ffffff", font=UI_BOLD).grid(row=0, column=col, sticky="w", padx=4)
        self.m_left = tk.Listbox(top, exportselection=False, font=("Consolas", 10))
        self.m_right = tk.Listbox(top, exportselection=False, font=("Consolas", 10))
        self.m_left.grid(row=1, column=0, sticky="nsew", padx=4)
        self.m_right.grid(row=1, column=1, sticky="nsew", padx=4)
        tk.Label(top, text="Matching (Page variable  =  Code mask variable)", bg="#ffffff",
                 font=UI_BOLD).grid(row=0, column=2, sticky="w", padx=4)
        self.m_pairs = ttk.Treeview(top, columns=("page", "mask"), show="headings", height=10)
        self.m_pairs.heading("page", text="Interaction Page Variable")
        self.m_pairs.heading("mask", text="Code Mask Variable")
        self.m_pairs.grid(row=1, column=2, sticky="nsew", padx=4)
        top.columnconfigure((0, 1, 2), weight=1)
        top.rowconfigure(1, weight=1)
        bar = tk.Frame(tab, bg="#ffffff")
        bar.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(bar, text="Add", command=self.add_pair).pack(side="left", padx=2)
        ttk.Button(bar, text="Delete", command=self.delete_pair).pack(side="left", padx=2)
        ttk.Button(bar, text="Automatic Matching", command=self.auto_match).pack(side="left", padx=2)
        self.m_info = tk.Label(bar, text="", bg="#ffffff", fg="#505050", font=UI_FONT)
        self.m_info.pack(side="left", padx=10)

    # ------------------------------------------------------------- Rules
    def _build_rules_tab(self):
        tab = tk.Frame(self.nb, bg="#ffffff")
        self.nb.add(tab, text="  Rules  ")
        tk.Label(tab, text="Steps generated by the code mask (click to change the rules)", bg="#ffffff",
                 font=UI_BOLD).pack(anchor="w", padx=8, pady=(8, 2))
        self.r_tree = ttk.Treeview(tab, columns=("num", "name", "root", "sub"), show="headings", height=12)
        for c, text, w in (("num", "Step", 60), ("name", "Step Name (NEWSTEP)", 420),
                           ("root", "Allow Root (Move/Delete)", 170), ("sub", "Allow Interaction (Sub Steps)", 200)):
            self.r_tree.heading(c, text=text)
            self.r_tree.column(c, width=w, anchor="w" if c == "name" else "center")
        self.r_tree.pack(fill="both", expand=True, padx=8)
        self.r_tree.bind("<Button-1>", self._rule_click)
        f = tk.Frame(tab, bg="#ffffff")
        f.pack(fill="x", padx=8, pady=8)
        tk.Label(f, text="Allow Parent (component names, comma separated) :", bg="#ffffff",
                 font=UI_BOLD).pack(side="left")
        self.v_requires = tk.StringVar()
        ttk.Entry(f, textvariable=self.v_requires).pack(side="left", fill="x", expand=True, padx=6)
        self.v_requires.trace_add("write", lambda *a: self.set_dirty())
        tk.Label(tab, text="Step 1 is always a root step.  Allow Parent: the component can be used only inside "
                           "these components (example: Exit Loop inside While Loop).",
                 bg="#ffffff", fg="#505050", font=UI_FONT).pack(anchor="w", padx=8, pady=(0, 8))

    # ============================================================= data
    def load(self, data, path, domain):
        self.comp = Component(data, path)
        if data is None:
            self.comp.pages = [new_page("Page1")]
            self.comp.pages[0]["controls"].append({"type": "label", "x": 0, "y": 0, "w": 620, "h": 44,
                                                  "caption": "  New Component", "fg": "#ffffff",
                                                  "bg": "#400040", "font": ["Arial", 14, "bold"]})
            self.comp.mask = "<RPWI:NEWSTEP> Step Name\n"
        self.v_name.set(self.comp.name)
        self.v_domain.set(domain or "")
        self.v_desc.set(self.comp.description)
        self.v_order.set(str(self.comp.order))
        self.v_requires.set(", ".join(self.comp.requires_ancestor))
        self.mask.set(self.comp.mask)
        self._highlight_mask()
        self.page_index = 0
        self.sel = None
        self.refresh_pages()
        self.dirty = False
        self.update_file_label()

    def update_file_label(self):
        path = _short_path(self.comp) if self.comp.path else "(NO NAME)"
        self.tb.itemconfigure(self.file_text, text="File : %s%s" % (path, "  *" if self.dirty else ""))

    def set_dirty(self):
        if not self.dirty:
            self.dirty = True
            self.update_file_label()

    def collect(self):
        c = self.comp
        c.name = self.v_name.get().strip() or "New Component"
        c.description = self.v_desc.get().strip()
        try:
            c.order = int(self.v_order.get())
        except ValueError:
            c.order = 1000
        c.mask = self.mask.get().rstrip("\n")
        c.rules["requires_ancestor"] = [x.strip() for x in self.v_requires.get().split(",") if x.strip()]
        dom = self.v_domain.get().strip().strip("/")
        c.key = (dom + "/" + c.name).strip("/")
        return c

    def tab_changed(self):
        self.collect()
        idx = self.nb.index("current")
        if idx == 1:
            self.mask_vars.delete(0, "end")
            for page, var, ctrl in self.comp.variables():
                self.mask_vars.insert("end", "%s   (%s)" % (var, page))
        elif idx == 2:
            self.refresh_matching()
        elif idx == 3:
            self.refresh_rules()

    # ====================================================== pages editor
    def refresh_pages(self):
        self.pages_list.delete(0, "end")
        for p in self.comp.pages:
            self.pages_list.insert("end", "  " + p["name"])
        self.page_index = max(0, min(self.page_index, len(self.comp.pages) - 1))
        self.pages_list.selection_set(self.page_index)
        self.render_page()

    def page_selected(self, _e=None):
        sel = self.pages_list.curselection()
        if sel:
            self.page_index = sel[0]
            self.sel = None
            self.render_page()

    @property
    def page(self):
        return self.comp.pages[self.page_index]

    def add_page(self):
        name = ask_string(self, "Add Page", "Page Name :", "Page%d" % (len(self.comp.pages) + 1))
        if name:
            self.comp.pages.append(new_page(name))
            self.page_index = len(self.comp.pages) - 1
            self.sel = None
            self.refresh_pages()
            self.set_dirty()

    def delete_page(self):
        if len(self.comp.pages) < 2:
            messagebox.showinfo("Sorry", "The component needs at least one page", parent=self)
            return
        if messagebox.askyesno("Delete", "Delete the page (%s)?" % self.page["name"], parent=self):
            del self.comp.pages[self.page_index]
            self.sel = None
            self.refresh_pages()
            self.set_dirty()

    def rename_page(self):
        name = ask_string(self, "Rename Page", "Page Name :", self.page["name"])
        if name:
            self.page["name"] = name
            self.refresh_pages()
            self.set_dirty()

    def move_page(self, d):
        i, j = self.page_index, self.page_index + d
        if 0 <= j < len(self.comp.pages):
            ps = self.comp.pages
            ps[i], ps[j] = ps[j], ps[i]
            self.page_index = j
            self.refresh_pages()
            self.set_dirty()

    def render_page(self, props=True):
        if self.page_frame is not None:
            self.page_frame.destroy()
        p = self.page
        frame, _, widgets = build_page(self.canvas, p, {}, design=True)
        self.page_frame, self.widgets = frame, widgets
        if self.page_item is None:
            self.page_item = self.canvas.create_window(16, 16, window=frame, anchor="nw")
        else:
            self.canvas.itemconfigure(self.page_item, window=frame)
        self.canvas.configure(scrollregion=(0, 0, p.get("width", 620) + 40, p.get("height", 320) + 40))
        frame.bind("<Button-1>", lambda e: self.select(None))
        for c, w in widgets:
            w.bind("<Button-1>", lambda e, cc=c: self._press(e, cc))
            w.bind("<B1-Motion>", self._motion)
            w.bind("<ButtonRelease-1>", self._release)
            if isinstance(w, tk.Listbox):
                w.bind("<<ListboxSelect>>", lambda e: "break")
        self.handles = [tk.Frame(frame, bg="#ff0000") for _ in range(4)]
        self.grip = tk.Frame(frame, bg="#000000", width=8, height=8, cursor="size_nw_se")
        self.grip.bind("<Button-1>", lambda e: self._press(e, self.sel, resize=True))
        self.grip.bind("<B1-Motion>", self._motion)
        self.grip.bind("<ButtonRelease-1>", self._release)
        self.show_selection()
        if props:
            self.show_props()

    def show_selection(self):
        c = self.sel
        if c is None:
            for h in self.handles:
                h.place_forget()
            self.grip.place_forget()
            return
        x, y, w, h = c["x"], c["y"], c["w"], c["h"]
        b = 2
        self.handles[0].place(x=x - b, y=y - b, width=w + 2 * b, height=b)
        self.handles[1].place(x=x - b, y=y + h, width=w + 2 * b, height=b)
        self.handles[2].place(x=x - b, y=y, width=b, height=h)
        self.handles[3].place(x=x + w, y=y, width=b, height=h)
        self.grip.place(x=x + w - 4, y=y + h - 4)
        for f in self.handles + [self.grip]:
            f.lift()

    def select(self, c):
        self.sel = c
        self.show_selection()
        self.show_props()

    def _press(self, e, c, resize=False):
        if c is None:
            return "break"
        if c is not self.sel:
            self.select(c)
        self.drag = (e.x_root, e.y_root, c["x"], c["y"], c["w"], c["h"], resize)
        self.canvas.focus_set()
        return "break"

    def _motion(self, e):
        if not self.drag or self.sel is None:
            return "break"
        x0, y0, cx, cy, cw, ch, resize = self.drag
        dx, dy = e.x_root - x0, e.y_root - y0
        c = self.sel
        if resize:
            c["w"], c["h"] = max(10, cw + dx), max(10, ch + dy)
        else:
            c["x"], c["y"] = max(0, cx + dx), max(0, cy + dy)
        for cc, w in self.widgets:
            if cc is c:
                w.place_configure(x=c["x"], y=c["y"], width=c["w"], height=c["h"])
        self.show_selection()
        return "break"

    def _release(self, _e):
        if self.drag:
            self.drag = None
            self.set_dirty()
            self.show_props()
        return "break"

    def _arrow(self, e):
        if self.sel is None or self.nb.index("current") != 0 or self.focus_get() is not self.canvas:
            return
        step = 10 if e.state & 0x0001 else 1
        d = {"Left": (-step, 0), "Right": (step, 0), "Up": (0, -step), "Down": (0, step)}.get(e.keysym)
        if d:
            self.sel["x"] = max(0, self.sel["x"] + d[0])
            self.sel["y"] = max(0, self.sel["y"] + d[1])
            self.render_page()
            self.set_dirty()
            return "break"
        if e.keysym == "Delete":
            self.delete_control()

    def add_control(self, t):
        p = self.page
        n = sum(1 for _, v, _ in self.comp.variables()) + 1
        c = {"type": t, "x": 20, "y": 60 + 10 * (len(p["controls"]) % 10), "w": 200, "h": 26,
             "fg": "#000000", "bg": "" if t in ("label", "checkbox") else "#ffffff", "font": ["Arial", 10]}
        if t == "label":
            c["caption"] = "Label :"
        elif t == "textbox":
            c.update({"var": "var%d" % n, "title": "Value %d" % n, "text": "", "kind": "any"})
        elif t == "listbox":
            c.update({"var": "var%d" % n, "title": "List %d" % n, "items": ["Item 1", "Item 2"],
                      "selected": 0, "mode": "item", "h": 70})
        elif t == "checkbox":
            c.update({"var": "var%d" % n, "title": "Option %d" % n, "caption": "Option", "value": 0})
        p["controls"].append(c)
        self.sel = c
        self.render_page()
        self.set_dirty()

    def delete_control(self):
        if self.sel is not None:
            self.page["controls"].remove(self.sel)
            self.sel = None
            self.render_page()
            self.set_dirty()

    def duplicate_control(self):
        if self.sel is None:
            return
        c = copy.deepcopy(self.sel)
        c["x"] += 10
        c["y"] += 10
        if c.get("var"):
            c["var"] = c["var"] + "_2"
        self.page["controls"].append(c)
        self.sel = c
        self.render_page()
        self.set_dirty()

    # ------------------------------------------------------- properties
    def show_props(self):
        for w in self.props.winfo_children():
            w.destroy()
        c = self.sel
        f = self.props
        tk.Label(f, text="Properties", bg="#e0e0e0", font=UI_BOLD, anchor="w").pack(fill="x")
        body = tk.Frame(f, bg="#f7f7f7")
        body.pack(fill="both", expand=True, padx=6, pady=4)
        self._prow = 0
        if c is None:
            p = self.page
            tk.Label(body, text="Page", bg="#f7f7f7", fg="#400040", font=UI_BOLD).grid(row=0, column=0, sticky="w")
            self._prow = 1
            self._entry(body, "Name", p, "name", str, refresh_list=True)
            self._color(body, "Back Color", p, "bgcolor")
            self._entry(body, "Width", p, "width", int)
            self._entry(body, "Height", p, "height", int)
            return
        tk.Label(body, text=c["type"].upper(), bg="#f7f7f7", fg="#400040", font=UI_BOLD).grid(row=0, column=0, sticky="w")
        self._prow = 1
        t = c["type"]
        if t != "label":
            self._entry(body, "Variable", c, "var", str)
            self._entry(body, "Title", c, "title", str)
        if t in ("label", "checkbox"):
            self._entry(body, "Caption", c, "caption", str)
        if t == "textbox":
            self._entry(body, "Default Text", c, "text", str)
            self._combo(body, "Kind (Check)", c, "kind", KINDS)
            self._check(body, "Escape quotes (text)", c, "escape")
            self._check(body, "Allow empty value", c, "allow_empty")
            self._check(body, "Default focus", c, "focus")
        if t == "listbox":
            self._lines(body, "Items", c, "items")
            self._lines(body, "Values (code)", c, "values")
            self._entry(body, "Selected (0..)", c, "selected", int)
            self._combo(body, "Value Mode", c, "mode", ["item", "index"])
        if t == "checkbox":
            self._entry(body, "Checked (0/1)", c, "value", int)
        for key in ("x", "y", "w", "h"):
            self._entry(body, key.upper(), c, key, int)
        self._color(body, "Text Color", c, "fg")
        self._color(body, "Back Color", c, "bg")
        font = c.setdefault("font", ["Arial", 10])
        holder = {"fname": font[0], "fsize": font[1] if len(font) > 1 else 10, "bold": 1 if "bold" in font else 0}

        def apply_font():
            c["font"] = [holder["fname"], holder["fsize"]] + (["bold"] if holder["bold"] else [])
        self._entry(body, "Font", holder, "fname", str, after=apply_font)
        self._entry(body, "Font Size", holder, "fsize", int, after=apply_font)
        self._check(body, "Bold", holder, "bold", after=apply_font)

    def _label(self, body, text):
        tk.Label(body, text=text, bg="#f7f7f7", font=UI_FONT, anchor="w").grid(row=self._prow, column=0,
                                                                              sticky="w", pady=1)

    def _entry(self, body, text, obj, key, conv, refresh_list=False, after=None):
        self._label(body, text)
        v = tk.StringVar(value=str(obj.get(key, "")))
        e = ttk.Entry(body, textvariable=v, width=20)
        e.grid(row=self._prow, column=1, sticky="ew", pady=1)
        body.columnconfigure(1, weight=1)

        def apply(_e=None):
            try:
                val = conv(v.get())
            except ValueError:
                return
            if obj.get(key) != val:
                obj[key] = val
                if after:
                    after()
                self.set_dirty()
                if refresh_list:
                    self.pages_list.delete(self.page_index)
                    self.pages_list.insert(self.page_index, "  " + self.page["name"])
                    self.pages_list.selection_set(self.page_index)
                self.render_page(props=False)
        e.bind("<Return>", apply)
        e.bind("<FocusOut>", apply)
        self._prow += 1

    def _combo(self, body, text, obj, key, values):
        self._label(body, text)
        v = tk.StringVar(value=obj.get(key, values[0]))
        cb = ttk.Combobox(body, textvariable=v, values=values, state="readonly", width=17)
        cb.grid(row=self._prow, column=1, sticky="ew", pady=1)
        cb.bind("<<ComboboxSelected>>", lambda e: (obj.__setitem__(key, v.get()), self.set_dirty()))
        self._prow += 1

    def _check(self, body, text, obj, key, after=None):
        v = tk.IntVar(value=1 if obj.get(key) else 0)

        def apply():
            obj[key] = bool(v.get()) if after is None else v.get()
            if after:
                after()
                self.render_page(props=False)
            self.set_dirty()
        tk.Checkbutton(body, text=text, variable=v, command=apply, bg="#f7f7f7", font=UI_FONT,
                       anchor="w").grid(row=self._prow, column=0, columnspan=2, sticky="w")
        self._prow += 1

    def _lines(self, body, text, obj, key):
        self._label(body, text)
        t = tk.Text(body, height=4, width=20, font=("Consolas", 9))
        t.insert("1.0", "\n".join(obj.get(key) or []))
        t.grid(row=self._prow, column=1, sticky="ew", pady=1)

        def apply(_e=None):
            lines = [ln.strip() for ln in t.get("1.0", "end-1c").splitlines() if ln.strip()]
            if lines != (obj.get(key) or []):
                if lines or key == "items":
                    obj[key] = lines
                else:
                    obj.pop(key, None)
                self.set_dirty()
                self.render_page(props=False)
        t.bind("<FocusOut>", apply)
        self._prow += 1

    def _color(self, body, text, obj, key):
        self._label(body, text)
        cur = obj.get(key) or ""
        b = tk.Button(body, text=cur or "(Transparent)", bg=cur or "#f7f7f7", relief="solid", bd=1,
                      font=UI_FONT, cursor="hand2")
        b.grid(row=self._prow, column=1, sticky="ew", pady=1)

        def pick():
            col = colorchooser.askcolor(cur or "#ffffff", parent=self)[1]
            if col:
                obj[key] = col
                b.configure(text=col, bg=col)
                self.set_dirty()
                self.render_page(props=False)

        def clear(_e=None):
            obj[key] = ""
            b.configure(text="(Transparent)", bg="#f7f7f7")
            self.set_dirty()
            self.render_page(props=False)
        b.configure(command=pick)
        b.bind("<Button-3>", clear)
        ToolTip(b, "Click: choose color   Right click: transparent")
        self._prow += 1

    # ========================================================== matching
    def refresh_matching(self):
        c = self.collect()
        self.m_left.delete(0, "end")
        self.m_right.delete(0, "end")
        for _, var, _ in c.variables():
            self.m_left.insert("end", var)
        for tok in c.mask_tokens():
            self.m_right.insert("end", tok)
        for i in self.m_pairs.get_children():
            self.m_pairs.delete(i)
        for a, b in c.pairs():
            self.m_pairs.insert("", "end", values=(a, b))
        self.m_info.configure(text="Automatic matching :  variable  =  #{variable}" if not c.matching
                              else "Custom matching")

    def add_pair(self):
        a, b = self.m_left.curselection(), self.m_right.curselection()
        if not a or not b:
            messagebox.showinfo("Matching", "Select a page variable and a code mask variable", parent=self)
            return
        if not self.comp.matching:
            self.comp.matching = [list(p) for p in self.comp.pairs()]
        pair = [self.m_left.get(a[0]), self.m_right.get(b[0])]
        self.comp.matching = [p for p in self.comp.matching if p[0] != pair[0]] + [pair]
        self.set_dirty()
        self.refresh_matching()

    def delete_pair(self):
        sel = self.m_pairs.selection()
        if not sel:
            return
        if not self.comp.matching:
            self.comp.matching = [list(p) for p in self.comp.pairs()]
        a, b = self.m_pairs.item(sel[0], "values")
        self.comp.matching = [p for p in self.comp.matching if not (p[0] == a and p[1] == b)]
        self.set_dirty()
        self.refresh_matching()

    def auto_match(self):
        self.comp.matching = []
        self.set_dirty()
        self.refresh_matching()

    # ============================================================= rules
    def refresh_rules(self):
        c = self.collect()
        for i in self.r_tree.get_children():
            self.r_tree.delete(i)
        n = 0
        for ln in c.mask.splitlines():
            ln = ln.strip()
            if ln.upper().startswith("<RPWI:NEWSTEP>"):
                n += 1
                root = "Yes" if (n == 1 or c.allow_root(n)) else ""
                sub = "Yes" if c.allow_interaction(n) else ""
                self.r_tree.insert("", "end", iid=str(n), values=(n, ln[14:].strip(), root, sub))

    def _rule_click(self, e):
        row, col = self.r_tree.identify_row(e.y), self.r_tree.identify_column(e.x)
        if not row or col not in ("#3", "#4"):
            return
        n = int(row)
        key = "allow_root" if col == "#3" else "allow_interaction"
        if key == "allow_root" and n == 1:
            return
        lst = [int(x) for x in self.comp.rules.get(key, [])]
        if n in lst:
            lst.remove(n)
        else:
            lst.append(n)
        self.comp.rules[key] = sorted(lst)
        self.set_dirty()
        self.refresh_rules()

    # ============================================================== file
    def ask_save(self):
        if not self.dirty:
            return True
        r = messagebox.askyesnocancel("Component Designer", "Save changes ?", parent=self)
        if r is None:
            return False
        return self.save() if r else True

    def new(self):
        if self.ask_save():
            self.load(None, None, self.v_domain.get())

    def open(self):
        if not self.ask_save():
            return
        f = filedialog.askopenfilename(parent=self, initialdir=self.app.library.root_dir,
                                       filetypes=[("PyPWCT Component", "*.json")])
        if f:
            try:
                comp = Component.load(f)
            except (OSError, ValueError) as ex:
                messagebox.showerror("Error", "The File is not valid - Process Canceled\n%s" % ex, parent=self)
                return
            rel = os.path.relpath(os.path.dirname(f), self.app.library.root_dir).replace("\\", "/")
            self.load(comp.to_dict(), f, "" if rel.startswith("..") or rel == "." else rel)

    def save(self):
        if not self.comp.path:
            return self.save_as()
        return self._write(self.comp.path)

    def save_as(self):
        c = self.collect()
        folder = os.path.join(self.app.library.root_dir, *[x for x in self.v_domain.get().split("/") if x])
        os.makedirs(folder, exist_ok=True)
        f = filedialog.asksaveasfilename(parent=self, initialdir=folder, defaultextension=".json",
                                         initialfile=c.name.replace(" ", "_") + ".json",
                                         filetypes=[("PyPWCT Component", "*.json")])
        if not f:
            return False
        return self._write(f)

    def _write(self, path):
        c = self.collect()
        if not c.name.strip():
            messagebox.showwarning("Sorry", "You should enter the component name", parent=self)
            return False
        vars_ = [v for _, v, _ in c.variables()]
        dup = {v for v in vars_ if vars_.count(v) > 1}
        if dup:
            messagebox.showwarning("Sorry", "Duplicated variables : " + ", ".join(sorted(dup)), parent=self)
            return False
        try:
            c.save(path)
        except OSError as ex:
            messagebox.showerror("Error", str(ex), parent=self)
            return False
        self.dirty = False
        self.update_file_label()
        self.app.reload_components()
        self.app.status("Component saved : " + path)
        return True

    def close(self):
        if self.ask_save():
            self.destroy()

    # ============================================================== test
    def test(self):
        c = self.collect()
        project = Project()
        goal = project.goals[0]
        gen = Generator(project, self.app.library, self.app.language)
        result = {}

        def on_ok(values, again):
            try:
                gen.run(c, values, goal, goal.root)
            except InteractionError as ex:
                messagebox.showwarning("Sorry", str(ex), parent=win)
                return False
            result["ok"] = True
            return True

        win = InteractionWindow(self, c, project, on_ok, allow_again=True, title_suffix=" (Test)")
        win.show()
        if result:
            PreviewDialog(self, project, self.app.language).show()


class PreviewDialog(Dialog):
    """Steps and code generated by the test of a component."""

    def __init__(self, parent, project, lang=None):
        super().__init__(parent, "Test - Generated Steps and Code", size=(900, 520))
        pw = ttk.PanedWindow(self.body, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=6, pady=6)
        tree = ttk.Treeview(pw, show="tree")
        pw.add(tree, weight=1)
        code_view = ScrolledText(pw, font=("Consolas", 10))
        pw.add(code_view, weight=1)
        root = project.goals[0].root

        def add(parent, step):
            for s in step.children:
                label = "%s   [%d]" % (s.name, s.internum)
                tree.insert(parent, "end", iid=s.id, text=label, open=True)
                add(s.id, s)
        tree.insert("", "end", iid=root.id, text=root.name, open=True)
        add(root.id, root)
        files = {}
        code, _ = codegen.generate(project, header=False, files=files, lang=lang)
        code_view.set(codegen.with_files(code, files), readonly=True)
        highlight_python(code_view.text, lang)
        self.button_bar([("Close", self.cancel)])
