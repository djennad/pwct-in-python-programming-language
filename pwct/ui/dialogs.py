"""Small windows: Goal Viewer (source code), Steps Colors, VPL Compiler,
About, Welcome and Samples Manager."""

import os
import shutil
import subprocess
import tempfile
import time
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog

from .. import APP_NAME, VERSION, codegen
from ..languages import error_lines
from ..rules import TYPE_NAMES
from ..settings import STYLES
from .common import Dialog, ScrolledText, highlight_python, image, UI_BOLD, UI_FONT, center


class CodeViewer(Dialog):
    """Goal Viewer Window - the generated Python source code."""

    def __init__(self, app):
        super().__init__(app.root, "Goal Viewer Window - Source Code", size=(900, 620))
        self.app = app
        top = tk.Frame(self.body, bg="#ffffff")
        top.pack(fill="x", padx=8, pady=(6, 0))
        self.info = tk.Label(top, text="", bg="#ffffff", font=UI_FONT, anchor="w")
        self.info.pack(side="left")
        self.view = ScrolledText(self.body, font=("Consolas", 11), bg="#ffffff")
        self.view.pack(fill="both", expand=True, padx=8, pady=6)
        self.button_bar([("Run", self.run), ("Save As...", self.save_as), ("Copy", self.copy_all),
                         ("Refresh", self.refresh), ("Close", self.cancel)])
        self.refresh()

    def refresh(self):
        lang = self.app.language
        files = {}
        code, _ = codegen.generate(self.app.project, files=files, lang=lang)
        self.code = code
        self.view.set(codegen.with_files(code, files), readonly=True)
        highlight_python(self.view.text, lang)
        n = code.count("\n")
        self.info.configure(text="%s source code generated from the steps tree  (%s)  -  %d lines"
                                 % (lang.title, lang.name, n))

    def run(self):
        self.app.run_program()

    def copy_all(self):
        self.clipboard_clear()
        self.clipboard_append(self.code)
        self.app.status("Source code copied to the clipboard")

    def save_as(self):
        init = self.app.output_path()
        ext = self.app.language.extension
        f = filedialog.asksaveasfilename(parent=self, defaultextension=ext, initialfile=os.path.basename(init),
                                         initialdir=os.path.dirname(init),
                                         filetypes=[("%s source" % self.app.language.title, "*" + ext),
                                                    ("All files", "*.*")])
        if f:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(self.code)
            self.app.status("Source code saved : " + f)


class StepsColorsDialog(Dialog):
    """Set steps colors (stepscolors.scx)."""

    def __init__(self, app):
        super().__init__(app.root, "Set steps colors", size=(640, 430), resizable=False)
        self.app = app
        self.colors = dict(app.settings.colors)
        g = tk.Frame(self.body, bg="#ffffff")
        g.pack(side="left", fill="both", expand=True, padx=12, pady=8)
        for col, text in enumerate(("Step Type", "Font Color", "Back Color", "", "Preview")):
            tk.Label(g, text=text, bg="#ffffff", font=UI_BOLD).grid(row=0, column=col, padx=6, pady=4, sticky="w")
        self.swatches = {}
        self.previews = {}
        for r, t in enumerate(sorted(TYPE_NAMES), start=1):
            tk.Label(g, text=TYPE_NAMES[t], bg="#ffffff", font=UI_FONT).grid(row=r, column=0, sticky="w", padx=6)
            for c, idx in ((1, 0), (2, 1)):
                sw = tk.Label(g, width=6, height=2, relief="solid", bd=1, cursor="hand2")
                sw.grid(row=r, column=c, padx=6, pady=4)
                sw.bind("<Button-1>", lambda e, tt=t, i=idx: self.pick(tt, i))
                self.swatches[(t, idx)] = sw
            ttk.Button(g, text="Hide", width=6, command=lambda tt=t: self.hide(tt)).grid(row=r, column=3, padx=4)
            pv = tk.Label(g, text="  Step  ", font=("Arial", 11))
            pv.grid(row=r, column=4, padx=6)
            self.previews[t] = pv
        side = tk.Frame(self.body, bg="#ffffff")
        side.pack(side="right", fill="y", padx=12, pady=8)
        tk.Label(side, text="Styles", bg="#ffffff", font=UI_BOLD).pack(anchor="w")
        self.styles = tk.Listbox(side, height=8, width=22, exportselection=False, font=UI_FONT)
        for name in STYLES:
            self.styles.insert("end", name)
        self.styles.pack(fill="y", expand=True)
        self.styles.bind("<<ListboxSelect>>", self.select_style)
        self.button_bar([("Apply", self.apply), ("Cancel", self.cancel)])
        self.update_swatches()

    def update_swatches(self):
        for (t, idx), sw in self.swatches.items():
            sw.configure(bg=self.colors[t][idx])
        for t, pv in self.previews.items():
            fg, bg = self.colors[t]
            pv.configure(fg=fg, bg=bg, text="  Step  " if fg.lower() != bg.lower() else "  (Hidden)  ")

    def pick(self, t, idx):
        c = colorchooser.askcolor(self.colors[t][idx], parent=self)[1]
        if c:
            pair = list(self.colors[t])
            pair[idx] = c
            self.colors[t] = tuple(pair)
            self.update_swatches()

    def hide(self, t):
        self.colors[t] = ("#ffffff", "#ffffff")
        self.update_swatches()

    def select_style(self, _e=None):
        sel = self.styles.curselection()
        if sel:
            self.colors = dict(STYLES[self.styles.get(sel[0])])
            self.update_swatches()

    def apply(self):
        self.app.settings.colors = dict(self.colors)
        self.app.settings.save()
        self.app.gd.apply_style()
        self.app.gd.refresh()
        self.destroy()


