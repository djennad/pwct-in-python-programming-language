"""Form Designer (the Form Designer button of rpwi.scx - Ctrl+F).

Visual design of a window: the controls are real Tkinter widgets (what you see is
what the program shows).  Saving writes the design to the steps tree through the
components (see pwct/forms.py), so every control stays a normal step.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox

from ..engine import InteractionError
from ..forms import FormModel, control_components, function_component, items_list, items_text, is_identifier
from .common import Dialog, Gradient, ToolTip, center, icon_button, image, UI_BOLD, UI_FONT

OX, OY, TITLE_H = 30, 30, 30
SNAP = 5


class SelectWindowDialog(Dialog):
    """Select the window to design (selwin.scx)."""

    def __init__(self, parent, windows):
        super().__init__(parent, "Form Designer - Select Window", size=(420, 330), resizable=False)
        self.windows = windows
        tk.Label(self.body, text="Windows in the active goal :", bg="#ffffff", font=UI_BOLD).pack(
            anchor="w", padx=12, pady=(8, 2))
        self.list = tk.Listbox(self.body, font=("Segoe UI", 10), activestyle="none")
        self.list.pack(fill="both", expand=True, padx=12)
        for _, name in windows:
            self.list.insert("end", "  " + name)
        if windows:
            self.list.selection_set(0)
        else:
            self.list.insert("end", "  (No windows - create a new window)")
        self.list.bind("<Double-Button-1>", lambda e: self.ok())
        self.button_bar([("Open", self.ok), ("New Window", self.new), ("Cancel", self.cancel)])

    def ok(self):
        sel = self.list.curselection()
        if sel and self.windows:
            self.result = self.windows[sel[0]][0]
            self.destroy()

    def new(self):
        self.result = "new"
        self.destroy()


class FormDesigner(tk.Toplevel):
    def __init__(self, app, model):
        super().__init__(app.root)
        self.app = app
        self.m = model
        self.sel = None                 # FormControl or None (= the window)
        self.widgets = {}               # FormControl -> widget
        self.drag = None
        ic = image("app_icon")
        if ic:
            self.iconphoto(False, ic)
        self.configure(bg="#ffffff")
        self._build()
        self.render()
        self.show_props()
        center(self, None, 1180, 740)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Control-s>", lambda e: (self.save(), "break")[1])
        self.bind("<Delete>", self._key_delete)
        self.bind("<KeyPress>", self._arrow)
        self.update_title()

    # ================================================================ UI
    def _build(self):
        tb = Gradient(self, height=42)
        tb.pack(fill="x")
        x = 8
        for img, text, tip, cmd in (("save", " Save", "Save the design to the steps (Ctrl+S)", self.save),
                                    (None, "Save and Run", "Save then run the program (Ctrl+R)", self.save_run),
                                    ("wzclose", " Close", "Close the Form Designer", self.close)):
            b = icon_button(tb, img, tip, cmd, text=text, padx=6)
            tb.create_window(x, 21, window=b, anchor="w")
            x += 110 if img is None else 80
        tb.create_line(x, 8, x, 34, fill="#a0a0a0")
        tb.create_text(x + 10, 21, text="Controls :", anchor="w", font=UI_BOLD)
        x += 80
        self.toolbox = control_components(self.app.library)
        for comp in self.toolbox:
            b = ttk.Button(tb, text="+ " + comp.name, command=lambda c=comp: self.add(c))
            tb.create_window(x, 21, window=b, anchor="w")
            ToolTip(b, comp.description)
            x += 8 * len(comp.name) + 36
        b = ttk.Button(tb, text="Delete", command=self.delete)
        tb.create_window(x + 6, 21, window=b, anchor="w")
        self.snap = tk.IntVar(value=1)
        cb = tk.Checkbutton(tb, text="Snap", variable=self.snap, bg="#e4e4e4", font=UI_FONT)
        tb.create_window(x + 74, 21, window=cb, anchor="w")
        tk.Frame(self, height=1, bg="#808080").pack(fill="x")

        self.status = tk.Label(self, text="", bg="#e8e8e8", font=UI_FONT, anchor="w", padx=8)
        self.status.pack(fill="x", side="bottom")

        main = tk.Frame(self, bg="#ffffff")
        main.pack(fill="both", expand=True)
        self.props = tk.Frame(main, bg="#f7f7f7", width=300, bd=1, relief="solid")
        self.props.pack(side="right", fill="y", padx=6, pady=6)
        self.props.pack_propagate(False)
        area = tk.Frame(main, bg="#b8b8b8")
        area.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        self.canvas = tk.Canvas(area, bg="#b8b8b8", highlightthickness=0)
        ys = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        xs = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)
        self.canvas.tag_bind("titlebar", "<Button-1>", lambda e: self.select(None))
        self.canvas.tag_bind("wgrip", "<Button-1>", self._wgrip_press)
        self.canvas.tag_bind("wgrip", "<B1-Motion>", self._wgrip_motion)
        self.canvas.tag_bind("wgrip", "<ButtonRelease-1>", self._release)
        self.client = None

    def update_title(self):
        self.title("Form Designer - %s%s" % (self.m.window.name, "  *" if self.m.dirty else ""))

    def say(self, text, error=False):
        self.status.configure(text=text, fg="#b00000" if error else "#000000")

    # ============================================================ render
    def window_size(self):
        w = self.m.window.geti("w", 400) or 400
        h = self.m.window.geti("h", 300) or 300
        return max(w, 60), max(h, 40)

    def render(self):
        c = self.canvas
        c.delete("chrome")
        if self.client is not None:
            self.client.destroy()
        w, h = self.window_size()
        c.create_rectangle(OX - 1, OY - 1, OX + w, OY + TITLE_H + h, outline="#606060", tags="chrome")
        c.create_rectangle(OX, OY, OX + w, OY + TITLE_H, fill="#1f5fa8", outline="", tags=("chrome", "titlebar"))
        title = self.m.window.get("title") or self.m.window.name
        c.create_text(OX + 10, OY + TITLE_H // 2, text=title, anchor="w", fill="#ffffff",
                      font=("Segoe UI", 10), tags=("chrome", "titlebar"))
        c.create_text(OX + w - 12, OY + TITLE_H // 2, text="✕   ", anchor="e", fill="#ffffff",
                      font=("Segoe UI", 10), tags=("chrome", "titlebar"))
        bg = self.m.window.get("bg") or None
        self.client = tk.Frame(c, width=w, height=h)
        if bg:
            try:
                self.client.configure(bg=bg)
            except tk.TclError:
                self.say("Unknown color : " + bg, True)
        self.client.pack_propagate(False)
        c.create_window(OX, OY + TITLE_H, window=self.client, anchor="nw", tags="chrome")
        c.create_rectangle(OX + w - 5, OY + TITLE_H + h - 5, OX + w + 5, OY + TITLE_H + h + 5, fill="#000000",
                           outline="#ffffff", tags=("chrome", "wgrip"))
        c.configure(scrollregion=(0, 0, OX + w + 80, OY + TITLE_H + h + 80))
        self.client.bind("<Button-1>", lambda e: self.select(None))
        self.widgets = {}
        for ctrl in self.m.controls:
            if ctrl.deleted:
                continue
            wdg = self.make_widget(ctrl)
            if wdg is None:
                continue
            self.widgets[ctrl] = wdg
            wdg.bind("<Button-1>", lambda e, cc=ctrl: self._press(e, cc))
            wdg.bind("<B1-Motion>", self._motion)
            wdg.bind("<ButtonRelease-1>", self._release)
            wdg.bind("<Double-Button-1>", lambda e, cc=ctrl: self._double(cc))
            wdg.bind("<Key>", lambda e: "break")
        self.handles = [tk.Frame(self.client, bg="#ff0000") for _ in range(4)]
        self.grip = tk.Frame(self.client, bg="#000000", width=8, height=8, cursor="size_nw_se")
        self.grip.bind("<Button-1>", lambda e: self._press(e, self.sel, resize=True))
        self.grip.bind("<B1-Motion>", self._motion)
        self.grip.bind("<ButtonRelease-1>", self._release)
        self.show_selection()
        self.update_title()

    def make_widget(self, ctrl):
        size = ctrl.geti("size", 10) or 10
        font = ("Arial", size)
        k = ctrl.kind
        p = self.client
        if k == "label":
            w = tk.Label(p, text=ctrl.get("text"), font=font)
        elif k == "button":
            w = tk.Button(p, text=ctrl.get("text"), font=font)
        elif k == "textbox":
            try:
                chars = int(ctrl.values.get("width", 20))
            except (TypeError, ValueError):
                chars = 20
            w = tk.Entry(p, width=chars, font=font)
        elif k == "textarea":
            w = tk.Text(p, font=font, width=20, height=5)
        elif k == "checkbox":
            var = tk.IntVar(value=int(ctrl.values.get("checked", 0) or 0))
            w = tk.Checkbutton(p, text=ctrl.get("text"), font=font, variable=var)
            w._var = var
        elif k == "listbox":
            w = tk.Listbox(p, font=font, exportselection=False)
            for it in items_list(ctrl.get("items")):
                w.insert("end", it)
        else:
            return None
        for prop, opt in (("fg", "fg"), ("bg", "bg")):
            val = ctrl.get(prop)
            if val:
                try:
                    w.configure(**{opt: val})
                except tk.TclError:
                    self.say("%s : unknown color %s" % (ctrl.name, val), True)
        x, y = ctrl.geti("x", 0), ctrl.geti("y", 0)
        opts = {"x": x if x is not None else 0, "y": y if y is not None else 0}
        cw, ch = ctrl.geti("w", None), ctrl.geti("h", None)
        if cw:
            opts["width"] = cw
        if ch:
            opts["height"] = ch
        w.place(**opts)
        return w

    def geometry_of(self, ctrl):
        wdg = self.widgets.get(ctrl)
        x, y = ctrl.geti("x", 0) or 0, ctrl.geti("y", 0) or 0
        w, h = ctrl.geti("w", None), ctrl.geti("h", None)
        if wdg is not None:
            wdg.update_idletasks()
            w = w or wdg.winfo_reqwidth()
            h = h or wdg.winfo_reqheight()
        return x, y, w or 40, h or 20

    def show_selection(self):
        c = self.sel
        if c is None or c not in self.widgets:
            for f in self.handles:
                f.place_forget()
            self.grip.place_forget()
            return
        x, y, w, h = self.geometry_of(c)
        b = 2
        self.handles[0].place(x=x - b, y=y - b, width=w + 2 * b, height=b)
        self.handles[1].place(x=x - b, y=y + h, width=w + 2 * b, height=b)
        self.handles[2].place(x=x - b, y=y, width=b, height=h)
        self.handles[3].place(x=x + w, y=y, width=b, height=h)
        self.grip.place(x=x + w - 4, y=y + h - 4)
        for f in self.handles + [self.grip]:
            f.lift()

    # ============================================================ mouse
    def _snap(self, v):
        return int(round(v / SNAP) * SNAP) if self.snap.get() else int(v)

    def _press(self, e, ctrl, resize=False):
        if ctrl is None:
            return "break"
        if ctrl is not self.sel:
            self.select(ctrl)
        x, y, w, h = self.geometry_of(ctrl)
        self.drag = (e.x_root, e.y_root, x, y, w, h, resize)
        self.canvas.focus_set()
        return "break"

    def _motion(self, e):
        if not self.drag or self.sel is None:
            return "break"
        x0, y0, cx, cy, cw, ch, resize = self.drag
        dx, dy = e.x_root - x0, e.y_root - y0
        c = self.sel
        wdg = self.widgets.get(c)
        if resize:
            c.set("w", str(max(10, self._snap(cw + dx))))
            c.set("h", str(max(10, self._snap(ch + dy))))
            if wdg is not None:
                wdg.place_configure(width=int(c.get("w")), height=int(c.get("h")))
        else:
            c.set("x", str(max(0, self._snap(cx + dx))))
            c.set("y", str(max(0, self._snap(cy + dy))))
            if wdg is not None:
                wdg.place_configure(x=int(c.get("x")), y=int(c.get("y")))
        self.show_selection()
        self.say("%s : x=%s  y=%s  width=%s  height=%s" % (c.name, c.get("x"), c.get("y"),
                                                           c.get("w") or "auto", c.get("h") or "auto"))
        return "break"

    def _release(self, _e):
        if self.drag:
            self.drag = None
            self.update_title()
            self.show_props()
        return "break"

    def _wgrip_press(self, e):
        self.select(None)
        w, h = self.window_size()
        self.drag = (e.x_root, e.y_root, 0, 0, w, h, "window")

    def _wgrip_motion(self, e):
        if not self.drag:
            return
        x0, y0, _, _, w0, h0, _ = self.drag
        self.m.window.set("w", str(max(100, self._snap(w0 + e.x_root - x0))))
        self.m.window.set("h", str(max(60, self._snap(h0 + e.y_root - y0))))
        self.render()
        w, h = self.window_size()
        self.say("Window : %d x %d" % (w, h))

    def _arrow(self, e):
        if self.sel is None or self.focus_get() is not self.canvas:
            return
        step = 10 if e.state & 0x0001 else 1
        d = {"Left": (-step, 0), "Right": (step, 0), "Up": (0, -step), "Down": (0, step)}.get(e.keysym)
        if d:
            c = self.sel
            c.set("x", str(max(0, (c.geti("x", 0) or 0) + d[0])))
            c.set("y", str(max(0, (c.geti("y", 0) or 0) + d[1])))
            self.render()
            self.show_props()
            return "break"

    def _key_delete(self, _e):
        if self.focus_get() is self.canvas:
            self.delete()
            return "break"

    def _double(self, ctrl):
        if ctrl.has("command"):
            self.event_code(ctrl)
        return "break"

    # ============================================================ editing
    def select(self, ctrl):
        self.sel = ctrl
        self.show_selection()
        self.show_props()

    def add(self, comp):
        n = len([c for c in self.m.controls if not c.deleted])
        c = self.m.add(comp, 20 + 10 * (n % 10), 20 + 10 * (n % 10))
        self.render()
        self.select(c)
        self.say("New %s : %s  (Save to create its step)" % (comp.name, c.name))

    def delete(self):
        if self.sel is None:
            return
        name = self.sel.name
        self.m.delete(self.sel)
        self.sel = None
        self.render()
        self.show_props()
        self.say("Deleted : %s  (Save to delete its steps)" % name)

    # ======================================================= properties
    def show_props(self):
        for w in self.props.winfo_children():
            w.destroy()
        f = self.props
        tk.Label(f, text="Objects", bg="#e0e0e0", font=UI_BOLD, anchor="w").pack(fill="x")
        objs = [None] + [c for c in self.m.controls if not c.deleted]
        lb = tk.Listbox(f, height=min(len(objs), 7), font=("Segoe UI", 9), exportselection=False,
                        activestyle="none")
        for o in objs:
            lb.insert("end", "  %s  (%s)" % ((self.m.window.name, "window") if o is None else (o.name, o.kind)))
        lb.pack(fill="x", padx=4, pady=2)
        lb.selection_set(objs.index(self.sel) if self.sel in objs else 0)
        lb.bind("<<ListboxSelect>>", lambda e: self.select(objs[lb.curselection()[0]]) if lb.curselection() else None)

        tk.Label(f, text="Properties", bg="#e0e0e0", font=UI_BOLD, anchor="w").pack(fill="x", pady=(4, 0))
        body = tk.Frame(f, bg="#f7f7f7")
        body.pack(fill="both", expand=True, padx=6, pady=4)
        self._row = 0
        c = self.sel
        if c is None:
            w = self.m.window
            tk.Label(body, text="WINDOW (%s)" % w.component.name, bg="#f7f7f7", fg="#400040",
                     font=UI_BOLD).grid(row=0, column=0, columnspan=2, sticky="w")
            self._row = 1
            self._entry(body, "Name", w, "name", rename_window=True)
            self._entry(body, "Title", w, "title")
            self._entry(body, "Width", w, "w", number=True)
            self._entry(body, "Height", w, "h", number=True)
            self._color(body, "Back Color", w, "bg")
            if w.has("show"):
                self._check(body, "Show", "Show the window (mainloop)", w, "show")
            self._step_info(body, w)
            return
        tk.Label(body, text="%s (%s)" % (c.kind.upper(), c.component.name), bg="#f7f7f7", fg="#400040",
                 font=UI_BOLD).grid(row=0, column=0, columnspan=2, sticky="w")
        self._row = 1
        self._entry(body, "Name", c, "name")
        if c.has("text"):
            self._entry(body, "Text", c, "text")
        if c.has("command"):
            self._command(body, c)
        if c.has("items"):
            self._items(body, c)
        for prop, label in (("x", "Left (X)"), ("y", "Top (Y)"), ("w", "Width"), ("h", "Height")):
            if c.has(prop):
                self._entry(body, label, c, prop, number=True, allow_empty=prop in ("w", "h"))
        if c.has("size"):
            self._entry(body, "Font Size", c, "size", number=True)
        if c.has("fg"):
            self._color(body, "Text Color", c, "fg")
        if c.has("bg"):
            self._color(body, "Back Color", c, "bg")
        self._step_info(body, c)

    def _label(self, body, text):
        tk.Label(body, text=text, bg="#f7f7f7", font=UI_FONT, anchor="w").grid(row=self._row, column=0,
                                                                              sticky="w", pady=1)

    def _changed(self):
        self.render()
        self.update_title()

    def _entry(self, body, text, ctrl, prop, number=False, allow_empty=False, rename_window=False):
        self._label(body, text)
        v = tk.StringVar(value=ctrl.get(prop))
        e = ttk.Entry(body, textvariable=v, width=22)
        e.grid(row=self._row, column=1, sticky="ew", pady=1)
        body.columnconfigure(1, weight=1)

        def apply(_e=None):
            val = v.get().strip() if number or prop == "name" else v.get()
            if val == ctrl.get(prop):
                return
            if number and val:
                try:
                    float(val)
                except ValueError:
                    self.say("%s must be a number" % text, True)
                    return
            if number and not val and not allow_empty:
                return
            if prop == "name" and not is_identifier(val):
                self.say("The name (%s) is not valid" % val, True)
                return
            if rename_window:
                self.m.rename_window(val)
            else:
                ctrl.set(prop, val)
            self._changed()
            self.say("%s = %s" % (text, val or "(auto)"))
        e.bind("<Return>", apply)
        e.bind("<FocusOut>", apply)
        self._row += 1

    def _color(self, body, text, ctrl, prop):
        self._label(body, text)
        cur = ctrl.get(prop)
        b = tk.Button(body, text=cur or "(Default)", relief="solid", bd=1, font=UI_FONT, cursor="hand2")
        try:
            b.configure(bg=cur or "#f7f7f7")
        except tk.TclError:
            pass
        b.grid(row=self._row, column=1, sticky="ew", pady=1)

        def pick():
            col = colorchooser.askcolor(cur or "#ffffff", parent=self)[1]
            if col:
                ctrl.set(prop, col)
                self._changed()
                self.show_props()

        def clear(_e=None):
            ctrl.set(prop, "")
            self._changed()
            self.show_props()
        b.configure(command=pick)
        b.bind("<Button-3>", clear)
        ToolTip(b, "Click: choose a color   Right click: default color")
        self._row += 1

    def _check(self, body, text, caption, ctrl, prop):
        self._label(body, text)
        v = tk.IntVar(value=1 if ctrl.get(prop, "0") not in ("", "0") else 0)

        def apply():
            ctrl.set(prop, v.get())
            self._changed()
            self.say("%s = %s" % (text, "Yes" if v.get() else "No"))
        tk.Checkbutton(body, text=caption, variable=v, command=apply, bg="#f7f7f7", font=UI_FONT,
                       anchor="w").grid(row=self._row, column=1, sticky="w", pady=1)
        self._row += 1

    def _command(self, body, ctrl):
        self._label(body, "On Click")
        v = tk.StringVar(value=ctrl.get("command"))
        cb = ttk.Combobox(body, textvariable=v, values=[""] + self.m.functions(), width=19)
        cb.grid(row=self._row, column=1, sticky="ew", pady=1)

        def apply(_e=None):
            val = v.get().strip()
            if val != ctrl.get("command"):
                ctrl.set("command", val)
                self._changed()
        cb.bind("<<ComboboxSelected>>", apply)
        cb.bind("<Return>", apply)
        cb.bind("<FocusOut>", apply)
        self._row += 1
        ttk.Button(body, text="Event Code (double click)", command=lambda: self.event_code(ctrl)).grid(
            row=self._row, column=0, columnspan=2, sticky="ew", pady=2)
        self._row += 1

    def _items(self, body, ctrl):
        self._label(body, "Items")
        t = tk.Text(body, height=4, width=20, font=("Consolas", 9))
        t.insert("1.0", "\n".join(items_list(ctrl.get("items"))))
        t.grid(row=self._row, column=1, sticky="ew", pady=1)

        def apply(_e=None):
            lines = [ln for ln in t.get("1.0", "end-1c").splitlines() if ln.strip()]
            val = items_text(lines)
            if val != ctrl.get("items"):
                ctrl.set("items", val)
                self._changed()
        t.bind("<FocusOut>", apply)
        self._row += 1

    def _step_info(self, body, ctrl):
        if ctrl.is_new:
            text = "Step : (new - Save to create it)"
        else:
            root = self.m.project.interaction_root(ctrl.interaction.id)
            text = "Step : " + (root.name if root else "?")
        tk.Label(body, text=text, bg="#f7f7f7", fg="#505050", font=UI_FONT, wraplength=270,
                 justify="left").grid(row=self._row, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self._row += 1
        if not ctrl.is_new:
            ttk.Button(body, text="Show in the Steps Tree", command=lambda: self.goto(ctrl)).grid(
                row=self._row, column=0, columnspan=2, sticky="ew")
            self._row += 1

    # ======================================================== save / run
    def save(self, quiet=False):
        if not self.m.dirty:
            if not quiet:
                self.say("No changes")
            return True
        try:
            updated, added, deleted = self.m.apply(self.app.generator)
        except InteractionError as ex:
            messagebox.showwarning("Form Designer", str(ex), parent=self)
            return False
        self.after_save()
        self.say("Saved to the steps : %d updated, %d added, %d deleted" % (updated, added, deleted))
        return True

    def after_save(self):
        self.app.project.modified = True
        self.app.update_title()
        root = self.m.project.interaction_root(self.m.window.interaction.id)
        self.app.gd.refresh(select=root.id if root else None)
        self.render()
        self.show_props()

    def save_run(self):
        if self.save(quiet=True):
            self.app.run_program()

    def event_code(self, ctrl):
        """Double click on a button: go to its function, or create <name>_click."""
        cmd = ctrl.get("command")
        if cmd and cmd in self.m.functions():
            self.goto_function(cmd)
            return
        if not self.save(quiet=True):
            return
        if ctrl.is_new:
            return
        try:
            name, start = self.m.create_event(ctrl, self.app.generator)
            self.m.apply(self.app.generator)
        except InteractionError as ex:
            messagebox.showwarning("Form Designer", str(ex), parent=self)
            return
        self.after_save()
        self.say("New event function : %s" % name)
        if start is not None and messagebox.askyesno(
                "Form Designer", "The function %s is created.\n\nGo to its steps now?" % name, parent=self):
            self.destroy()
            self.app.gd.goto_step(start.id)

    def goto_function(self, name):
        p = self.m.project
        fn = function_component(self.app.library)
        for it in p.interactions:
            if fn is not None and it.component == fn.key and it.values.get("name") == name:
                steps = p.interaction_steps(it.id)
                start = next((s for s in steps if s.name == "Start Here"), steps[0] if steps else None)
                if start is not None:
                    if self.close():
                        self.app.gd.goto_step(start.id)
                    return

    def goto(self, ctrl):
        root = self.m.project.interaction_root(ctrl.interaction.id)
        if root is not None and self.close():
            self.app.gd.goto_step(root.id)

    def close(self):
        if self.m.dirty:
            r = messagebox.askyesnocancel("Form Designer", "Save the design to the steps ?", parent=self)
            if r is None:
                return False
            if r and not self.save(quiet=True):
                return False
        self.destroy()
        return True


def open_form_designer(app):
    """Goal Designer > Form Designer (Ctrl+F)."""
    from ..forms import window_component
    gd = app.gd
    if not gd.live():
        app.status("The Time Machine : go to the last time frame first")
        return
    if window_component(app.library) is None:
        messagebox.showinfo("Form Designer", "The Form Designer needs window components (a designer mapping).\n"
                            "They are available in PythonPWCT.", parent=app.root)
        return
    project, goal = app.project, gd.goal
    sel = gd.selected()
    wit = FormModel.window_of_step(project, app.library, goal, sel) if sel is not None else None
    if wit is None:
        wins = FormModel.windows(project, app.library, goal)
        res = SelectWindowDialog(gd, wins).show()
        if res is None:
            return
        if res == "new":
            parent = sel if (sel is not None and gd._can("interact")) else goal.root
            wit = FormModel.create_window(project, app.library, app.generator, goal, parent)
            project.modified = True
            app.update_title()
            gd.refresh()
        else:
            wit = res
    FormDesigner(app, FormModel(project, app.library, goal, wit, app.language))
