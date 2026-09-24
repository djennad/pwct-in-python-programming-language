"""Components (the PWCT "Transporter" files) and the Domain Tree.

A PWCT component was made of:
  *.TRF   transporter  : pages list, code mask, matching pairs
  *.IDF   interaction  : the controls of one interaction page
  *.RULES rules        : AllowRoot / AllowInteraction / ...
Here one JSON file holds all of them.  The folder that contains the file is
the component domain, so the folders under components/ form the Domain Tree.
"""

import json
import os
import re

COMPONENT_EXT = ".json"
ORDER_FILE = "_order.txt"
TOKEN_RE = re.compile(r"#\{([A-Za-z_][A-Za-z0-9_]*)(?::item)?\}")
# PWCT code mask variables: <T_NAME> <T_INPUT> <T_OUTPUT> <T_TB_NAME> <T_CB_NAME> <T_LB_NAME>
# (any <word> that is not an RPWI/PWCT command, like transd.scx)
MASK_VAR_RE = re.compile(r"<[A-Za-z_][A-Za-z0-9_]*>")
CONTROL_PREFIXES = ("TB_", "CB_", "LB_")


def _match_name(name, prefixes):
    """Name used by the Automatic Matching (transd.scx - Command3)."""
    name = name.strip().upper()
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
            break
    for p in CONTROL_PREFIXES:
        if name.startswith(p):
            return name[len(p):]
    return name


def new_page(name="Page1"):
    return {"name": name, "bgcolor": "#ffffff", "width": 620, "height": 320, "controls": []}


class Component:
    def __init__(self, data=None, path=None, key=None):
        data = data or {}
        self.path = path
        self.key = key or ""
        self.name = data.get("name", "New Component")
        self.description = data.get("description", "")
        self.order = data.get("order", 1000)
        self.pages = data.get("pages") or [new_page()]
        self.mask = data.get("mask", "")
        self.matching = data.get("matching", [])
        self.rules = data.get("rules", {})
        self.designer = data.get("designer")    # Form Designer mapping (pwct/forms.py)

    # ----------------------------------------------------------- domain
    @property
    def domain(self):
        return self.key.rsplit("/", 1)[0] if "/" in self.key else ""

    # --------------------------------------------------------- controls
    def controls(self):
        for page in self.pages:
            for c in page["controls"]:
                yield page, c

    def variables(self):
        """Variables of the interaction pages as (page name, variable, control)."""
        return [(p["name"], c["var"], c) for p, c in self.controls()
                if c.get("type") != "label" and c.get("var")]

    def mask_tokens(self):
        """Variables From Code Mask: #{var} and the PWCT style <T_...> variables."""
        seen = []
        for m in TOKEN_RE.finditer(self.mask):
            tok = "#{%s}" % m.group(1)
            if tok not in seen:
                seen.append(tok)
        for m in MASK_VAR_RE.finditer(self.mask):
            if not any(m.group(0).upper() == t.upper() for t in seen):
                seen.append(m.group(0))
        return seen

    def auto_pairs(self):
        """Automatic Matching: var <-> #{var}, and var <-> <T_VAR> / <T_TB_VAR> / <T_CB_VAR> / <T_LB_VAR>."""
        tokens = [t for t in self.mask_tokens() if not t.startswith("#{")]
        pairs = []
        for _, var, _ in self.variables():
            pairs.append((var, "#{%s}" % var))
            key = _match_name(var, ("D_",))
            for tok in tokens:
                if _match_name(tok[1:-1], ("T_",)) == key:
                    pairs.append((var, tok))
        return pairs

    def pairs(self):
        """Matching: interaction page variable -> code mask token."""
        if self.matching:
            return [tuple(p) for p in self.matching]
        return self.auto_pairs()

    # ------------------------------------------------------------ rules
    def _rule_list(self, name):
        return [int(x) for x in self.rules.get(name, [])]

    def allow_root(self, internum):
        return internum in self._rule_list("allow_root")

    def allow_interaction(self, internum):
        return internum in self._rule_list("allow_interaction")

    @property
    def requires_ancestor(self):
        return self.rules.get("requires_ancestor", [])

    def allowed_under(self, internum):
        """ALLOW rule: the only components accepted under the step internum (None = all)."""
        only = self.rules.get("allow", {}).get(str(internum))
        return only if only else None

    # ------------------------------------------------------------- file
    def to_dict(self):
        d = {"name": self.name, "description": self.description, "order": self.order,
             "pages": self.pages, "mask": self.mask, "rules": self.rules}
        if self.matching:
            d["matching"] = self.matching
        if self.designer:
            d["designer"] = self.designer
        return d

    def save(self, path=None):
        if path:
            self.path = path
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=1)

    @classmethod
    def load(cls, path, key=None):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data, path, key)


