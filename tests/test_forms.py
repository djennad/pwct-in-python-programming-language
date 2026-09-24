"""Tests of the Form Designer model (pwct/forms.py) and of Modify in the engine.

Run:  python -m unittest discover -s tests      (from the project folder)
"""

import os
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from pwct import codegen  # noqa: E402
from pwct.components import Library  # noqa: E402
from pwct.engine import Generator, InteractionError, default_values  # noqa: E402
from pwct.forms import FormModel, control_components, items_list, items_text  # noqa: E402
from pwct.languages import Languages  # noqa: E402
from pwct.model import Project  # noqa: E402

LANGS = Languages(os.path.join(BASE, "languages"))
PY = LANGS.get("Python")
LIB = Library(PY.components_dir)


def comp(name):
    return next(c for c in LIB.all() if c.name == name)


class FormTests(unittest.TestCase):
    def setUp(self):
        self.p = Project("Python")
        self.g = self.p.goals[0]
        self.gen = Generator(self.p, LIB, PY)
        self.wit = FormModel.create_window(self.p, LIB, self.gen, self.g, self.g.root)

    def model(self):
        return FormModel(self.p, LIB, self.g, self.wit, PY)

    def code(self):
        code, _ = codegen.generate(self.p, lang=PY, header=False)
        compile(code, "test", "exec")
        return code

    def test_new_window_has_event_loop(self):
        """Create Window alone shows the window: Start Here + End of Window (mainloop)."""
        self.assertEqual(len(self.g.root.children), 1)
        win = self.g.root.children[0]
        self.assertTrue(win.name.startswith("Window win1"))
        self.assertEqual([s.name for s in win.children], ["Start Here", "End of Window win1"])
        self.assertTrue(self.code().rstrip().endswith("win1.mainloop()"))

    def test_window_without_show(self):
        m = self.model()
        m.window.set("show", 0)
        m.apply(self.gen)
        self.assertNotIn("mainloop", self.code())
        self.assertEqual(len(self.g.root.children[0].children), 2)

    def test_controls_go_in_start_here(self):
        m = self.model()
        m.add(comp("Label"), 10, 10)
        m.add(comp("Button"), 10, 40)
        m.apply(self.gen)
        start = self.g.root.children[0].children[0]
        self.assertEqual(start.name, "Start Here")
        self.assertEqual([s.name.split()[0] for s in start.children], ["Label", "Button"])
        m = self.model()
        m.add(comp("Text Box"), 10, 70)
        m.apply(self.gen)
        self.assertEqual([s.name.split()[0] for s in start.children], ["Label", "Button", "Text"])

    def test_add_controls_before_event_loop(self):
        m = self.model()
        tb = {c.name: c for c in control_components(LIB)}
        for kind in ("Label", "Button", "Text Box", "Text Area", "Check Box", "List Box"):
            m.add(tb[kind], 10, 10)
        self.assertEqual(m.apply(self.gen), (0, 6, 0))
        code = self.code()
        self.assertLess(code.index("list1 = tk.Listbox"), code.index("win1.mainloop()"))
        self.assertEqual([c.name for c in self.model().controls],
                         ["label1", "button1", "text1", "area1", "check1", "list1"])

    def test_move_resize_color_and_delete(self):
        m = self.model()
        lbl = m.add(comp("Label"), 10, 10)
        m.apply(self.gen)
        m = self.model()
        lbl = m.controls[0]
        lbl.set("x", "55")
        lbl.set("w", "120")
        lbl.set("h", "30")
        lbl.set("fg", "red")
        self.assertEqual(m.apply(self.gen), (1, 0, 0))
        code = self.code()
        self.assertIn("label1.place(x=55, y=10)", code)
        self.assertIn("label1.place_configure(width=120)", code)
        self.assertIn('label1.config(fg="red")', code)
        m = self.model()
        m.delete(m.controls[0])
        self.assertEqual(m.apply(self.gen), (0, 0, 1))
        self.assertNotIn("label1", self.code())

    def test_rename_window_updates_controls_and_loop(self):
        m = self.model()
        m.add(comp("Button"), 10, 10)
        m.apply(self.gen)
        m = self.model()
        m.rename_window("main")
        m.apply(self.gen)
        code = self.code()
        self.assertIn("main = tk.Tk()", code)
        self.assertIn("tk.Button(main,", code)
        self.assertIn("main.mainloop()", code)

    def test_button_event_function_before_window(self):
        m = self.model()
        b = m.add(comp("Button"), 10, 10)
        m.apply(self.gen)
        m = self.model()
        b = m.controls[0]
        name, start = m.create_event(b, self.gen)
        m.apply(self.gen)
        self.assertEqual(name, "button1_click")
        self.assertEqual(start.name, "Start Here")
        code = self.code()
        self.assertLess(code.index("def button1_click"), code.index("win1 = tk.Tk()"))
        self.assertIn("command=button1_click", code)

    def test_invalid_name_is_refused(self):
        m = self.model()
        c = m.add(comp("Label"), 10, 10)
        c.set("name", "1abc")
        with self.assertRaises(InteractionError):
            m.apply(self.gen)

    def test_items_helpers(self):
        self.assertEqual(items_list('"One", "Two"'), ["One", "Two"])
        self.assertEqual(items_text(['a"b', "c"]), '"a\\"b", "c"')

    def test_window_of_control_step(self):
        m = self.model()
        m.add(comp("Label"), 10, 10)
        m.apply(self.gen)
        step = next(s for s in self.g.root.walk() if s.name.startswith("Label"))
        self.assertIs(FormModel.window_of_step(self.p, LIB, self.g, step), self.wit)


