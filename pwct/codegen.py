"""Source code extraction (port of goaltores.prg + CGLevel2.prg).

Level 1 walks the steps tree (pre-order) and collects the code of the enabled
steps.  Level 2 processes the code generator commands:
  <RPWI:TABPUSH> / <RPWI:TABPOP>   indentation (a block with no statements
                                    gets "pass", Python needs it)
  <pwct:newline>                    empty line
  <pwct:ignorelast> text            remove text from the end of the last line
  <pwct:mergenexttoprev>            merge the next line with the last one (with a space)
  <pwct:mergenexttoprevbyspaceorstar>
                                    the same, but without the space when the
                                    last line ends with "*"
  <pwct:addvar> name                start a variable (a text to be replaced)
  <pwct:setvar> value               add a value: at the end, every occurrence
                                    of the variable is replaced by the first value
  <pwct:tofile> file ... <pwct:endfile>
                                    the lines between them are written to another
                                    file (in the folder of the generated source)
"""

import os
import sys
import textwrap

from . import APP_TITLE
from .languages import PYTHON


def level1(project, goals=None, lang=None):
    """Steps tree -> [(code line, step)]."""
    lang = lang or PYTHON
    out = []
    goals = goals if goals is not None else project.goals
    many = len(goals) > 1

    def visit(step, parent_disabled):
        disabled = parent_disabled or step.disabled
        if not disabled and step.code:
            for ln in step.code.splitlines():
                out.append((ln, step))
        for c in step.children:
            visit(c, disabled)

    for g in goals:
        if many:
            out.append((lang.comment + " " + "-" * 60, None))
            out.append((lang.comment + " Goal : " + g.name, None))
            out.append((lang.comment + " " + "-" * 60, None))
        for c in g.root.children:
            visit(c, False)
    return out


def _is_statement(text, comment="#"):
    t = text.strip()
    return bool(t) and not t.startswith(comment)


def _dedent(lines):
    text = textwrap.dedent("\n".join(t for t, _ in lines))
    return list(zip(text.split("\n"), [s for _, s in lines])) if lines else []


def level2(pairs, files=None, lang=None):
    """[(line, step)] with commands -> [(indented line, step)].

    The content of <pwct:tofile> ... <pwct:endfile> goes to files[name].
    """
    lang = lang or PYTHON
    indent = lang.indent
    filler = lang.empty_block
    if files is None:
        files = {}
    result = []
    target = result            # the main output or the content of a <pwct:tofile>
    current_file = None
    rule = None                # <pwct:addvar>
    table = []                 # [(variable, value)] from <pwct:setvar>
    level = 0
    blocks = []                # statements count inside each open block
    i = 0
    while i < len(pairs):
        text, step = pairs[i]
        cmd = text.strip()
        low = cmd.lower()
        i += 1
        if low == "<rpwi:tabpush>":
            level += 1
            blocks.append([0, step])
            continue
        if low == "<rpwi:tabpop>":
            if blocks:
                count, st = blocks.pop()
                if count == 0 and filler:
                    target.append((indent * level + filler, st))
                    if blocks:
                        blocks[-1][0] += 1
            level = max(level - 1, 0)
            continue
        if low.startswith("<pwct:tofile>"):
            if current_file is not None:
                files[current_file] = _dedent(target)
            current_file = cmd[13:].strip()
            target = []
            continue
        if low.startswith("<pwct:endfile>"):
            if current_file is not None:
                files[current_file] = _dedent(target)
            current_file = None
            target = result
            continue
        if low.startswith("<pwct:addvar>"):
            rule = cmd[13:].strip()
            continue
        if low.startswith("<pwct:setvar>"):
            if rule:
                table.append((rule, cmd[13:].strip()))
            continue
        if low.startswith("<pwct:newline>"):
            target.append(("", step))
            continue
        if low.startswith("<pwct:ignorelast>"):
            ign = cmd[17:].strip()
            if target and ign and target[-1][0].rstrip().upper().endswith(ign.upper()):
                ln, st = target[-1]
                target[-1] = (ln.rstrip()[:-len(ign)], st)
            continue
        if low.startswith("<pwct:mergenexttoprevbyspaceorstar>"):
            if i < len(pairs) and target:
                ln, st = target[-1]
                sep = "" if ln.rstrip().endswith("*") else " "
                target[-1] = (ln.rstrip() + sep + pairs[i][0].strip(), st)
                i += 1
            continue
        if low.startswith("<pwct:mergenexttoprev>"):
            if i < len(pairs) and target:
                ln, st = target[-1]
                target[-1] = (ln.rstrip() + " " + pairs[i][0].strip(), st)
                i += 1
            continue
        target.append((indent * level + cmd, step))
        if blocks and _is_statement(cmd, lang.comment):
            blocks[-1][0] += 1
    while blocks:
        count, st = blocks.pop()
        if count == 0 and filler:
            target.append((indent * level + filler, st))
        level -= 1
    if current_file is not None:
        files[current_file] = _dedent(target)
    if table:
        def apply(lines):
            out = []
            for ln, st in lines:
                for var, value in table:
                    ln = ln.replace(var, value)
                out.append((ln, st))
            return out
        result = apply(result)
        for name in files:
            files[name] = apply(files[name])
    return result


