"""Form Designer model (port of the Form Designer of rpwi.scx: ld_mymap / ld_objsarr).

Like PWCT, a window is not stored in a separate form file: the window IS steps.
  - the window   = an interaction of a component whose designer type is "window"
  - its controls = the interactions of components that have a designer mapping and
                   whose "window" property is the name of the window
The designer changes the values of these interactions and runs the code generator
(Modify / new interactions), so the steps tree stays the source of the program and
everything made by the designer can still be changed with Modify.

The mapping ("designer" in the component file) says which interaction variable
holds each property (PWCT: ld_mymap - TOP ROW, LEFT ROW, WIDTH ROW...):
    {"type": "button", "props": {"name": "name", "window": "win", "x": "x", "y": "y",
                                 "w": "w", "h": "h", "text": "text", "command": "cmd", ...}}
types: window, eventloop, label, button, textbox, textarea, checkbox, listbox
"""

import ast
import keyword
import re

from .engine import InteractionError, check_values, default_values

CONTROL_TYPES = ("label", "button", "textbox", "textarea", "checkbox", "listbox")


def _dtype(component):
    return (component.designer or {}).get("type") if component is not None else None


def window_component(library):
    return next((c for c in library.all() if _dtype(c) == "window"), None)


def eventloop_component(library):
    return next((c for c in library.all() if _dtype(c) == "eventloop"), None)


def control_components(library):
    return [c for c in library.all() if _dtype(c) in CONTROL_TYPES]


def function_component(library):
    return next((c for c in library.all() if c.name == "Define Function"), None)


def is_identifier(name):
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name or "")) and not keyword.iskeyword(name)


def items_list(text):
    """'"One", "Two"' -> ['One', 'Two']"""
    text = (text or "").strip()
    if not text:
        return []
    try:
        value = ast.literal_eval("[" + text + "]")
        return [str(v) for v in value]
    except (ValueError, SyntaxError):
        return [p.strip().strip("\"'") for p in text.split(",") if p.strip()]


def items_text(items):
    """['One', 'Two'] -> '"One", "Two"'"""
    return ", ".join('"%s"' % s.replace("\\", "\\\\").replace('"', '\\"') for s in items)


class FormControl:
    """The window or one control, with the values of its interaction."""

    def __init__(self, component, values, interaction=None):
        self.component = component
        self.kind = component.designer["type"]
        self.map = component.designer.get("props", {})
        self.values = dict(values)
        self.original = dict(values)
        self.interaction = interaction
        self.deleted = False

    def has(self, prop):
        return prop in self.map

    def get(self, prop, default=""):
        var = self.map.get(prop)
        if var is None:
            return default
        v = self.values.get(var)
        return default if v is None else str(v)

    def set(self, prop, value):
        var = self.map.get(prop)
        if var is not None:
            self.values[var] = value

    def geti(self, prop, default=0):
        """Integer value of a property (None when it is an expression that the designer can't use)."""
        v = self.get(prop, "").strip()
        if v == "":
            return default
        try:
            return int(round(float(v)))
        except ValueError:
            return None

    @property
    def name(self):
        return self.get("name")

    @property
    def is_new(self):
        return self.interaction is None

    @property
    def changed(self):
        norm = lambda d: {k: str(v) for k, v in d.items()}
        return norm(self.values) != norm(self.original)