class UpgradeTests(unittest.TestCase):
    """Files made before 1.3: the window step had no Start Here / End of Window."""

    def setUp(self):
        self.p = Project("Python")
        self.g = self.p.goals[0]
        self.gen = Generator(self.p, LIB, PY)

    def old_window(self):
        c = comp("Create Window")
        it, _ = self.gen.run(c, default_values(c, self.p), self.g, self.g.root)
        for s in self.p.interaction_steps(it.id):
            if s.internum != 1:
                s.detach()
        it.values.pop("show", None)
        return it

    def add(self, cname, **vals):
        c = comp(cname)
        v = default_values(c, self.p)
        v.update(vals)
        self.gen.run(c, v, self.g, self.g.root)

    def code(self):
        code, _ = codegen.generate(self.p, lang=PY, header=False)
        compile(code, "test", "exec")
        return code

    def test_old_window_alone_is_shown(self):
        self.old_window()
        self.add("Label", name="label1", win="win1")
        self.assertNotIn("mainloop", self.code())
        self.assertEqual(FormModel.upgrade_windows(self.p, LIB, self.gen), 1)
        code = self.code()
        self.assertLess(code.index("label1 = tk.Label"), code.index("win1.mainloop()"))
        self.assertEqual(len(self.g.root.children), 1)
        self.assertEqual(FormModel.upgrade_windows(self.p, LIB, self.gen), 0)

    def test_old_window_with_event_loop_stays_the_same(self):
        self.old_window()
        self.add("Label", name="label1", win="win1")
        self.add("Start Event Loop", win="win1")
        before = self.code()
        self.assertEqual(FormModel.upgrade_windows(self.p, LIB, self.gen), 1)
        self.assertEqual(self.code(), before)
        self.assertEqual(self.code().count("mainloop"), 1)


class ModifyInsertTests(unittest.TestCase):
    def test_new_alternative_step_stays_in_place(self):
        """Modify that changes the root step (Call Function with/without result) keeps its place."""
        p = Project("Python")
        g = p.goals[0]
        gen = Generator(p, LIB, PY)
        call = comp("Call Function")
        vals = default_values(call, p)
        gen.run(comp("Print Text"), default_values(comp("Print Text"), p), g, g.root)
        it, _ = gen.run(call, vals, g, g.root)
        gen.run(comp("Print New Line"), {}, g, g.root)
        vals = dict(vals, result="r")
        gen.run(call, vals, g, g.root, it)
        names = [s.name for s in g.root.children]
        self.assertTrue(names[1].startswith("r = Call"), names)
        self.assertEqual(len(names), 3)

    def test_else_is_inserted_before_end_of_if(self):
        p = Project("Python")
        g = p.goals[0]
        gen = Generator(p, LIB, PY)
        c = comp("If Statement")
        it, _ = gen.run(c, default_values(c, p), g, g.root)
        vals = dict(it.values)
        vals["else"] = 1
        gen.run(c, vals, g, g.root, it)
        names = [s.name for s in g.root.children[0].children]
        self.assertEqual(names, ["Start Here", "Else", "End of If"])


if __name__ == "__main__":
    unittest.main()
