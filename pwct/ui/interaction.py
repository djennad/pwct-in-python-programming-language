"""Interaction Using Transporter (port of runtrf.scx).

Shows the interaction pages of a component so the user can enter the data,
then Ok / Again send the values to the code generator.
"""

import re
import tkinter as tk
from tkinter import ttk

from ..engine import default_values, expand_default
from .common import Dialog, Gradient, hex_color, SILVER_BOTTOM, UI_FONT, UI_BOLD, ToolTip


def _font(spec, default=("Arial", 10)):
    if not spec:
        return default
    spec = list(spec)
    return tuple(spec[:2]) + tuple(s for s in spec[2:] if s in ("bold", "italic", "underline"))


def _short_path(component):
    if not component.path:
        return component.name + " (not saved)"
    parts = component.path.replace("\\", "/").split("/")
    if "components" in parts:
        return "/".join(parts[len(parts) - 1 - parts[::-1].index("components"):])
    return component.path


def build_page(master, page, values, project=None, component=None, design=False):
    """Create the widgets of one interaction page.  Returns (frame, {var: getter}, widgets)."""
    bg = page.get("bgcolor") or "#ffffff"
    frame = tk.Frame(master, bg=bg, width=page.get("width", 620), height=page.get("height", 320))
    frame.pack_propagate(False)
    getters = {}
    widgets = []
    for c in page["controls"]:
        t = c.get("type")
        cbg = c.get("bg") or bg
        fg = c.get("fg") or "#000000"
        font = _font(c.get("font"))
        var = c.get("var")
        if t == "label":
            w = tk.Label(frame, text=c.get("caption", ""), fg=fg, bg=cbg, font=font, anchor="w",
                         justify="left", wraplength=max(c.get("w", 100) - 4, 20))
        elif t == "textbox":
            w = tk.Entry(frame, fg=fg, bg=cbg, font=font, relief="solid", bd=1,
                         insertbackground=fg, disabledbackground=cbg, readonlybackground=cbg)
            v = values.get(var) if var in values else expand_default(c.get("text", ""), project, component)
            w.insert(0, "" if v is None else str(v))
            if design:
                w.configure(state="readonly")
            getters[var] = w.get
        elif t == "listbox":
            w = tk.Listbox(frame, fg=fg, bg=cbg, font=font, exportselection=False, relief="solid", bd=1,
                           activestyle="none", selectbackground="#0a64ad", selectforeground="#ffffff",
                           highlightthickness=0)
            for it in c.get("items", []):
                w.insert("end", " " + it)
            idx = values.get(var, c.get("selected", 0)) if var else 0
            try:
                idx = int(idx)
            except (TypeError, ValueError):
                idx = 0
            if w.size():
                idx = max(0, min(idx, w.size() - 1))
                w.selection_set(idx)
                w.see(idx)
            getters[var] = (lambda lb=w: (lb.curselection() or (0,))[0])
        elif t == "checkbox":
            iv = tk.IntVar(value=int(values.get(var, c.get("value", 0)) or 0))
            w = tk.Checkbutton(frame, text=c.get("caption", ""), variable=iv, fg=fg, bg=cbg,
                               activebackground=cbg, selectcolor="#ffffff", font=font, anchor="w")
            w._var = iv
            getters[var] = iv.get
        else:
            continue
        w.place(x=c.get("x", 0), y=c.get("y", 0), width=c.get("w", 100), height=c.get("h", 24))
        widgets.append((c, w))
    return frame, getters, widgets


