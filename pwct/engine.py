"""Code Generation Level 1 - RPWI statements (port of CGLevel1.prg).

The code mask of a component is processed in three passes:

1. <RPWI:TEST> blocks are evaluated using the values entered by the user.
   <RPWI:POSITIVE> / <RPWI:NEGATIVE> select the test type and <RPWI:VALUE>
   the value searched for (default: NEGATIVE, "0").  A NEGATIVE test keeps
   its block when the value is NOT found in the tested text, a POSITIVE
   test keeps it when the value is found.
2. The interaction page variables are replaced by their values (Matching).
3. The RPWI statements build the steps tree:
     <RPWI:NEWSTEP> name     new step under the current parent step; the
                             code lines that follow are stored in it
     <RPWI:PUTMARK> n        remember the last created step as mark n
     <RPWI:SETMARK> n        the marked step becomes the current parent
     <RPWI:SELECTSTEPBYNAME> find a step by name and make it the parent
     <RPWI:INFORMATION> txt  information about the step
     <RPWI:IGNORELAST> c     remove the last character c from the code
     <RPWI:IGNORELEVEL> n    1 = steps of this interaction, 2 = all childs
     <RPWI:NEWVAR> / <RPWI:SETVARVALUE> / <RPWI:SELECTVAR> /
     <RPWI:REPLACEVARSWITHVALUES>   temporary variables
     <RPWI:NOTE> / <*>       comments
   Any other line is code.  <RPWI:TABPUSH> and <RPWI:TABPOP> are kept in the
   code and processed by the Level 2 code generator (indentation).

Every <RPWI:NEWSTEP> of the mask has a fixed number (its order in the mask)
so a step keeps its identity when the interaction is modified later.
"""

import keyword
import re

from .model import Interaction, Step

MAX_MARKS = 30


class InteractionError(Exception):
    pass


# --------------------------------------------------------------- values

def expand_default(text, project, component):
    """Textbox default values: <autonumber> = uses of this component + 1."""
    if "<autonumber>" in text.lower():
        n = project.component_use_count(component.key) + 1 if project else 1
        text = re.sub("<autonumber>", str(n), text, flags=re.I)
    return text


def default_values(component, project=None):
    vals = {}
    for _, var, c in component.variables():
        t = c["type"]
        if t == "textbox":
            vals[var] = expand_default(c.get("text", ""), project, component)
        elif t == "listbox":
            vals[var] = int(c.get("selected", 0))
        elif t == "checkbox":
            vals[var] = int(c.get("value", 0))
    return vals


def _escape(v):
    return v.replace("\\", "\\\\").replace('"', '\\"')


def resolve_values(component, raw):
    """User values -> (code values, displayed item values) by variable."""
    code, item = {}, {}
    for _, var, c in component.variables():
        t = c["type"]
        v = raw.get(var)
        if t == "textbox":
            s = "" if v is None else str(v)
            if not c.get("escape"):
                s = s.strip()  # text literals keep their spaces
            item[var] = s.strip()
            code[var] = _escape(s) if c.get("escape") else s
        elif t == "listbox":
            items = c.get("items", [])
            values = c.get("values") or items
            idx = int(v) if v is not None else int(c.get("selected", 0))
            idx = max(0, min(idx, len(items) - 1)) if items else 0
            item[var] = items[idx] if items else ""
            if c.get("mode") == "index":
                code[var] = str(idx + 1)
            else:
                code[var] = values[idx] if idx < len(values) else ""
        elif t == "checkbox":
            code[var] = "1" if v else "0"
            item[var] = code[var]
    return code, item


IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PAIRS = {")": "(", "]": "[", "}": "{"}


