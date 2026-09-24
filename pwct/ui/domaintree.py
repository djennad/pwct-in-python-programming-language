"""Domain Tree (dtree.scx) + Install / Uninstall Component."""

import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ..components import Component
from .common import Dialog, ask_string, image, UI_BOLD, UI_FONT


class DomainTreeDialog(Dialog):
    def __init__(self, app):
        super().__init__(app.root, "Domain Tree", size=(820, 520))
        self.app = app
        main = tk.Frame(self.body, bg="#ffffff")
        main.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(main, text="Domain Tree", bg="#ffffff", font=UI_BOLD).grid(row=0, column=0, sticky="w")
        tk.Label(main, text="Components in Domain", bg="#ffffff", font=UI_BOLD).grid(row=0, column=1, sticky="w")
        self.tree = ttk.Treeview(main, show="tree", selectmode="browse")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.list = tk.Listbox(main, font=("Segoe UI", 10), activestyle="none", exportselection=False)
        self.list.grid(row=1, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)
        self.info = tk.Label(main, text="", bg="#ffffff", fg="#404040", font=UI_FONT, anchor="w")
        self.info.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        btns = tk.Frame(main, bg="#ffffff")
        btns.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        for text, cmd in (("New Root", lambda: self.new_domain(True)), ("New Child", lambda: self.new_domain(False)),
                          ("Rename", self.rename_domain), ("Delete", self.delete_domain)):
            ttk.Button(btns, text=text, command=cmd).pack(side="left", padx=2)
        ttk.Separator(btns, orient="vertical").pack(side="left", fill="y", padx=8)
        for text, cmd in (("New Component", self.new_component), ("Edit Component", self.edit_component),
                          ("Install Component", self.install), ("Uninstall Component", self.uninstall)):
            ttk.Button(btns, text=text, command=cmd).pack(side="left", padx=2)
        self.button_bar([("Close", self.cancel)])
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.fill())
        self.list.bind("<<ListboxSelect>>", lambda e: self.show_info())
        self.list.bind("<Double-Button-1>", lambda e: self.edit_component())
        self.reload()

    def reload(self, select=None):
        self.app.reload_components()
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.doms = {}
        img = image("open") or ""

        def add(parent, d):
            self.doms[d.key] = d
            self.tree.insert(parent, "end", iid=d.key, text="  %s" % d.name, image=img, open=True)
            for c in d.children:
                add(d.key, c)
        for d in self.app.library.root.children:
            add("", d)
        if select and self.tree.exists(select):
            self.tree.selection_set(select)
        elif self.tree.get_children():
            self.tree.selection_set(self.tree.get_children()[0])
        self.fill()

    def domain(self):
        sel = self.tree.selection()
        return self.doms.get(sel[0]) if sel else None

    def fill(self):
        self.list.delete(0, "end")
        d = self.domain()
        self.comps = d.components if d else []
        for c in self.comps:
            self.list.insert("end", "  " + c.name)
        self.info.configure(text=("components/" + d.key) if d else "")

    def component(self):
        sel = self.list.curselection()
        return self.comps[sel[0]] if sel else None

    def show_info(self):
        c = self.component()
        if c:
            self.info.configure(text="%s  -  %s" % (os.path.basename(c.path), c.description))

    def new_domain(self, root):
        d = self.domain()
        if not root and d is None:
            messagebox.showinfo("Sorry", "Please select Domain First !", parent=self)
            return
        name = ask_string(self, "New Root" if root else "New Child", "Domain Name :")
        if not name:
            return
        base = self.app.library.root_dir if root else d.path
        path = os.path.join(base, name)
        try:
            os.makedirs(path)
        except OSError as ex:
            messagebox.showerror("Sorry", str(ex), parent=self)
            return
        key = name if root else d.key + "/" + name
        self.reload(select=key)

    def rename_domain(self):
        d = self.domain()
        if d is None:
            return
        name = ask_string(self, "Edit", "Name :", d.name)
        if not name or name == d.name:
            return
        new = os.path.join(os.path.dirname(d.path), name)
        try:
            os.rename(d.path, new)
        except OSError as ex:
            messagebox.showerror("Sorry", str(ex), parent=self)
            return
        self.reload(select=(d.key.rsplit("/", 1)[0] + "/" + name) if "/" in d.key else name)

    def delete_domain(self):
        d = self.domain()
        if d is None:
            return
        if any(x.components for x in d.walk()):
            messagebox.showinfo("Sorry", "The domain contains components, uninstall them first", parent=self)
            return
        if messagebox.askyesno("Delete", "Delete the domain (%s) ?" % d.name, parent=self):
            shutil.rmtree(d.path, ignore_errors=True)
            self.reload()

    def new_component(self):
        d = self.domain()
        self.app.component_designer(domain=d.key if d else "")

    def edit_component(self):
        c = self.component()
        if c:
            self.app.component_designer(c)

    def install(self):
        d = self.domain()
        if d is None:
            messagebox.showinfo("Sorry", "You should select the domain", parent=self)
            return
        f = filedialog.askopenfilename(parent=self, title="Install Component",
                                       filetypes=[("PyPWCT Component", "*.json")])
        if not f:
            return
        try:
            Component.load(f)
        except (OSError, ValueError) as ex:
            messagebox.showerror("Error", "The File is not valid - Process Canceled\n%s" % ex, parent=self)
            return
        dest = os.path.join(d.path, os.path.basename(f))
        if os.path.exists(dest) and not messagebox.askyesno(
                "Alert", "Are you sure that you want reinstalling this Component", parent=self):
            return
        shutil.copyfile(f, dest)
        self.reload(select=d.key)
        messagebox.showinfo("Great", "Component installed", parent=self)

    def uninstall(self):
        c = self.component()
        if c is None:
            messagebox.showinfo("Sorry", "Please select Component", parent=self)
            return
        if messagebox.askyesno("Alert", "Are you sure that you want uninstalling this Component\n\n%s" % c.name,
                               parent=self):
            os.remove(c.path)
            self.reload(select=c.domain)