class VPLCompilerDialog(Dialog):
    """VPL Compiler (frmvplcompiler.scx): check the visual source for errors."""

    def __init__(self, app):
        super().__init__(app.root, "VPL Compiler", size=(760, 520))
        self.app = app
        tk.Label(self.body, text="Log :", bg="#ffffff", font=UI_BOLD).pack(anchor="w", padx=10, pady=(6, 0))
        self.log = ScrolledText(self.body, height=8, font=("Consolas", 10), bg="#fbfbfb")
        self.log.pack(fill="x", padx=10)
        tk.Label(self.body, text="Errors :  (double click to go to the step)", bg="#ffffff",
                 font=UI_BOLD).pack(anchor="w", padx=10, pady=(6, 0))
        self.errors = tk.Listbox(self.body, font=("Consolas", 10), fg="#b00000", activestyle="none")
        self.errors.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.errors.bind("<Double-Button-1>", self.goto)
        self.error_steps = []
        self.button_bar([("Compile", self.compile), ("Close", self.cancel)])
        self.after(100, self.compile)

    def add_log(self, text):
        self.log.text.configure(state="normal")
        self.log.text.insert("end", text + "\n")
        self.log.text.see("end")
        self.log.text.configure(state="disabled")

    def add_error(self, text, step=None):
        self.errors.insert("end", " " + text)
        self.error_steps.append(step)

    def compile(self):
        p = self.app.project
        self.log.set("", readonly=True)
        self.errors.delete(0, "end")
        self.error_steps = []
        t0 = time.time()
        self.add_log(" Compiling...")
        steps = [s for g in p.goals for s in g.root.walk() if s.parent is not None]
        self.add_log(" Goals : %d   Steps : %d   Interactions : %d" % (len(p.goals), len(steps), len(p.interactions)))
        # 1 - interactions: component found, same Enable/Ignore status, steps order
        for it in p.interactions:
            its = p.interaction_steps(it.id)
            if not its:
                continue
            if self.app.library.get(it.component) is None:
                self.add_error("Error : Component ( %s ) is not found" % it.component, its[0])
            if len({s.disabled for s in its}) > 1:
                for s in its:
                    self.add_error("Error : Step ( %s ) Enable/Ignore status is not correct" % s.name, s)
            last = 0
            for s in its:
                if s.internum < last:
                    self.add_error("Error : Step ( %s ) is not expected to be in this order" % s.name, s)
                last = s.internum
        # 2 - the generated code
        lang = self.app.language
        self.add_log(" Visual Programming Language : %s (%s)" % (lang.name, lang.title))
        files = {}
        code, linemap = codegen.generate(p, files=files, lang=lang)
        if files:
            self.add_log(" Files (<pwct:tofile>) : " + ", ".join(files))
        if lang.is_python:
            err = codegen.check_syntax(code, linemap, files, lang)
            if err is None:
                self.add_log(" Python syntax check : OK")
            else:
                msg, line, step, fname = err
                where = ("Step ( %s )" % step.name) if step else "line %s" % line
                if fname != "<generated>":
                    where += " in file %s" % fname
                self.add_error("Syntax Error : %s - %s" % (msg, where), step)
                self.add_log(" Python syntax check : Error at line %s" % line)
        else:
            self.compiler_check(lang, code, linemap, files)
        n = self.errors.size()
        self.add_log(" Errors : %d" % n)
        self.add_log(" Processing time : %.3f seconds" % (time.time() - t0))
        if n == 0:
            self.errors.insert("end", " No errors - the visual source is ready to run (Ctrl+R)")
            self.errors.itemconfigure(0, fg="#006000")
            self.error_steps.append(None)

    def compiler_check(self, lang, code, linemap, files):
        """Compile with the compiler of the language (in a temporary folder) and map the errors to steps."""
        tmp = tempfile.mkdtemp(prefix="pypwct_")
        try:
            name = os.path.splitext(os.path.basename(self.app.output_path()))[0]
            src = os.path.join(tmp, name + lang.extension)
            codegen.write_files(src, code, files)
            values = lang.placeholders(src, tmp)
            cmd = lang.command(lang.check, values) if lang.check else None
            if cmd is None and lang.build:
                cmd = lang.command(lang.build, dict(values, exe=os.path.join(tmp, "check.exe")))
            if cmd is None:
                self.add_log(" Compiler not found (%s) - only the steps were checked"
                             % (", ".join(lang.missing_tools(lang.check or lang.build)) or "no command"))
                return
            self.add_log(" Compiler : " + " ".join(os.path.basename(c) if k == 0 else c for k, c in enumerate(cmd)))
            self.config(cursor="watch")
            self.update()
            try:
                r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=120,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except (OSError, subprocess.TimeoutExpired) as ex:
                self.add_log(" Compiler error : %s" % ex)
                return
            finally:
                self.config(cursor="")
            output = (r.stdout + r.stderr).strip()
            found = error_lines(output, src)
            for line, text in found:
                if "warning" in text.lower():
                    continue
                step = linemap[line - 1] if 0 < line <= len(linemap) else None
                where = ("Step ( %s )" % step.name) if step else "line %d" % line
                msg = text.split("error", 1)[-1].strip(" :") if "error" in text.lower() else text
                self.add_error("Error : %s - %s" % (msg[:150], where), step)
            if r.returncode != 0 and not any("warning" not in t.lower() for _, t in found):
                for ln in output.splitlines()[:8]:
                    self.add_error(ln[:180])
            self.add_log(" %s compiler : %s" % (lang.title, "OK" if r.returncode == 0 else "Errors"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def goto(self, _e=None):
        sel = self.errors.curselection()
        if sel and self.error_steps[sel[0]] is not None:
            self.app.gd.goto_step(self.error_steps[sel[0]].id)


class AboutDialog(Dialog):
    def __init__(self, app):
        super().__init__(app.root, "About", size=(560, 470), resizable=False)
        img = image("splash")
        if img:
            tk.Label(self.body, image=img, bg="#ffffff").pack(pady=(4, 0))
        langs = ", ".join(x.title for x in app.languages.items)
        text = ("%s - PyPWCT %s\n"
                "A Python/Tkinter re-implementation of PWCT 1.9 (Art)\n"
                "Visual Programming Languages : %s\n"
                "PWCT : Copyright 2006-2025, Mahmoud Samir Fayed (GPL)" % (APP_NAME, VERSION, langs))
        tk.Label(self.body, text=text, bg="#ffffff", font=UI_FONT, justify="center").pack(pady=6)
        self.button_bar([("Ok", self.cancel)])


class Welcome(tk.Toplevel):
    """Splash window (welcome.scx)."""

    def __init__(self, root, on_close):
        super().__init__(root)
        self.overrideredirect(True)
        self.configure(bg="#ffffff", bd=1, relief="solid")
        img = image("splash")
        c = tk.Canvas(self, width=556, height=360, highlightthickness=0, bg="#ffffff")
        c.pack()
        if img:
            c.create_image(0, 0, image=img, anchor="nw")
        c.create_text(16, 298, text="PyPWCT %s   -   Based on PWCT 1.9 (Art) by Mahmoud Samir Fayed" % VERSION,
                      anchor="w", font=("Segoe UI", 9, "bold"), fill="#ffffff")
        center(self, None, 558, 362)
        self.lift()
        self.attributes("-topmost", True)
        self.on_close = on_close
        c.bind("<Button-1>", lambda e: self.close())
        self.after(2200, self.close)

    def close(self):
        if self.winfo_exists():
            self.destroy()
            self.on_close()


class SamplesDialog(Dialog):
    """Samples Manager."""

    def __init__(self, app, folder):
        super().__init__(app.root, "Samples Manager", size=(560, 420))
        self.app = app
        self.folder = folder
        tk.Label(self.body, text="Samples :", bg="#ffffff", font=UI_BOLD).pack(anchor="w", padx=10, pady=(8, 0))
        self.list = tk.Listbox(self.body, font=("Segoe UI", 10), activestyle="none")
        self.list.pack(fill="both", expand=True, padx=10, pady=6)
        self.files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pwct")) if os.path.isdir(folder) else []
        for f in self.files:
            self.list.insert("end", "  " + os.path.splitext(f)[0].replace("_", " "))
        self.list.bind("<Double-Button-1>", lambda e: self.open())
        self.button_bar([("Open", self.open), ("Close", self.cancel)])

    def open(self):
        sel = self.list.curselection()
        if sel:
            path = os.path.join(self.folder, self.files[sel[0]])
            self.destroy()
            self.app.open_file(path, sample=True)