class Domain:
    def __init__(self, name, path, key):
        self.name = name
        self.path = path
        self.key = key
        self.children = []
        self.components = []

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


def _ordered(names, folder):
    order = []
    f = os.path.join(folder, ORDER_FILE)
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as fh:
            order = [ln.strip() for ln in fh if ln.strip()]
    rank = {n.lower(): i for i, n in enumerate(order)}
    return sorted(names, key=lambda n: (rank.get(n.lower(), len(rank)), n.lower()))


class Library:
    """All installed components, organized as the Domain Tree."""

    def __init__(self, root):
        self.root_dir = root
        self.errors = []
        self.reload()

    def reload(self):
        self.by_key = {}
        self.by_file = {}     # file name -> component (None when two domains have the same name)
        self.errors = []
        os.makedirs(self.root_dir, exist_ok=True)
        self.root = self._scan(self.root_dir, "", "Components")

    def _scan(self, folder, key, name):
        dom = Domain(name, folder, key)
        entries = os.listdir(folder)
        subdirs = [e for e in entries if os.path.isdir(os.path.join(folder, e)) and not e.startswith((".", "_"))]
        for d in _ordered(subdirs, folder):
            dom.children.append(self._scan(os.path.join(folder, d), (key + "/" + d).strip("/"), d))
        for e in entries:
            if e.lower().endswith(COMPONENT_EXT) and not e.startswith("_"):
                ckey = (key + "/" + e[:-len(COMPONENT_EXT)]).strip("/")
                try:
                    comp = Component.load(os.path.join(folder, e), ckey)
                except (OSError, ValueError) as ex:
                    self.errors.append("%s : %s" % (e, ex))
                    continue
                dom.components.append(comp)
                self.by_key[ckey.lower()] = comp
                fname = ckey.rsplit("/", 1)[-1].lower()
                self.by_file[fname] = None if fname in self.by_file else comp
        dom.components.sort(key=lambda c: (c.order, c.name.lower()))
        return dom

    def get(self, key):
        """The component of a key (domain path/file name).  When the component moved to another
        domain (the files made before the Domain Tree of 1.3 use "GUI (Tkinter)/Create_Window"),
        it is found by its file name."""
        key = (key or "").lower()
        comp = self.by_key.get(key)
        if comp is None and key:
            comp = self.by_file.get(key.rsplit("/", 1)[-1])
        return comp

    def update_keys(self, project):
        """Store the current keys of the components that moved to another domain in the
        interactions of the project.  Returns the number of updated interactions."""
        n = 0
        for it in project.interactions:
            comp = self.get(it.component)
            if comp is not None and comp.key != it.component:
                it.component = comp.key
                n += 1
        return n

    def all(self):
        out = []
        for d in self.root.walk():
            out.extend(d.components)
        return out

    def domain(self, key):
        for d in self.root.walk():
            if d.key.lower() == (key or "").lower():
                return d
        return None

    def search(self, text):
        t = text.strip().lower()
        if not t:
            return []
        comps = self.all()
        starts = [c for c in comps if c.name.lower().startswith(t)]
        inside = [c for c in comps if t in c.name.lower() and c not in starts]
        return starts + inside
