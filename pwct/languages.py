"""Visual Programming Languages (the VPLS folder of PWCT).

PWCT 1.9 could work with many programming languages behind the scene
(HarbourPWCT, PythonPWCT, C#PWCT, CPWCT, SupernovaPWCT).  Each VPL file
(VPLS/*.txt) gave: the components data folder, the VPL name, the extension of
the generated file, the build command and the start file.

Here each language is a folder:  languages/<id>/
    language.json   name, extension, comment, indentation, prelude,
                    build / run / check commands
    components/     the Domain Tree of this language
    samples/        samples (*.pwct)
    start.pwct      (optional) the visual source used by File > New
"""

import json
import os
import re
import shlex
import shutil
import sys

LANGUAGE_FILE = "language.json"
ORDER_FILE = "_order.txt"
DEFAULT_ID = "Python"


def python_exe():
    exe = sys.executable
    if os.path.basename(exe).lower() == "pythonw.exe":
        cand = os.path.join(os.path.dirname(exe), "python.exe")
        if os.path.exists(cand):
            return cand
    return exe


class Language:
    FIELDS = ("name", "title", "extension", "comment", "indent", "empty_block", "prelude",
              "build", "run", "check", "keywords", "syntax", "description", "start")

    def __init__(self, lid, path, data=None):
        data = data or {}
        self.id = lid
        self.path = path
        self.name = data.get("name", lid + "PWCT")
        self.title = data.get("title", lid)
        self.extension = data.get("extension", ".txt")
        self.comment = data.get("comment", "//")
        self.indent = data.get("indent", "    ")
        self.empty_block = data.get("empty_block", "")      # Python needs "pass"
        self.prelude = data.get("prelude", "")              # code added at the start of the program
        self.build = data.get("build", [])                  # alternatives (the first one found is used)
        self.run = data.get("run", [])
        self.check = data.get("check", [])
        self.keywords = data.get("keywords", "")
        self.syntax = data.get("syntax", "")                # "python" = internal syntax check
        self.description = data.get("description", "")
        self.start = data.get("start", "")

    @property
    def components_dir(self):
        return os.path.join(self.path, "components")

    @property
    def samples_dir(self):
        return os.path.join(self.path, "samples")

    @property
    def start_file(self):
        return os.path.join(self.path, self.start) if self.start else ""

    @property
    def is_python(self):
        return self.syntax == "python"

    def to_dict(self):
        return {f: getattr(self, f) for f in self.FIELDS}

    def save(self):
        os.makedirs(self.path, exist_ok=True)
        with open(os.path.join(self.path, LANGUAGE_FILE), "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=1)

    # ------------------------------------------------------------ commands
    def placeholders(self, source, tmpdir=None):
        folder, fname = os.path.split(source)
        name = os.path.splitext(fname)[0]
        exe = os.path.join(folder, name + (".exe" if os.name == "nt" else ""))
        return {"file": source, "dir": folder, "name": name, "exe": exe, "python": python_exe(),
                "tmpdir": tmpdir or folder}

    def command(self, alternatives, values):
        """First alternative whose program exists -> argument list (or None).

        A program given by a variable ({exe}: made by the build) is not checked."""
        for template in alternatives:
            raw = split_command(template, {})
            args = split_command(template, values)
            if args and ("{" in raw[0] or program_exists(args[0])):
                return args
        return None

    def missing_tools(self, alternatives):
        names = []
        for template in alternatives:
            parts = split_command(template, {})
            if parts:
                names.append(os.path.basename(parts[0]))
        return names


def split_command(template, values):
    """'gcc "{file}" -o "{exe}"' -> ['gcc', <file>, '-o', <exe>]."""
    try:
        parts = shlex.split(template, posix=False)
    except ValueError:
        parts = template.split()
    out = []
    for p in parts:
        if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'":
            p = p[1:-1]
        p = p.replace('"', "")  # /out:"{exe}" -> /out:{exe}  (the arguments are passed as a list)
        p = os.path.expandvars(p)
        for k, v in values.items():
            p = p.replace("{%s}" % k, v)
        out.append(p)
    return out


def program_exists(prog):
    if os.path.isabs(prog) or os.sep in prog or "/" in prog:
        return os.path.exists(prog)
    return shutil.which(prog) is not None


def error_lines(output, source):
    """Line numbers of the compiler messages about the generated file."""
    base = re.escape(os.path.basename(source))
    found = []
    for ln in output.splitlines():
        m = re.search(base + r"(?::|\()(\d+)", ln)
        if m:
            found.append((int(m.group(1)), ln.strip()))
    return found


class Languages:
    def __init__(self, root):
        self.root = root
        self.reload()

    def reload(self):
        self.items = []
        os.makedirs(self.root, exist_ok=True)
        order = []
        f = os.path.join(self.root, ORDER_FILE)
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fh:
                order = [ln.strip() for ln in fh if ln.strip()]
        rank = {n.lower(): i for i, n in enumerate(order)}
        ids = [d for d in os.listdir(self.root)
               if os.path.exists(os.path.join(self.root, d, LANGUAGE_FILE))]
        for lid in sorted(ids, key=lambda n: (rank.get(n.lower(), len(rank)), n.lower())):
            path = os.path.join(self.root, lid)
            try:
                with open(os.path.join(path, LANGUAGE_FILE), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, ValueError):
                continue
            self.items.append(Language(lid, path, data))

    def get(self, lid):
        for lang in self.items:
            if lang.id.lower() == (lid or "").lower() or lang.name.lower() == (lid or "").lower():
                return lang
        return None

    def default(self):
        return self.get(DEFAULT_ID) or (self.items[0] if self.items else None)

    def create(self, lid, data):
        path = os.path.join(self.root, lid)
        lang = Language(lid, path, data)
        lang.save()
        os.makedirs(lang.components_dir, exist_ok=True)
        os.makedirs(lang.samples_dir, exist_ok=True)
        self.reload()
        return self.get(lid)


# Used when no language is given (the Python rules of the first version)
PYTHON = Language(DEFAULT_ID, "", {"name": "PythonPWCT", "title": "Python", "extension": ".py", "comment": "#",
                                    "indent": "    ", "empty_block": "pass", "syntax": "python"})