class FormModel:
    def __init__(self, project, library, goal, window_interaction, lang=None):
        self.project = project
        self.library = library
        self.goal = goal
        self.lang = lang
        comp = library.get(window_interaction.component)
        if comp is None or _dtype(comp) != "window":
            raise ValueError("The step is not a window")
        self.window = FormControl(comp, self._values(comp, window_interaction), window_interaction)
        self.controls = []
        self.eventloop = None
        wname = self.window.name
        for it, comp in self._interactions():
            if it is window_interaction:
                continue
            t = _dtype(comp)
            if t in CONTROL_TYPES:
                c = FormControl(comp, self._values(comp, it), it)
                if c.get("window") == wname:
                    self.controls.append(c)
            elif t == "eventloop" and self.eventloop is None:
                c = FormControl(comp, self._values(comp, it), it)
                if c.get("window") == wname:
                    self.eventloop = c

    # ------------------------------------------------------------ helpers
    def _values(self, comp, it):
        vals = default_values(comp, self.project)
        vals.update(it.values)
        return vals

    def _interactions(self):
        """Interactions of the goal in the order of their root steps in the tree."""
        seen = []
        for s in self.goal.root.walk():
            if s.interaction_id and s.interaction_id not in seen:
                seen.append(s.interaction_id)
        out = []
        for iid in seen:
            it = self.project.interaction(iid)
            comp = self.library.get(it.component) if it else None
            if comp is not None and comp.designer:
                out.append((it, comp))
        return out

    @staticmethod
    def windows(project, library, goal):
        """[(interaction, window name)] of the goal, in the steps order."""
        out = []
        seen = set()
        for s in goal.root.walk():
            iid = s.interaction_id
            if not iid or iid in seen:
                continue
            seen.add(iid)
            it = project.interaction(iid)
            comp = library.get(it.component) if it else None
            if _dtype(comp) == "window":
                vals = default_values(comp, project)
                vals.update(it.values)
                out.append((it, str(vals.get(comp.designer["props"].get("name", "name"), ""))))
        return out

    @staticmethod
    def window_of_step(project, library, goal, step):
        """The window interaction of a step (the window itself or one of its controls)."""
        s = step
        while s is not None and not s.interaction_id:
            s = s.parent
        if s is None:
            return None
        it = project.interaction(s.interaction_id)
        comp = library.get(it.component) if it else None
        t = _dtype(comp)
        if t == "window":
            return it
        if t in CONTROL_TYPES or t == "eventloop":
            var = comp.designer["props"].get("window")
            wname = str(it.values.get(var, "")) if var else ""
            for wit, name in FormModel.windows(project, library, goal):
                if name == wname:
                    return wit
        return None

    def used_names(self):
        names = set()
        for it in self.project.interactions:
            comp = self.library.get(it.component)
            if comp is not None and comp.designer and "name" in comp.designer.get("props", {}):
                names.add(str(it.values.get(comp.designer["props"]["name"], "")))
        for c in [self.window] + self.controls:
            names.add(c.name)
        fn = function_component(self.library)
        if fn is not None:
            names.update(str(i.values.get("name", "")) for i in self.project.interactions if i.component == fn.key)
        return names

    def unique_name(self, prefix):
        used = self.used_names()
        n = 1
        while "%s%d" % (prefix, n) in used:
            n += 1
        return "%s%d" % (prefix, n)

    def functions(self):
        """Names of the functions defined in the program (for the button events)."""
        fn = function_component(self.library)
        if fn is None:
            return []
        return [str(i.values.get("name", "")) for i in self.project.interactions if i.component == fn.key]

    # ------------------------------------------------------------ editing
    def add(self, component, x=20, y=20):
        vals = default_values(component, self.project)
        c = FormControl(component, vals)
        prefix = re.sub(r"<autonumber>", "", c.get("name") or component.name.lower().replace(" ", ""),
                        flags=re.I) or "control"
        prefix = re.sub(r"\d+$", "", prefix)
        c.set("name", self.unique_name(prefix))
        c.set("window", self.window.name)
        c.set("x", str(x))
        c.set("y", str(y))
        c.original = {}
        self.controls.append(c)
        return c

    def delete(self, control):
        if control.is_new:
            self.controls.remove(control)
        else:
            control.deleted = True

    def rename_window(self, new_name):
        old = self.window.name
        self.window.set("name", new_name)
        for c in self.controls:
            if c.get("window") == old:
                c.set("window", new_name)
        if self.eventloop is not None:
            self.eventloop.set("window", new_name)

    @property
    def dirty(self):
        return (self.window.changed or any(c.changed or c.is_new or c.deleted for c in self.controls)
                or (self.eventloop is not None and self.eventloop.changed))

    def validate(self):
        errors = []
        names = {}
        for c in [self.window] + [x for x in self.controls if not x.deleted]:
            if not is_identifier(c.name):
                errors.append("The name (%s) is not valid" % c.name)
            elif c.name in names:
                errors.append("The name (%s) is used two times" % c.name)
            names[c.name] = c
            if c.changed or c.is_new:
                for e in check_values(c.component, c.values, self.lang):
                    errors.append("%s : %s" % (c.name, e))
        return errors

    def container(self):
        """The step of the window that holds its controls (Start Here), None for the old windows
        that have no container (their controls are after the window, before Start Event Loop)."""
        num = (self.window.component.designer or {}).get("container")
        if not num:
            return None
        return next((s for s in self.project.interaction_steps(self.window.interaction.id)
                     if s.internum == num), None)

    def controls_place(self):
        """(parent, anchor) of the new controls: they are added after anchor (None = at the end)."""
        box = self.container()
        if box is not None:
            return box, None
        wroot = self.project.interaction_root(self.window.interaction.id)
        return wroot.parent, wroot

    def apply(self, generator):
        """Write the design to the steps tree.  Returns (updated, added, deleted)."""
        errors = self.validate()
        if errors:
            raise InteractionError("\n".join(errors))
        project, goal = self.project, self.goal
        parent, anchor = self.controls_place()
        # the new controls go after the last control of the window (before the event loop)
        for c in self.controls:
            if c.is_new or c.deleted:
                continue
            r = project.interaction_root(c.interaction.id)
            if r is not None and r.parent is parent and (
                    anchor is None or parent.children.index(r) > parent.children.index(anchor)):
                anchor = r
        updated = added = deleted = 0
        for c in [self.window] + self.controls + ([self.eventloop] if self.eventloop else []):
            if c.is_new or c.deleted or not c.changed:
                continue
            root = project.interaction_root(c.interaction.id)
            generator.run(c.component, c.values, goal, root.parent if root else parent, c.interaction)
            c.original = dict(c.values)
            updated += 1
        for c in [x for x in self.controls if x.deleted]:
            for s in project.interaction_steps(c.interaction.id):
                if s.parent is not None:
                    s.detach()
            self.controls.remove(c)
            deleted += 1
        project.purge_interactions()
        for c in self.controls:
            if not c.is_new:
                continue
            it, created = generator.run(c.component, c.values, goal, parent)
            for r in [s for s in created if s.parent is parent]:
                parent.children.remove(r)
                pos = len(parent.children) if anchor is None else parent.children.index(anchor) + 1
                parent.children.insert(pos, r)
                anchor = r
            c.interaction = it
            c.original = dict(c.values)
            added += 1
        project.modified = True
        return updated, added, deleted

    def create_event(self, control, generator):
        """New function <control>_click before the window + the command of the button.
        Returns (function name, the "Start Here" step of the function)."""
        fn = function_component(self.library)
        if fn is None:
            raise InteractionError("The component (Define Function) is not found")
        name = control.name + "_click"
        if name in self.used_names():
            name = self.unique_name(name + "_")
        vals = default_values(fn, self.project)
        vals["name"] = name
        wroot = self.project.interaction_root(self.window.interaction.id)
        parent = wroot.parent
        _, created = generator.run(fn, vals, self.goal, parent)
        for r in [s for s in created if s.parent is parent]:
            parent.children.remove(r)
            parent.children.insert(parent.children.index(wroot), r)
        control.set("command", name)
        start = next((s for s in created if s.name == "Start Here"), None)
        return name, start

    @staticmethod
    def upgrade_windows(project, library, generator):
        """Files made before PyPWCT 1.3: Create Window was one step, without (Start Here) and
        (End of Window) that shows the window.  Modify each old window so it gets them:
          - a Start Event Loop step exists for the window : Show = 0 (the program stays the same)
          - no event loop (the window was never shown)    : Show = 1, and the controls of the
            window that follow it move into its Start Here (before the event loop)
        Returns the number of upgraded windows."""
        count = 0
        for it in list(project.interactions):
            comp = library.get(it.component)
            num = (comp.designer or {}).get("container") if _dtype(comp) == "window" else None
            steps = project.interaction_steps(it.id) if num else []
            if not steps or any(s.internum == num for s in steps):
                continue
            root = project.interaction_root(it.id)
            goal = project.goal(it.goal)
            if root is None or root.parent is None or goal is None:
                continue
            vals = default_values(comp, project)
            vals.update(it.values)
            wname = str(vals.get(comp.designer["props"].get("name", "name"), ""))
            loop, controls = False, []
            for oit in project.interactions:
                ocomp = library.get(oit.component)
                t = _dtype(ocomp)
                var = ocomp.designer["props"].get("window") if t else None
                if not var or oit.goal != it.goal or str(oit.values.get(var, "")) != wname:
                    continue
                if t == "eventloop":
                    loop = True
                elif t in CONTROL_TYPES:
                    controls.append(oit)
            show = comp.designer["props"].get("show")
            if show:
                vals[show] = 0 if loop else 1
            try:
                generator.run(comp, vals, goal, root.parent, it)
            except InteractionError:
                continue
            box = next((s for s in project.interaction_steps(it.id) if s.internum == num), None)
            if box is not None and not loop:
                parent = root.parent
                for oit in controls:
                    r = project.interaction_root(oit.id)
                    if r is not None and r.parent is parent and \
                            parent.children.index(r) > parent.children.index(root):
                        r.detach()
                        box.add(r)
            count += 1
        if count:
            project.modified = True
        return count

    @staticmethod
    def create_window(project, library, generator, goal, parent):
        """New window (+ its event loop when the window component has no container) under parent.
        Returns the window interaction."""
        wcomp = window_component(library)
        vals = default_values(wcomp, project)
        wit, _ = generator.run(wcomp, vals, goal, parent)
        loop = eventloop_component(library)
        if loop is not None and not wcomp.designer.get("container"):
            lv = default_values(loop, project)
            lv[loop.designer["props"]["window"]] = str(vals[wcomp.designer["props"]["name"]])
            generator.run(loop, lv, goal, parent)
        return wit
