"""Programming Languages List (langlist form of PWCT + the VPLS files).

Add / edit the Visual Programming Languages: extension, comment, indentation,
prelude and the build / run / check commands.  A new language gets a
components folder with two starter components (Comment and Code); then its
components are made with the Component Designer (Interaction + Transporter).
"""

import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox

from .common import Dialog, UI_BOLD, UI_FONT

HELP = ("Commands : one alternative per line (the first one found is used).  Variables :  {file} the generated "
        "source   {exe} the executable   {dir} the folder   {name} the file name   {python} Python   "
        "{tmpdir} temporary folder (check)")


def starter_components(lang):
    """Comment + Code components for a new language."""
    base = os.path.join(lang.components_dir, "General")
    os.makedirs(base, exist_ok=True)
    with open(os.path.join(lang.components_dir, "_order.txt"), "w", encoding="utf-8") as f:
        f.write("General\n")

    def page(title, field):
        return [{"name": title, "bgcolor": "#ffffff", "width": 620, "height": 120, "controls": [
            {"type": "label", "x": 0, "y": 0, "w": 620, "h": 44, "caption": "  " + title, "fg": "#ffffff",
             "bg": "#404040", "font": ["Arial", 14, "bold"]},
            {"type": "label", "x": 20, "y": 67, "w": 190, "h": 22, "caption": field + " :", "fg": "#000000",
             "bg": "", "font": ["Arial", 10, "bold"]},
            {"type": "textbox", "var": "text", "title": field, "text": "", "kind": "any", "focus": True,
             "x": 215, "y": 64, "w": 380, "h": 26, "fg": "#000080", "bg": "#ffffff", "font": ["Consolas", 11]}]}]
    comps = {
        "Comment": {"name": "Comment", "description": "Add a comment line.", "order": 0,
                    "pages": page("Comment", "Comment"),
                    "mask": "<RPWI:NEWSTEP> Comment : #{text}\n%s #{text}" % lang.comment,
                    "rules": {"allow_root": [1], "allow_interaction": []}},
        "Code": {"name": lang.title + " Code", "description": "Write one line of code directly.", "order": 1,
                 "pages": page(lang.title + " Code", "Code"),
                 "mask": "<RPWI:NEWSTEP> %s Code : #{text}\n#{text}" % lang.title,
                 "rules": {"allow_root": [1], "allow_interaction": []}},
    }
    for fname, data in comps.items():
        path = os.path.join(base, fname + ".json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)


class LanguagesDialog(Dialog):
    def __init__(self, app):
        super().__init__(app.root, "Programming Languages List", size=(980, 640))
        self.app = app
        self.current = None
        main = tk.Frame(self.body, bg="#ffffff")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left = tk.Frame(main, bg="#ffffff")
        left.pack(side="left", fill="y")
        tk.Label(left, text="Visual Programming Languages", bg="#ffffff", font=UI_BOLD).pack(anchor="w")
        self.list = tk.Listbox(left, width=26, font=("Segoe UI", 10), exportselection=False, activestyle="none")
        self.list.pack(fill="y", expand=True)
        self.list.bind("<<ListboxSelect>>", lambda e: self.select())
        for text, cmd in (("New Language", self.new), ("Delete", self.delete), ("Open Folder", self.open_folder)):
            ttk.Button(left, text=text, command=cmd).pack(fill="x", pady=1)

        form = tk.Frame(main, bg="#ffffff")
        form.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self.vars = {}
        row = 0
        for key, label in (("name", "VPL Name"), ("title", "Language"), ("extension", "File Extension"),
                           ("comment", "Comment"), ("indent", "Indentation (spaces)"),
                           ("empty_block", "Empty block filler"), ("keywords", "Keywords"),
                           ("description", "Description")):
            tk.Label(form, text=label + " :", bg="#ffffff", font=UI_FONT).grid(row=row, column=0, sticky="w", pady=1)
            v = tk.StringVar()
            ttk.Entry(form, textvariable=v).grid(row=row, column=1, sticky="ew", pady=1)
            self.vars[key] = v
            row += 1
        self.texts = {}
        for key, label, h in (("prelude", "Prelude (code at the start)", 4), ("build", "Build commands", 3),
                              ("run", "Run commands", 2), ("check", "Check commands (VPL Compiler)", 2)):
            tk.Label(form, text=label + " :", bg="#ffffff", font=UI_FONT).grid(row=row, column=0, sticky="nw", pady=1)
            t = tk.Text(form, height=h, font=("Consolas", 9), wrap="none")
            t.grid(row=row, column=1, sticky="ew", pady=1)
            self.texts[key] = t
            row += 1
        tk.Label(form, text=HELP, bg="#ffffff", fg="#505050", font=UI_FONT, wraplength=640,
                 justify="left").grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 0))
        row += 1
        self.status = tk.Label(form, text="", bg="#ffffff", fg="#006000", font=UI_BOLD, anchor="w")
        self.status.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        form.columnconfigure(1, weight=1)
        self.button_bar([("Save", self.save), ("Activate", self.use), ("Close", self.cancel)])
        self.fill()

    def fill(self, select=None):
        self.app.languages.reload()
        self.items = list(self.app.languages.items)
        self.list.delete(0, "end")
        for lang in self.items:
            mark = "  (active)" if lang.id == self.app.language.id else ""
            self.list.insert("end", "  %s%s" % (lang.name, mark))
        idx = 0
        for k, lang in enumerate(self.items):
            if lang.id == (select or self.app.language.id):
                idx = k
        if self.items:
            self.list.selection_set(idx)
            self.select()

    def select(self):
        sel = self.list.curselection()
        if not sel:
            return
        lang = self.items[sel[0]]
        self.current = lang
        for key, v in self.vars.items():
            val = getattr(lang, key)
            v.set(str(len(val)) if key == "indent" else val)
        for key, t in self.texts.items():
            val = getattr(lang, key)
            t.delete("1.0", "end")
            t.insert("1.0", val if isinstance(val, str) else "\n".join(val))
        ok = []
        for what in ("build", "run"):
            alts = getattr(lang, what)
            if alts:
                found = lang.command(alts, lang.placeholders(os.path.join(lang.path, "x" + lang.extension)))
                ok.append("%s : %s" % (what.title(), "found (%s)" % os.path.basename(found[0]) if found
                                       else "NOT FOUND (%s)" % ", ".join(lang.missing_tools(alts))))
        n = sum(1 for _, _, fs in os.walk(lang.components_dir) for f in fs if f.endswith(".json"))
        self.status.configure(text="%d components   %s" % (n, "   ".join(ok)),
                              fg="#006000" if "NOT" not in " ".join(ok) else "#b00000")

    def collect(self, lang):
        for key, v in self.vars.items():
            val = v.get()
            if key == "indent":
                try:
                    val = " " * max(0, int(val))
                except ValueError:
                    val = "    "
            setattr(lang, key, val)
        for key, t in self.texts.items():
            txt = t.get("1.0", "end-1c")
            setattr(lang, key, txt.rstrip("\n") if key == "prelude"
                    else [ln.strip() for ln in txt.splitlines() if ln.strip()])
        if not lang.extension.startswith("."):
            lang.extension = "." + lang.extension

    def save(self):
        if self.current is None:
            return
        self.collect(self.current)
        self.current.save()
        self.fill(self.current.id)
        if self.current.id == self.app.language.id:
            self.app.set_language(self.app.languages.get(self.current.id))
            self.app.gd.refresh()
        self.status.configure(text="Saved : " + self.current.name, fg="#006000")

    def use(self):
        if self.current is not None:
            self.save()
            self.app.change_language(self.current.name)
            self.fill(self.current.id)

    def new(self):
        from .common import ask_string
        title = ask_string(self, "New Language", "Programming Language (example : Ruby) :")
        if not title:
            return
        lid = re.sub(r"[^A-Za-z0-9_]", "", title.replace("#", "Sharp").replace("+", "Plus")) or "Language"
        if self.app.languages.get(lid):
            messagebox.showinfo("Sorry", "The language already exists : " + lid, parent=self)
            return
        data = {"name": title + "PWCT", "title": title, "extension": "." + lid.lower(), "comment": "//",
                "indent": "    ", "empty_block": "", "prelude": "", "build": [],
                "run": ['%s "{file}"' % lid.lower()], "check": [], "keywords": "", "syntax": "",
                "description": title, "start": ""}
        lang = self.app.languages.create(lid, data)
        order = os.path.join(self.app.languages.root, "_order.txt")
        try:
            with open(order, "a", encoding="utf-8") as f:
                f.write(lid + "\n")
        except OSError:
            pass
        starter_components(lang)
        self.fill(lid)
        self.status.configure(text="New language created : %s - set its commands, then make its components with the "
                                   "Component Designer" % lang.name, fg="#006000")

    def delete(self):
        lang = self.current
        if lang is None:
            return
        if lang.id == self.app.language.id:
            messagebox.showinfo("Sorry", "You can't delete the active language", parent=self)
            return
        n = sum(1 for _, _, fs in os.walk(lang.components_dir) for f in fs if f.endswith(".json"))
        if n > 2:
            messagebox.showinfo("Sorry", "The language contains %d components.\nDelete its folder manually if you "
                                         "don't need it :\n%s" % (n, lang.path), parent=self)
            return
        if not messagebox.askyesno("Delete", "Delete the language %s ?" % lang.name, parent=self):
            return
        import shutil
        shutil.rmtree(lang.path, ignore_errors=True)
        self.fill()

    def open_folder(self):
        if self.current is not None and hasattr(os, "startfile"):
            os.startfile(self.current.path)
