"""Main window (DoubleS.scx + sysmenu.prg + mytool.vcx): menu, Standard tool bar,
status bar and the Goal Designer."""

import json
import os
import re
import subprocess
import sys
import tkinter as tk
import webbrowser
from tkinter import ttk, filedialog, messagebox

from .. import APP_NAME, FILE_EXT, codegen
from ..components import Library
from ..engine import Generator
from ..forms import FormModel
from ..languages import Languages, python_exe
from ..model import Project
from ..rules import Rules
from ..settings import Settings, config_dir
from .common import Gradient, ask_string, icon_button, image, UI_FONT, UI_BOLD
from .dialogs import (AboutDialog, CodeViewer, SamplesDialog, StepsColorsDialog, VPLCompilerDialog, Welcome)
from .domaintree import DomainTreeDialog
from .goaldesigner import GoalDesigner

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGUAGES_DIR = os.path.join(BASE_DIR, "languages")
FILETYPES = [("PyPWCT Visual Source", "*" + FILE_EXT), ("All files", "*.*")]


class App:
    def __init__(self, root, filename=None):
        self.root = root
        self.settings = Settings()
        self.languages = Languages(LANGUAGES_DIR)
        self.language = self.languages.get(self.settings.language) or self.languages.default()
        if self.language is None:
            raise SystemExit("No Visual Programming Language in " + LANGUAGES_DIR)
        self.library = Library(self.language.components_dir)
        self.project = Project(self.language.id)
        self.rules = Rules(self.project, self.library, self.settings.syntax_directed)
        self.generator = Generator(self.project, self.library, self.language)
        self.run_dir = os.path.join(config_dir(), "run")

        root.title(APP_NAME)
        ic = image("app_icon")
        if ic:
            root.iconphoto(True, ic)
        root.configure(bg="#ffffff")
        root.minsize(900, 600)
        self._style()
        self._menu()
        self._toolbar()
        self._statusbar()
        self.gd = GoalDesigner(root, self)
        self.gd.pack(fill="both", expand=True)
        self.set_project(self.start_project())
        self.update_language_ui()
        self._keys()
        root.protocol("WM_DELETE_WINDOW", self.exit)
        if self.library.errors:
            self.status("Components with errors : " + "; ".join(self.library.errors))
        else:
            self.status("Start PWCT Environment  -  %s  -  %d components in the Domain Tree"
                        % (self.language.name, len(self.library.all())))
        if filename:
            root.after(100, lambda: self.open_file(filename))
        if self.settings.show_welcome:
            root.after(50, lambda: Welcome(root, lambda: self.gd.tree.focus_set()))
        else:
            root.after(100, self.gd.tree.focus_set)

    # ============================================================== UI
    def _style(self):
        st = ttk.Style(self.root)
        if "vista" in st.theme_names():
            st.theme_use("vista")
        st.configure("TButton", font=UI_FONT)

    def _menu(self):
        m = tk.Menu(self.root)
        self.root.config(menu=m)

        def menu(label, items):
            sub = tk.Menu(m, tearoff=False)
            for it in items:
                if it is None:
                    sub.add_separator()
                elif isinstance(it[1], tk.Menu):
                    sub.add_cascade(label=it[0], menu=it[1])
                else:
                    sub.add_command(label=it[0], command=it[1], accelerator=it[2] if len(it) > 2 else "")
            m.add_cascade(label=label, menu=sub)
            return sub

        self.recent_menu = tk.Menu(m, tearoff=False, postcommand=self._fill_recent)
        menu("File", [("New", self.new_file), ("Open...", self.open_dialog, "Ctrl+O"),
                      ("Close", self.close_file, "Ctrl+W"), None,
                      ("Save", self.save, "Ctrl+S"), ("Save As...", self.save_as), None,
                      ("Recent Files", self.recent_menu), None, ("Exit", self.exit, "Alt+F4")])
        menu("Edit", [("Cut", self.gd_call("cut"), "Ctrl+X"), ("Copy", self.gd_call("copy"), "Ctrl+C"),
                      ("Paste", self.gd_call("paste"), "Ctrl+V"), None,
                      ("Search", self.gd_call("search"), "Ctrl+Shift+F")])
        menu("Goal", [("RPWI - Goal Designer", lambda: self.gd.tree.focus_set()),
                      ("Goal Viewer Window (Source Code)", self.show_code, "F5"),
                      ("Form Designer", self.gd_call("form_designer"), "Ctrl+F"), None,
                      ("New Goal", self.new_goal), ("Edit Goal", self.edit_goal), ("Delete Goal", self.delete_goal),
                      None, ("Run", self.run_program, "Ctrl+R"),
                      ("Generate Source Code", self.generate_file, "Ctrl+G"),
                      ("VPL Compiler", self.vpl_compiler, "F7"), None,
                      ("Steps Colors", self.steps_colors)])
        menu("Domain Tree", [("Domain Tree", self.domain_tree), ("Install Component", self.domain_tree),
                             ("Reload Components", self.reload_components)])
        self.vpl_menu = tk.Menu(m, tearoff=False, postcommand=self._fill_vpl_menu)
        menu("Transporter", [("Programming Languages List", self.languages_list),
                             ("Visual Programming Language", self.vpl_menu), None,
                             ("Interaction Designer", lambda: self.component_designer(tab=0)),
                             ("Transporter Designer", lambda: self.component_designer(tab=1)), None,
                             ("Edit Selected Step Component", self.edit_step_component)])
        menu("Tools", [("Calculator", lambda: self.tool("calc")), ("NotePad", lambda: self.tool("notepad")),
                       ("Paint", lambda: self.tool("mspaint")), None,
                       ("Python Shell (IDLE)", self.idle),
                       ("Open the folder of the generated files", self.open_output_folder)])
        menu("Help", [("PWCT on the Web", lambda: webbrowser.open("https://doublesvsoop.sourceforge.net/")),
                      None, ("Samples Manager", self.samples), None,
                      ("Show Welcome Window at startup", self.toggle_welcome), None, ("About", self.about)])

    def gd_call(self, name):
        return lambda: getattr(self.gd, name)()

    def _toolbar(self):
        tb = Gradient(self.root, height=40)
        tb.pack(fill="x")
        x = 6
        for img, tip, cmd in (("new", "New Visual Source File", self.new_file),
                              ("open", "Open (Ctrl+O)", self.open_dialog),
                              ("save", "Save (Ctrl+S)", self.save),
                              ("help", "Help - Samples Manager", self.samples)):
            b = icon_button(tb, img, tip, cmd, width=28, height=26)
            tb.create_window(x, 20, window=b, anchor="w")
            x += 32
        run = icon_button(tb, None, "Run the program (Ctrl+R)", self.run_program, text="!", width=3,
                          height=1, fg="#c00000")
        run.configure(font=("Arial", 13, "bold"))
        tb.create_window(x + 4, 20, window=run, anchor="w")
        x += 44
        b = icon_button(tb, "wzclose", "Close (Ctrl+W)", self.close_file, width=28, height=26)
        tb.create_window(x, 20, window=b, anchor="w")
        x += 44
        tb.create_line(x, 6, x, 34, fill="#a0a0a0")
        tb.create_text(x + 10, 20, text="Visual Programming Language", anchor="w", font=UI_BOLD)
        self.vpl_combo = ttk.Combobox(tb, state="readonly", width=16)
        self.vpl_combo.bind("<<ComboboxSelected>>", lambda e: self.change_language(self.vpl_combo.get()))
        tb.create_window(x + 200, 20, window=self.vpl_combo, anchor="w")
        b = icon_button(tb, "btn_code", "Generate source code (Goal Viewer Window)", self.show_code,
                        text=" Source Code", padx=4)
        tb.create_window(x + 344, 20, window=b, anchor="w")
        b = icon_button(tb, None, "Check the visual source (VPL Compiler)", self.vpl_compiler, text="VPL Compiler",
                        padx=6)
        tb.create_window(x + 464, 20, window=b, anchor="w")
        tb.create_text(0, 20, text="", anchor="e", font=UI_FONT, fill="#404040", tags="langinfo")
        tb.bind("<Configure>", lambda e: tb.coords("langinfo", e.width - 6, 20), add="+")
        self.toolbar = tb
        tk.Frame(self.root, height=1, bg="#909090").pack(fill="x")

    def _statusbar(self):
        sb = Gradient(self.root, height=24)
        sb.pack(fill="x", side="bottom")
        self.status_id = sb.create_text(8, 12, text="", anchor="w", font=UI_FONT)
        self.file_id = sb.create_text(0, 12, text="", anchor="e", font=UI_FONT, tags="file")
        sb.bind("<Configure>", lambda e: sb.coords("file", e.width - 8, 12), add="+")
        self.statusbar = sb

    def _keys(self):
        r = self.root

        def main_only(fn):
            # shortcuts of the main window only (not inside the other windows)
            def handler(e):
                try:
                    if e.widget.winfo_toplevel() is not r:
                        return None
                except (AttributeError, KeyError, tk.TclError):
                    return None
                fn()
                return "break"
            return handler
        for key, fn in (("<Control-o>", self.open_dialog), ("<Control-s>", self.save),
                        ("<Control-w>", self.close_file), ("<Control-r>", self.run_program),
                        ("<Control-g>", self.generate_file), ("<F5>", self.show_code),
                        ("<F7>", self.vpl_compiler), ("<Control-f>", self.gd_call("form_designer")),
                        ("<Control-F>", self.gd_call("search")), ("<F3>", self.gd_call("search"))):
            r.bind(key, main_only(fn))

    def status(self, msg):
        self.statusbar.itemconfigure(self.status_id, text=msg)

    def update_title(self):
        p = self.project
        name = os.path.basename(p.filename) if p.filename else "(NO NAME)"
        self.root.title("%s - [%s%s]" % (APP_NAME, name, " *" if p.modified else ""))
        self.statusbar.itemconfigure(self.file_id, text="File : " + (os.path.basename(p.filename) if p.filename
                                                                      else "(NO NAME)"))

    # ========================================================== languages
    def set_language(self, lang):
        """Activate a Visual Programming Language: its Domain Tree, code generation and run."""
        self.language = lang
        self.library = Library(lang.components_dir)
        self.rules.library = self.library
        self.generator.library = self.library
        self.generator.lang = lang
        self.gd.last_domain = None
        self.settings.language = lang.id
        self.settings.save()
        self.update_language_ui()

    def update_language_ui(self):
        self.languages.reload()
        self.vpl_combo["values"] = [x.name for x in self.languages.items]
        self.vpl_combo.set(self.language.name)
        info = self.language.title
        if self.language.is_python:
            info = "Python %d.%d" % sys.version_info[:2]
        self.toolbar.itemconfigure("langinfo", text="Language : %s  " % info)

    def change_language(self, name):
        lang = self.languages.get(name)
        if lang is None or lang.id == self.language.id:
            self.update_language_ui()
            return
        if not self.ask_save():
            self.update_language_ui()
            return
        self.set_language(lang)
        self.set_project(self.start_project())
        self.status("Visual Programming Language : %s  -  %d components  (%s)"
                    % (lang.name, len(self.library.all()), lang.description))

    def _fill_vpl_menu(self):
        self.vpl_menu.delete(0, "end")
        self.languages.reload()
        self._vpl_var = tk.StringVar(value=self.language.id)
        for lang in self.languages.items:
            self.vpl_menu.add_radiobutton(label=lang.name, value=lang.id, variable=self._vpl_var,
                                          command=lambda n=lang.name: self.change_language(n))

    def start_project(self):
        """File > New: the start file of the language (like VPLS/*/Start.SSF) or an empty file."""
        lang = self.language
        if lang.start_file and os.path.exists(lang.start_file):
            try:
                p = Project.load(lang.start_file)
                p.filename = None
                p.modified = False
                p.language = lang.id
                return p
            except (OSError, ValueError, KeyError):
                pass
        return Project(lang.id)

    def languages_list(self):
        from .languagesdlg import LanguagesDialog
        LanguagesDialog(self).show()
        self.update_language_ui()

    # =========================================================== project
    def set_project(self, project):
        self.library.update_keys(project)
        self.project = project
        self.rules.project = project
        self.generator.project = project
        self.gd.load_project()
        self.update_title()

    def ask_save(self):
        if not self.project.modified:
            return True
        r = messagebox.askyesnocancel("Question", "Save Changes ? ", parent=self.root)
        if r is None:
            return False
        return self.save() if r else True

    def new_file(self):
        if self.ask_save():
            self.set_project(self.start_project())
            self.status("New visual source file  -  " + self.language.name)

    def close_file(self):
        self.new_file()

    def open_dialog(self):
        if not self.ask_save():
            return
        f = filedialog.askopenfilename(parent=self.root, filetypes=FILETYPES,
                                       initialdir=self.settings.last_dir or self.language.samples_dir)
        if f:
            self.open_file(f, asked=True)

    def open_file(self, filename, asked=False, sample=False):
        if not asked and not self.ask_save():
            return
        try:
            p = Project.load(filename)
        except (OSError, ValueError, KeyError) as ex:
            messagebox.showerror("Error", "The File is not valid - Process Canceled\n\n%s" % ex, parent=self.root)
            return
        if p.language.lower() != self.language.id.lower():
            lang = self.languages.get(p.language)
            if lang is None:
                messagebox.showerror("Sorry", "The Visual Programming Language (%s) of this file is not installed"
                                     % p.language, parent=self.root)
                return
            self.set_language(lang)
        self.generator.project = p
        upgraded = FormModel.upgrade_windows(p, self.library, self.generator)
        self.set_project(p)
        if not sample:
            self.settings.add_recent(filename)
            self.settings.save()
        missing = {i.component for i in p.interactions if self.library.get(i.component) is None}
        msg = "File opened : " + os.path.basename(filename)
        if upgraded:
            msg += "   (%d window(s) updated : Start Here + End of Window)" % upgraded
        if missing:
            msg += "   (Components not found : %s)" % ", ".join(sorted(missing))
        self.status(msg)

    def _fill_recent(self):
        self.recent_menu.delete(0, "end")
        files = [f for f in self.settings.recent if os.path.exists(f)]
        if not files:
            self.recent_menu.add_command(label="(Empty)", state="disabled")
        for f in files:
            self.recent_menu.add_command(label=f, command=lambda ff=f: self.open_file(ff))

    def save(self):
        if not self.project.filename:
            return self.save_as()
        try:
            self.project.save()
        except OSError as ex:
            messagebox.showerror("Error", str(ex), parent=self.root)
            return False
        self.settings.add_recent(self.project.filename)
        self.settings.save()
        self.update_title()
        self.status("Saved : " + os.path.basename(self.project.filename))
        return True

    def save_as(self):
        f = filedialog.asksaveasfilename(parent=self.root, filetypes=FILETYPES, defaultextension=FILE_EXT,
                                         initialdir=self.settings.last_dir or os.path.expanduser("~"))
        if not f:
            return False
        self.project.filename = f
        return self.save()

    def exit(self):
        if self.ask_save():
            self.gd.stop_movie()
            self.settings.save()
            self.root.destroy()

    # ============================================================== goals
    def new_goal(self):
        name = ask_string(self.root, "New Goal", "Goal Name :")
        if not name:
            return
        if self.project.goal(name):
            messagebox.showinfo("Sorry", "There are already goal with the same name", parent=self.root)
            return
        self.project.add_goal(name)
        self.gd.select_goal(name)
        self.update_title()

    def edit_goal(self):
        g = self.gd.goal
        name = ask_string(self.root, "Edit Goal", "Goal Name :", g.name)
        if not name or name == g.name:
            return
        if self.project.goal(name):
            messagebox.showinfo("Sorry", "There are already goal with the same name", parent=self.root)
            return
        for it in self.project.interactions:
            if it.goal == g.name:
                it.goal = name
        g.name = name
        self.project.modified = True
        self.gd.select_goal(name)
        self.update_title()

    def delete_goal(self):
        if len(self.project.goals) < 2:
            messagebox.showinfo("Sorry", "The visual source must contain at least one goal", parent=self.root)
            return
        g = self.gd.goal
        if messagebox.askyesno("Delete", "Are you sure that you want to delete the goal (%s) ?" % g.name,
                               parent=self.root):
            self.project.remove_goal(g)
            self.gd.select_goal(self.project.goals[0].name)
            self.update_title()

    # ============================================================ windows
    def show_code(self):
        CodeViewer(self).show(modal=False)

    def steps_colors(self):
        StepsColorsDialog(self).show()

    def vpl_compiler(self):
        VPLCompilerDialog(self).show(modal=False)

    def domain_tree(self):
        DomainTreeDialog(self).show()

    def component_designer(self, component=None, domain=None, tab=0):
        from .designer import ComponentDesigner
        ComponentDesigner(self, component, domain, tab)

    def edit_step_component(self):
        s = self.gd.selected()
        comp = self.rules.component_of(s) if s is not None else None
        if comp is None:
            messagebox.showinfo("Sorry", "Select a generated step first", parent=self.root)
            return
        self.component_designer(comp, tab=1)

    def reload_components(self):
        self.library.reload()
        self.gd.refresh()
        self.status("Components reloaded : %d components" % len(self.library.all()))

    def samples(self):
        SamplesDialog(self, self.language.samples_dir).show()

    def about(self):
        AboutDialog(self).show()

    def toggle_welcome(self):
        self.settings.show_welcome = not self.settings.show_welcome
        self.settings.save()
        self.status("Welcome window at startup : " + ("On" if self.settings.show_welcome else "Off"))

    # ============================================================== tools
    def tool(self, exe):
        try:
            subprocess.Popen([exe])
        except OSError:
            self.status("Sorry, can't run " + exe)

    def idle(self):
        subprocess.Popen([python_exe(), "-m", "idlelib"])

    def output_path(self):
        """Next to the visual source file - but the samples of PyPWCT are generated in the run folder."""
        fn = self.project.filename
        if fn and os.path.normcase(os.path.abspath(fn)).startswith(os.path.normcase(LANGUAGES_DIR)):
            os.makedirs(self.run_dir, exist_ok=True)
            name = os.path.splitext(os.path.basename(fn))[0]
            return os.path.join(self.run_dir, name + self.language.extension)
        return codegen.output_path(self.project, self.run_dir, self.language.extension)

    def open_output_folder(self):
        folder = os.path.dirname(self.output_path())
        if hasattr(os, "startfile"):
            os.startfile(folder)
        else:
            webbrowser.open("file://" + folder)

    # ========================================================== run code
    @staticmethod
    def python_exe():
        return python_exe()

    def _check_code(self):
        files = {}
        code, linemap = codegen.generate(self.project, files=files, lang=self.language)
        err = codegen.check_syntax(code, linemap, files, self.language)
        if err is not None:
            msg, line, step, fname = err
            where = step.name if step else "line %s" % line
            if fname != "<generated>":
                where += "  (file : %s)" % fname
            messagebox.showerror("VPL Compiler", "Syntax Error : %s\n\nStep : %s" % (msg, where), parent=self.root)
            if step is not None:
                self.gd.goto_step(step.id)
            return None
        return code, files

    def generate_file(self):
        checked = self._check_code()
        if checked is None:
            return None
        code, files = checked
        path = self.output_path()
        try:
            written = codegen.write_files(path, code, files)
        except OSError as ex:
            messagebox.showerror("Error", str(ex), parent=self.root)
            return None
        extra = "  (+ %d files)" % (len(written) - 1) if len(written) > 1 else ""
        self.status("Source code generated : " + os.path.basename(path) + extra)
        return path

    def run_program(self):
        if not any(g.root.children for g in self.project.goals):
            self.status("No steps inside the steps tree")
            return
        lang = self.language
        path = self.generate_file()
        if path is None:
            return
        values = lang.placeholders(path)
        steps = []
        if lang.build:
            cmd = lang.command(lang.build, values)
            if cmd is None:
                self.tool_missing("build", lang.build)
                return
            steps.append({"title": "Build", "cmd": cmd})
        cmd = lang.command(lang.run, values)
        if cmd is None:
            self.tool_missing("run", lang.run)
            return
        steps.append({"title": "Run", "cmd": cmd})
        job = os.path.join(self.run_dir, "job.json")
        os.makedirs(self.run_dir, exist_ok=True)
        with open(job, "w", encoding="utf-8") as f:
            json.dump({"cwd": os.path.dirname(path), "title": "%s - %s" % (lang.name, os.path.basename(path)),
                       "steps": steps}, f)
        runner = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runner.py")
        cmd = [python_exe(), runner, job]
        try:
            if os.name == "nt":
                subprocess.Popen(cmd, cwd=os.path.dirname(path), creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                for term in (["x-terminal-emulator", "-e"], ["gnome-terminal", "--"], ["xterm", "-e"],
                             ["open", "-a", "Terminal"]):
                    try:
                        subprocess.Popen(term + cmd, cwd=os.path.dirname(path))
                        break
                    except OSError:
                        continue
                else:
                    subprocess.Popen(cmd, cwd=os.path.dirname(path))
        except OSError as ex:
            messagebox.showerror("Error", str(ex), parent=self.root)
            return
        self.status("Run (%s) : %s" % (lang.name, os.path.basename(path)))

    def tool_missing(self, what, alternatives):
        tools = ", ".join(self.language.missing_tools(alternatives)) or "(no command)"
        messagebox.showerror(
            "Sorry", "The tool needed to %s %s programs is not found : %s\n\n"
            "Install it, or change the commands in Transporter > Programming Languages List.\n"
            "The source code is generated in : %s" % (what, self.language.title, tools, self.output_path()),
            parent=self.root)

    # ====================================================== intellisense
    def program_names(self):
        code, _ = codegen.generate(self.project, header=False, lang=self.language)
        names = set()
        pats = [r"^\s*([A-Za-z_]\w*)\s*(?:,\s*[A-Za-z_]\w*\s*)*=(?!=)", r"\bdef\s+([A-Za-z_]\w*)",
                r"\bclass\s+([A-Za-z_]\w*)", r"\bfor\s+([A-Za-z_]\w*)\s+in\b", r"\bimport\s+([A-Za-z_]\w*)",
                r"\bas\s+([A-Za-z_]\w*)",
                r"\b(?:int|double|float|char|bool|boolean|string|String|var|let|const|void|long)\s+\**([A-Za-z_]\w*)",
                r"\bfunction\s+([A-Za-z_]\w*)"]
        for p in pats:
            names.update(re.findall(p, code, flags=re.M))
        for m in re.finditer(r"\bdef\s+\w+\(([^)]*)\)", code):
            names.update(x.split("=")[0].strip() for x in m.group(1).split(",") if x.strip())
        for n in ("self", "_pwct_file", "main", "Main", "pwctRandom", "input"):
            names.discard(n)
        return sorted(n for n in names if n)


def main(argv):
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PyPWCT.PythonEdition")
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    root.withdraw()
    filename = argv[0] if argv else None
    App(root, filename)
    root.state("zoomed") if os.name == "nt" else root.geometry("1200x780")
    root.deiconify()
    root.mainloop()
