"""Tests of the Domain Tree: nested domains, the keys of the components that moved,
and the generator tools that must keep the components made by the user.

Run:  python -m unittest discover -s tests      (from the project folder)
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))

from pwct.components import Library  # noqa: E402
from pwct.model import Interaction, Project  # noqa: E402
import make_components  # noqa: E402

PY_DIR = os.path.join(BASE, "languages", "Python", "components")


class DomainTreeTests(unittest.TestCase):
    def setUp(self):
        self.lib = Library(PY_DIR)

    def test_nested_domains_in_order(self):
        self.assertEqual([d.name for d in self.lib.root.children],
                         ["User Interface", "Programming Basics", "Programming Paradigm", "System"])
        gui = self.lib.domain("User Interface/GUI Application")
        self.assertEqual([d.name for d in gui.children], ["Windows", "Controls"])
        self.assertIn("Create Window", [c.name for c in self.lib.domain(
            "User Interface/GUI Application/Windows").components])

    def test_old_keys_are_found(self):
        for old, new in (("GUI (Tkinter)/Create_Window", "User Interface/GUI Application/Windows/Create_Window"),
                         ("Input and Output/Print_Text", "User Interface/Print Text/Print_Text"),
                         ("Functions/Define_Function", "Programming Paradigm/Structure Programming/Define_Function")):
            self.assertEqual(self.lib.get(old).key, new)
        self.assertIsNone(self.lib.get("General/No_Such_Component"))

    def test_update_keys(self):
        p = Project("Python")
        p.interactions.append(Interaction("i1", "GUI (Tkinter)/Label", {}, "", p.goals[0].name))
        self.assertEqual(self.lib.update_keys(p), 1)
        self.assertEqual(p.interactions[0].component, "User Interface/GUI Application/Controls/Label")
        self.assertEqual(self.lib.update_keys(p), 0)

    def test_file_names_are_unique_in_each_language(self):
        for lang in ("Python", "C", "CSharp", "Java", "JavaScript"):
            lib = Library(os.path.join(BASE, "languages", lang, "components"))
            self.assertEqual([k for k, v in lib.by_file.items() if v is None], [], lang)


class WriteComponentsTests(unittest.TestCase):
    """write_components() replaces only the files it made (not the components of the user)."""

    def setUp(self):
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def user_component(self, folder):
        os.makedirs(os.path.join(self.out, folder), exist_ok=True)
        path = os.path.join(self.out, folder, "mine.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": "mine", "order": 1000, "pages": [], "mask": ""}, f)
        return path

    def test_user_component_is_kept(self):
        comps = make_components.COMPONENTS[:3]
        old = self.user_component("General")      # a folder of the old (flat) domains
        # an old generated file (order < 1000) in an old folder, without the manifest
        with open(os.path.join(self.out, "General", "Comment.json"), "w", encoding="utf-8") as f:
            json.dump({"name": "Comment", "order": 1}, f)
        make_components.write_components(comps, self.out)
        self.assertTrue(os.path.exists(old))
        self.assertFalse(os.path.exists(os.path.join(self.out, "General", "Comment.json")))
        new = self.user_component("Programming Basics/General")
        make_components.write_components(comps, self.out)      # with the manifest
        self.assertTrue(os.path.exists(new))
        lib = Library(self.out)
        self.assertEqual(len(lib.all()), 3 + 2)


if __name__ == "__main__":
    unittest.main()