def _balanced(v):
    """Generic check for the languages other than Python: brackets and quotes."""
    stack, quote, i = [], None, 0
    while i < len(v):
        ch = v[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack.pop() != PAIRS[ch]:
                return False
        i += 1
    return not stack and quote is None


def _check_kind(kind, v, python=True):
    """Syntax check of a value (the syntax directed part of the interaction)."""
    if not python:
        if kind == "name":
            return bool(IDENT_RE.match(v))
        if kind in ("expr", "target", "args", "params"):
            return _balanced(v) and "\n" not in v
        return "\n" not in v
    try:
        if kind == "expr":
            compile(v, "<value>", "eval")
        elif kind == "target":
            compile(v + " = None", "<value>", "exec")
        elif kind == "name":
            return v.isidentifier() and not keyword.iskeyword(v)
        elif kind == "params":
            compile("def _f(%s): pass" % v, "<value>", "exec")
        elif kind == "args":
            compile("_f(%s)" % v, "<value>", "eval")
        elif kind == "module":
            compile("import " + v, "<value>", "exec")
        elif kind == "stmt":
            compile(v, "<value>", "exec")
    except (SyntaxError, ValueError):
        return False
    return "\n" not in v


KIND_NAMES = {
    "expr": "an expression",
    "target": "a variable",
    "name": "a name (identifier)",
    "params": "a list of parameters",
    "args": "a list of arguments",
    "module": "a module name",
    "stmt": "a Python statement",
}


def check_values(component, raw, lang=None):
    """Return the list of error messages for the values entered by the user."""
    python = lang is None or lang.is_python
    code, _ = resolve_values(component, raw)
    used_text = "\n".join(t for t, _ in evaluate_tests(_mask_lines(component.mask), component, code))
    errors = []
    for var, tok in component.pairs():
        ctrl = _control(component, var)
        if ctrl is None or tok.lower() not in used_text.lower():
            continue
        title = ctrl.get("title") or var
        value = str(raw.get(var, "")).strip() if ctrl["type"] == "textbox" else code.get(var, "")
        if value == "":
            if not ctrl.get("allow_empty"):
                errors.append("Sorry, the value of (%s) is empty" % title)
            continue
        kind = ctrl.get("kind", "any")
        if ctrl["type"] == "textbox" and kind in KIND_NAMES and not _check_kind(kind, value, python):
            errors.append("Sorry, (%s) must be %s : %s" % (title, KIND_NAMES[kind], value))
    return errors


def _control(component, var):
    for _, v, c in component.variables():
        if v == var:
            return c
    return None


# ----------------------------------------------------------- mask passes

def _mask_lines(mask):
    """Strip tabs/spaces (like ALLTRIM) and number the <RPWI:NEWSTEP> lines."""
    out = []
    n = 0
    for ln in mask.splitlines():
        ln = ln.strip()
        if ln.upper().startswith("<RPWI:NEWSTEP>"):
            n += 1
            out.append((ln, n))
        else:
            out.append((ln, 0))
    return out


def substitute(text, mapping):
    for tok in sorted(mapping, key=len, reverse=True):
        if tok and tok.lower() in text.lower():
            text = re.sub(re.escape(tok), lambda m, v=mapping[tok]: v, text, flags=re.I)
    return text


def _mapping(component, code, item):
    mapping = {}
    for var, tok in component.pairs():
        if var in code:
            mapping[tok] = code[var]
            if tok.startswith("#{") and tok.endswith("}"):
                mapping[tok[:-1] + ":item}"] = item.get(var, "")
            else:
                mapping[tok + ":item"] = item.get(var, "")
                mapping[tok + ":idflistboxitem"] = item.get(var, "")  # PWCT name
    return mapping


def evaluate_tests(lines, component, code, item=None):
    """Pass 1: keep or drop the <RPWI:TEST> ... <RPWI:ENDTEST> blocks."""
    mapping = _mapping(component, code, item or {})
    state = {"positive": False, "value": "0"}
    out = []

    def run(start, end):
        i = start
        while i < end:
            ln, num = lines[i]
            u = ln.upper()
            if u.startswith("<RPWI:POSITIVE>"):
                state["positive"] = True
            elif u.startswith("<RPWI:NEGATIVE>"):
                state["positive"] = False
            elif u.startswith("<RPWI:VALUE>"):
                state["value"] = ln[12:].strip()
            elif u.startswith("<RPWI:ENDTEST>"):
                pass
            elif u.startswith("<RPWI:TEST>"):
                expr = substitute(ln[11:], mapping).strip()
                depth, j = 1, i + 1
                while j < end:
                    uj = lines[j][0].upper()
                    if uj.startswith("<RPWI:TEST>"):
                        depth += 1
                    elif uj.startswith("<RPWI:ENDTEST>"):
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                value = state["value"]
                found = (value in expr) if value else (expr == "")
                if found == state["positive"]:
                    run(i + 1, j)
                i = j
            elif ln:
                out.append((ln, num))
            i += 1

    run(0, len(lines))
    return out


# ------------------------------------------------------------ generator

class Generator:
    """Runs a component interaction against a project (add or modify)."""

    def __init__(self, project, library, lang=None):
        self.project = project
        self.library = library
        self.lang = lang

    def run(self, component, raw, goal, parent, interaction=None):
        """Generate steps under `parent`.

        interaction=None -> new interaction (Interact / Again)
        interaction=obj  -> modify the steps of an old interaction
        Returns (interaction, list of new steps).
        """
        errors = check_values(component, raw, self.lang)
        if errors:
            raise InteractionError("\n".join(errors))

        code, item = resolve_values(component, raw)
        mapping = _mapping(component, code, item)
        lines = evaluate_tests(_mask_lines(component.mask), component, code, item)
        lines = [[substitute(ln, mapping), num] for ln, num in lines]

        project = self.project
        modify = interaction is not None
        old = {}
        if modify:
            interaction.values = dict(raw)
            old = {s.internum: s for s in project.interaction_steps(interaction.id)}
        else:
            interaction = Interaction(project.new_id(), component.key, raw, parent.id, goal.name)
            project.interactions.append(interaction)

        iid = interaction.id
        current_parent = parent
        record = None
        pending, info = [], []
        marks = {n: parent for n in range(1, MAX_MARKS + 1)}
        last_created = parent
        used = set()
        level1 = []
        created = []
        ignore_last, ignore_level = None, 1
        tmpvars, active = [], None

        def flush():
            if record is None or record.interaction_id != iid:
                return
            if pending:
                record.code += "".join(ln + "\n" for ln in pending)
                del pending[:]
            if info:
                record.info += "".join(ln + "\n" for ln in info)
                del info[:]

        i = 0
        while i < len(lines):
            ln, num = lines[i]
            u = ln.upper()
            i += 1
            if u.startswith("<"):
                if u.startswith("<RPWI:NOTE>") or u.startswith("<*>"):
                    continue
                if u.startswith("<RPWI:IGNORELAST>"):
                    ignore_last = ln[17:].strip()
                    continue
                if u.startswith("<RPWI:IGNORELEVEL>"):
                    ignore_level = _int(ln[18:], 1)
                    continue
                if u.startswith("<RPWI:INFORMATION>"):
                    info.append(ln[18:].strip())
                    continue
                if u.startswith("<RPWI:NEWVAR>"):
                    name = ln[13:].strip()
                    tmpvars.append([name, name])
                    active = len(tmpvars) - 1
                    continue
                if u.startswith("<RPWI:SETVARVALUE>"):
                    if active is not None:
                        tmpvars[active][1] = ln[18:].strip()
                    continue
                if u.startswith("<RPWI:SELECTVAR>"):
                    name = ln[16:].strip().lower()
                    active = next((k for k, v in enumerate(tmpvars) if v[0].lower() == name), None)
                    continue
                if u.startswith("<RPWI:REPLACEVARSWITHVALUES>"):
                    vm = {"<%s>" % n: v for n, v in tmpvars}
                    for rest in lines[i:]:
                        rest[0] = substitute(rest[0], vm)
                    continue
                if u.startswith("<RPWI:PUTMARK>"):
                    n = _int(ln[14:], 0)
                    if 1 < n <= MAX_MARKS:
                        marks[n] = last_created
                    continue
                if u.startswith("<RPWI:SETMARK>"):
                    n = _int(ln[14:], 0)
                    if 1 <= n <= MAX_MARKS:
                        flush()
                        current_parent = record = marks[n]
                    continue
                if u.startswith("<RPWI:SELECTSTEPBYNAME>"):
                    flush()
                    found = self._step_by_name(goal, iid, ln[23:].strip())
                    if found is not None:
                        current_parent = record = found
                    continue
                if u.startswith("<RPWI:NEWSTEP>"):
                    flush()
                    name = ln[14:].strip()
                    step = old.get(num) if modify else None
                    if step is not None:
                        step.name = name
                        step.code = ""
                        step.info = ""
                    else:
                        step = Step(project.new_id(), name, interaction_id=iid, internum=num)
                        current_parent.add(step, self._insert_index(current_parent, iid, num) if modify else None)
                        created.append(step)
                    used.add(num)
                    level1.append(step)
                    record = last_created = step
                    continue
            if ln:
                pending.append(ln)
        flush()

        # steps of the old interaction that are not generated any more
        for num, step in old.items():
            if num not in used and step.parent is not None:
                step.detach()

        if ignore_last:
            candidates = list(parent.children) if ignore_level == 2 else level1
            self._ignore_last(candidates, ignore_last)

        project.modified = True
        return interaction, created

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _insert_index(parent, iid, num):
        """Modify: the place of a new step between the steps of the same interaction."""
        last = None
        for k, s in enumerate(parent.children):
            if s.interaction_id == iid:
                if s.internum > num:
                    return k          # before the next step of the interaction
                last = k
        return None if last is None else last + 1   # after the previous one (or at the end)

    @staticmethod
    def _ignore_last(steps, ch):
        for step in reversed(steps):
            code_lines = step.code.split("\n")
            for k in range(len(code_lines) - 1, -1, -1):
                ln = code_lines[k].rstrip()
                if ln.endswith(ch):
                    code_lines[k] = ln[:-len(ch)]
                    step.code = "\n".join(code_lines)
                    return

    def _step_by_name(self, goal, iid, name):
        name = name.lower()
        steps = list(goal.root.walk())
        for s in steps:
            if s.interaction_id == iid and s.name.lower() == name:
                return s
        for s in steps:
            if s.name.lower() == name:
                return s
        return None


def _int(s, default):
    try:
        return int(s.strip())
    except ValueError:
        return default