class InteractionWindow(Dialog):
    def __init__(self, parent, component, project, on_ok, values=None, allow_again=True,
                 names_provider=None, title_suffix=""):
        super().__init__(parent, "Interaction Using Transporter" + title_suffix,
                         header="Interaction Using Transporter")
        self.component = component
        self.project = project
        self.on_ok = on_ok
        self.names_provider = names_provider
        self.values = dict(default_values(component, project))
        if values:
            self.values.update(values)
        self.page_index = 0
        self.getters = {}
        self.focus_widgets = {}

        info = tk.Frame(self.body, bg="#e8e8e8", height=26)
        info.pack(fill="x")
        tk.Label(info, text=" FILE( %s )" % _short_path(component), bg="#e8e8e8",
                 font=UI_FONT, anchor="w").pack(fill="x", padx=4, pady=3)

        area = tk.Frame(self.body, bg="#f4f4f4")
        area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(area, bg="#f4f4f4", highlightthickness=0)
        ys = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        xs = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)

        self.pages = []
        for p in component.pages:
            frame, getters, widgets = build_page(self.canvas, p, self.values, project, component)
            item = self.canvas.create_window(12, 12, window=frame, anchor="nw", state="hidden")
            self.pages.append((p, frame, item))
            self.getters.update(getters)
            for c, w in widgets:
                if c.get("type") == "textbox":
                    w.bind("<Return>", lambda e: self.ok())
                    w.bind("<Control-Return>", lambda e: self.again())
                    w.bind("<Control-space>", self._intellisense)
                    self.focus_widgets.setdefault(p["name"], w)
                    if c.get("focus"):
                        self.focus_widgets[p["name"]] = w
                    if "<autonumber>" in c.get("text", "").lower():
                        w._autotext = c["text"]
                elif c.get("type") == "listbox":
                    w.bind("<Double-Button-1>", lambda e: self.ok())
                    w.bind("<Return>", lambda e: self.ok())
                    self.focus_widgets.setdefault(p["name"], w)

        # ----- bottom bar (page navigation + Again / Ok / Cancel)
        bar = Gradient(self, height=42)
        bar.pack(fill="x", side="bottom")
        right = tk.Frame(bar, bg=hex_color(SILVER_BOTTOM))
        bar.create_window(0, 7, window=right, anchor="ne", tags="right")
        bar.bind("<Configure>", lambda e: bar.coords("right", e.width - 8, 7), add="+")
        self.nav = []
        if len(self.pages) > 1:
            left = tk.Frame(bar, bg=hex_color(SILVER_BOTTOM))
            bar.create_window(6, 7, window=left, anchor="nw")
            for txt, cmd in (("|<", self.first), ("<", self.prev), (">", self.next), (">|", self.last)):
                b = ttk.Button(left, text=txt, width=4, command=cmd)
                b.pack(side="left", padx=1)
                self.nav.append(b)
            self.page_combo = ttk.Combobox(left, state="readonly", width=18,
                                           values=[p["name"] for p, _, _ in self.pages])
            self.page_combo.pack(side="left", padx=8)
            self.page_combo.bind("<<ComboboxSelected>>", lambda e: self.show_page(self.page_combo.current()))
        if allow_again:
            b = ttk.Button(right, text="Again", width=9, command=self.again)
            b.pack(side="left", padx=3)
            ToolTip(b, "Generate the steps and keep this window open (Ctrl+Enter)")
        ttk.Button(right, text="Ok", width=9, command=self.ok).pack(side="left", padx=3)
        ttk.Button(right, text="Cancel", width=9, command=self.cancel).pack(side="left", padx=3)
        self.bar = bar
        self.msg = bar.create_text(len(self.nav) * 50 + (170 if self.nav else 0) + 14, 21, text="", anchor="w",
                                   fill="#006000", font=UI_BOLD)

        self.bind("<Prior>", lambda e: self.prev())
        self.bind("<Next>", lambda e: self.next())
        w = max(p.get("width", 620) for p, _, _ in self.pages) + 48
        h = max(p.get("height", 320) for p, _, _ in self.pages) + 160
        self._size = (max(min(w, self.winfo_screenwidth() - 80), 520), min(h, self.winfo_screenheight() - 120))
        self.show_page(0)

    # ------------------------------------------------------------- pages
    def show_page(self, index):
        self.page_index = index
        for k, (p, frame, item) in enumerate(self.pages):
            self.canvas.itemconfigure(item, state="normal" if k == index else "hidden")
        p, frame, _ = self.pages[index]
        self.canvas.configure(scrollregion=(0, 0, p.get("width", 620) + 24, p.get("height", 320) + 24))
        if self.nav:
            self.page_combo.current(index)
            for b in self.nav[:2]:
                b.state(["disabled"] if index == 0 else ["!disabled"])
            for b in self.nav[2:]:
                b.state(["disabled"] if index == len(self.pages) - 1 else ["!disabled"])
        w = self.focus_widgets.get(p["name"])
        if w is not None:
            self.after(60, lambda: (w.focus_set(), w.select_range(0, "end") if isinstance(w, tk.Entry) else None))

    def first(self):
        self.show_page(0)

    def last(self):
        self.show_page(len(self.pages) - 1)

    def prev(self):
        if self.page_index > 0:
            self.show_page(self.page_index - 1)

    def next(self):
        if self.page_index < len(self.pages) - 1:
            self.show_page(self.page_index + 1)

    # ------------------------------------------------------------ values
    def collect(self):
        return {var: g() for var, g in self.getters.items()}

    def ok(self):
        values = self.collect()
        if self.on_ok(values, False):
            self.result = values
            self.destroy()

    def again(self):
        values = self.collect()
        if self.on_ok(values, True):
            self.bar.itemconfigure(self.msg, text="Done - you can use this interaction again")
            self.after(2500, lambda: self.bar.winfo_exists() and self.bar.itemconfigure(self.msg, text=""))
            for p, frame, _ in self.pages:
                for w in frame.winfo_children():
                    if getattr(w, "_autotext", None):
                        w.delete(0, "end")
                        w.insert(0, expand_default(w._autotext, self.project, self.component))
            self.show_page(self.page_index)

    # ------------------------------------------------------- intellisense
    def _intellisense(self, event):
        entry = event.widget
        names = sorted(set(self.names_provider() if self.names_provider else []), key=str.lower)
        if not names:
            return "break"
        text = entry.get()[:entry.index("insert")]
        m = re.search(r"[A-Za-z_][A-Za-z0-9_]*$", text)
        prefix = m.group(0) if m else ""
        items = [n for n in names if n.lower().startswith(prefix.lower())] or names
        pop = tk.Toplevel(self)
        pop.wm_overrideredirect(True)
        pop.geometry("+%d+%d" % (entry.winfo_rootx(), entry.winfo_rooty() + entry.winfo_height()))
        lb = tk.Listbox(pop, height=min(len(items), 8), font=("Consolas", 10), activestyle="dotbox")
        lb.pack()
        for n in items:
            lb.insert("end", n)
        lb.selection_set(0)
        lb.focus_set()

        def choose(_e=None):
            sel = lb.curselection()
            if sel:
                pos = entry.index("insert")
                entry.delete(pos - len(prefix), pos)
                entry.insert(pos - len(prefix), lb.get(sel[0]))
            pop.destroy()
            entry.focus_set()
            return "break"

        lb.bind("<Return>", choose)
        lb.bind("<Double-Button-1>", choose)
        lb.bind("<Escape>", lambda e: (pop.destroy(), entry.focus_set()))
        lb.bind("<FocusOut>", lambda e: pop.destroy())
        return "break"
