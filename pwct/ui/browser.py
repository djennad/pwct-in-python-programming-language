"""Components Browser (port of selser.scx): Domain Tree + components + search.

Like PWCT, the tree starts with the name of the Visual Programming Language
(HarbourPWCT, PythonPWCT...) and the domains are nested (User Interface >
GUI Application > Windows...).  A domain without components of its own shows
the components of its sub domains."""

import tkinter as tk
from tkinter import ttk

from .common import ClassicTree, Dialog, UI_FONT

ROOT = "::root::"


class ComponentsBrowser(Dialog):
    def __init__(self, parent, library, allowed=None, search="", last_domain=None, root_name="Components"):
        super().__init__(parent, "Components Browser", size=(880, 560))
        self.library = library
        self.allowed = allowed or (lambda c: True)
        self.shown = []

        page = tk.Frame(self.body, bg="#ffffff")
        page.pack(fill="both", expand=True, padx=10, pady=(4, 0))
        tk.Label(page, text="Select Domain :", bg="#ffffff", font=UI_FONT).grid(
            row=0, column=0, sticky="w", padx=2, pady=(6, 8))
        tk.Label(page, text="Components in Domain", bg="#ffffff", font=UI_FONT).grid(
            row=0, column=1, sticky="w", padx=14, pady=(6, 8))

        tf = tk.Frame(page, bd=2, relief="sunken", bg="#ffffff")
        tf.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.tree = ClassicTree(tf, on_select=self._domain_selected)
        self.tree.pack(fill="both", expand=True)

        lf = tk.Frame(page, bd=2, relief="sunken", bg="#ffffff")
        lf.grid(row=1, column=1, sticky="nsew")
        self.list = tk.Listbox(lf, font=("Times New Roman", 11), activestyle="none", exportselection=False,
                               selectbackground="#0078d7", selectforeground="#ffffff", relief="flat",
                               highlightthickness=0, bd=0)
        sb2 = ttk.Scrollbar(lf, orient="vertical", command=self.list.yview)
        self.list.configure(yscrollcommand=sb2.set)
        self.list.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
        sb2.pack(side="right", fill="y")

        sf = tk.Frame(page, bg="#ffffff")
        sf.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        tk.Label(sf, text="Search", bg="#ffffff", font=UI_FONT).pack(side="left")
        self.search = tk.StringVar(value=search)
        self.search_entry = ttk.Entry(sf, textvariable=self.search, font=("Segoe UI", 10))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(14, 0))
        self.desc = tk.Label(page, text="", bg="#ffffff", fg="#606060", font=UI_FONT, anchor="w",
                             justify="left")
        self.desc.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.desc.bind("<Configure>", lambda e: self.desc.configure(wraplength=max(e.width - 10, 100)))
        page.columnconfigure(0, weight=11, uniform="col")
        page.columnconfigure(1, weight=9, uniform="col")
        page.rowconfigure(1, weight=1)

        self.button_bar([("Ok", self.ok), ("Close", self.cancel, "wzclose")])

        self._nodes = {ROOT: library.root}
        self.tree.insert("", ROOT, root_name, open=True)
        for d in library.root.children:
            self._add_domain(ROOT, d)
        self.tree.redraw()
        self.list.bind("<<ListboxSelect>>", self._comp_selected)
        self.list.bind("<Double-Button-1>", lambda e: self.ok())
        self.list.bind("<Return>", lambda e: self.ok())
        self.search.trace_add("write", lambda *a: self._do_search())
        self.search_entry.bind("<Return>", lambda e: self.ok())
        self.search_entry.bind("<Down>", self._focus_list)
        self.bind("<Return>", lambda e: self.ok())

        first = last_domain if last_domain in self._nodes else self._first_domain()
        self.tree.selection_set(first, notify=not search)
        if search:
            self._do_search()
        self.after(60, lambda: (self.search_entry.focus_set(), self.search_entry.icursor("end")))

    def _add_domain(self, parent, dom):
        if not any(d.components for d in dom.walk()):
            return
        self.tree.insert(parent, dom.key, dom.name, open=True)
        self._nodes[dom.key] = dom
        for d in dom.children:
            self._add_domain(dom.key, d)

    def _first_domain(self):
        for d in self.library.root.walk():
            if d.components and d.key in self._nodes:
                return d.key
        return ROOT

    @staticmethod
    def _components(dom):
        """The components of the domain, or of its sub domains when it has none."""
        if dom.components:
            return list(dom.components)
        out = []
        for d in dom.walk():
            out.extend(d.components)
        return out

    def _fill(self, comps):
        self.list.delete(0, "end")
        self.shown = []
        for c in comps:
            self.list.insert("end", c.name)
            if not self.allowed(c):
                self.list.itemconfigure("end", fg="#a0a0a0")
            self.shown.append(c)
        if self.shown:
            self.list.selection_set(0)
            self._comp_selected()
        else:
            self.desc.configure(text="")

    def _domain_selected(self, _iid=None):
        sel = self.tree.selection()
        if not sel:
            return
        if self.search.get().strip():
            self.search.set("")
            return
        self._fill(self._components(self._nodes[sel[0]]))

    def _comp_selected(self, _e=None):
        sel = self.list.curselection()
        if not sel:
            return
        c = self.shown[sel[0]]
        note = "" if self.allowed(c) else "   (You can't use this component in this place)"
        self.desc.configure(text="%s :  %s%s" % (c.name, c.description, note))

    def _do_search(self):
        text = self.search.get()
        if not text.strip():
            sel = self.tree.selection()
            self._fill(self._components(self._nodes[sel[0]]) if sel else [])
            return
        comps = self.library.search(text)
        comps.sort(key=lambda c: not self.allowed(c))
        self._fill(comps)

    def _focus_list(self, _e=None):
        self.list.focus_set()
        return "break"

    def ok(self):
        sel = self.list.curselection()
        if not sel:
            return
        c = self.shown[sel[0]]
        if not self.allowed(c):
            self.bell()
            self.desc.configure(text="Sorry, you can't use the component (%s) in this place" % c.name)
            return
        self.result = c
        self.destroy()
