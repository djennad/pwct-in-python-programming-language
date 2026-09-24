"""User settings (Style.txt of PWCT: steps colors, tree font, syntax directed editor)."""

import json
import os

from .rules import ALLOW_SUB, ALLOW_SUB_LEAF, CREATED, GENERATED, LEAF, ROOT

# (font color, back color) for each step type
STYLES = {
    "Default": {CREATED: ("#ffffff", "#b8860b"), GENERATED: ("#000000", "#ffffff"),
                ROOT: ("#ffffff", "#0000ff"), ALLOW_SUB: ("#000000", "#00ff00"),
                LEAF: ("#000000", "#ffffff"), ALLOW_SUB_LEAF: ("#000000", "#00ff00")},
    "Black & White": {t: ("#000000", "#ffffff") for t in range(1, 7)},
    "Simple Colors": {CREATED: ("#b8860b", "#ffffff"), GENERATED: ("#000000", "#ffffff"),
                      ROOT: ("#0000ff", "#ffffff"), ALLOW_SUB: ("#000000", "#00ff00"),
                      LEAF: ("#000000", "#ffffff"), ALLOW_SUB_LEAF: ("#000000", "#00ff00")},
    "Read Mode": {CREATED: ("#000000", "#ffffff"), GENERATED: ("#000000", "#ffffff"),
                  ROOT: ("#0000ff", "#ffffff"), ALLOW_SUB: ("#000000", "#00ff00"),
                  LEAF: ("#ffffff", "#ffffff"), ALLOW_SUB_LEAF: ("#ffffff", "#ffffff")},
    "Read & Design Modes": {CREATED: ("#000000", "#ffffff"), GENERATED: ("#000000", "#ffffff"),
                            ROOT: ("#0000ff", "#ffffff"), ALLOW_SUB: ("#000000", "#00ff00"),
                            LEAF: ("#ffffff", "#ffffff"), ALLOW_SUB_LEAF: ("#000000", "#00ff00")},
}
DEFAULT_STYLE = "Simple Colors"


def config_dir():
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    d = os.path.join(base, "PyPWCT")
    os.makedirs(d, exist_ok=True)
    return d


class Settings:
    def __init__(self):
        self.path = os.path.join(config_dir(), "settings.json")
        self.tree_font = "Arial"
        self.tree_font_size = 13
        self.syntax_directed = True
        self.colors = dict(STYLES[DEFAULT_STYLE])
        self.recent = []
        self.last_dir = ""
        self.show_welcome = True
        self.language = "Python"
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            return
        self.tree_font = d.get("tree_font", self.tree_font)
        self.tree_font_size = d.get("tree_font_size", self.tree_font_size)
        self.syntax_directed = d.get("syntax_directed", self.syntax_directed)
        self.recent = [r for r in d.get("recent", []) if isinstance(r, str)]
        self.last_dir = d.get("last_dir", "")
        self.show_welcome = d.get("show_welcome", True)
        self.language = d.get("language", "Python")
        for k, v in d.get("colors", {}).items():
            self.colors[int(k)] = tuple(v)

    def save(self):
        d = {"tree_font": self.tree_font, "tree_font_size": self.tree_font_size,
             "syntax_directed": self.syntax_directed, "recent": self.recent[:10],
             "last_dir": self.last_dir, "show_welcome": self.show_welcome, "language": self.language,
             "colors": {str(k): list(v) for k, v in self.colors.items()}}
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=1)
        except OSError:
            pass

    def add_recent(self, filename):
        filename = os.path.abspath(filename)
        self.recent = [r for r in self.recent if os.path.normcase(r) != os.path.normcase(filename)]
        self.recent.insert(0, filename)
        del self.recent[10:]
        self.last_dir = os.path.dirname(filename)