def generate(project, goals=None, header=True, files=None, lang=None, prelude=None):
    """Return (source code, line map) - line map[i] = step of line i+1.

    If files is a dict it receives {file name: code} of the <pwct:tofile> blocks.
    The prelude of the language (includes, imports...) is added when header=True.
    """
    lang = lang or PYTHON
    prelude = header if prelude is None else prelude
    extra = {}
    lines = level2(level1(project, goals, lang), extra, lang)
    head = []
    if header:
        c = lang.comment
        name = os.path.basename(project.filename) if project.filename else "(NO NAME)"
        target = ("Python %d.%d" % sys.version_info[:2]) if lang.is_python else lang.title
        head = [(c + " " + "=" * 70, None),
                (c + " Generated by %s  -  %s" % (APP_TITLE, lang.name), None),
                (c + " Visual source file : %s" % name, None),
                (c + " Language : %s" % target, None),
                (c + " " + "=" * 70, None),
                ("", None)]
    if prelude and lang.prelude.strip():
        head += [(ln, None) for ln in lang.prelude.rstrip("\n").split("\n")] + [("", None)]
    lines = head + lines
    code = "\n".join(t for t, _ in lines) + "\n"
    if files is not None:
        for fname, flines in extra.items():
            files[fname] = ("\n".join(t for t, _ in flines) + "\n", [s for _, s in flines])
    return code, [s for _, s in lines]


def with_files(code, files):
    """Main code + the <pwct:tofile> files, for display."""
    out = code
    for name, (content, _) in files.items():
        out += "\n# %s\n# File : %s  (<pwct:tofile>)\n# %s\n%s" % ("=" * 70, name, "=" * 70, content)
    return out


def check_syntax(code, linemap, files, lang=None):
    """Compile the generated Python code.  Returns None or (message, line, step, file name).

    Only Python is checked here; the other languages are checked by their compilers
    (VPL Compiler)."""
    if lang is not None and not lang.is_python:
        return None
    sources = [("<generated>", code, linemap)]
    sources += [(n, c, m) for n, (c, m) in files.items() if n.lower().endswith(".py")]
    for fname, src, lmap in sources:
        try:
            compile(src, fname, "exec")
        except SyntaxError as e:
            step = lmap[e.lineno - 1] if e.lineno and 0 < e.lineno <= len(lmap) else None
            return e.msg, e.lineno, step, fname
    return None


def output_path(project, run_dir, ext=".py"):
    if project.filename:
        base = os.path.splitext(project.filename)[0]
        return base + ext
    os.makedirs(run_dir, exist_ok=True)
    return os.path.join(run_dir, "untitled" + ext)


def write_files(main_path, code, files):
    """Write the generated source and the <pwct:tofile> files. Returns the paths written."""
    folder = os.path.dirname(main_path)
    written = []
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(code)
    written.append(main_path)
    for name, (content, _) in files.items():
        path = os.path.normpath(os.path.join(folder, name))
        if not path.startswith(os.path.normpath(folder)):
            continue  # stay inside the output folder
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(path)
    return written
