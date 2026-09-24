"""Visual source model: goals, steps tree and interaction history.

Mirrors the PWCT tables:
  t33 (goals)        -> Goal
  t38 (steps)        -> Step
  t46 (interactions) -> Interaction   (the Time Machine frames)
"""

import datetime
import json

from . import VERSION

START_POINT_NAME = "Start Point (NOT STEP)"


class Step:
    """One node in the steps tree.

    interaction_id is empty for steps created by the user (comments /
    organization steps) and set for steps generated from a component.
    internum is the step number inside its interaction (1 = root step).
    """

    def __init__(self, sid, name, code="", disabled=False, interaction_id="", internum=0):
        self.id = sid
        self.name = name
        self.code = code
        self.info = ""
        self.disabled = disabled
        self.interaction_id = interaction_id
        self.internum = internum
        self.children = []
        self.parent = None

    @property
    def generated(self):
        return bool(self.interaction_id)

    @property
    def is_start_point(self):
        return self.parent is None

    def add(self, child, index=None):
        child.parent = self
        if index is None:
            self.children.append(child)
        else:
            self.children.insert(index, child)
        return child

    def detach(self):
        if self.parent is not None:
            self.parent.children.remove(self)
            self.parent = None

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent

    def depth(self):
        return sum(1 for _ in self.ancestors())

    def to_dict(self):
        d = {"id": self.id, "name": self.name}
        if self.code:
            d["code"] = self.code
        if self.info:
            d["info"] = self.info
        if self.disabled:
            d["disabled"] = True
        if self.interaction_id:
            d["interaction"] = self.interaction_id
            d["internum"] = self.internum
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d

    @classmethod
    def from_dict(cls, d):
        s = cls(d["id"], d.get("name", ""), d.get("code", ""), d.get("disabled", False),
                d.get("interaction", ""), d.get("internum", 0))
        s.info = d.get("info", "")
        for cd in d.get("children", []):
            s.add(cls.from_dict(cd))
        return s


class Interaction:
    """One use of a component (a Time Machine frame).

    values holds what the user entered in the interaction pages:
    textbox -> str, listbox -> int index, checkbox -> 0/1.
    """

    def __init__(self, iid, component, values, parent_step_id, goal):
        self.id = iid
        self.component = component
        self.values = dict(values)
        self.parent_step_id = parent_step_id
        self.goal = goal
        now = datetime.datetime.now()
        self.date = now.strftime("%Y-%m-%d")
        self.time = now.strftime("%H:%M:%S")

    def to_dict(self):
        return {"id": self.id, "component": self.component, "values": self.values,
                "parent": self.parent_step_id, "goal": self.goal,
                "date": self.date, "time": self.time}

    @classmethod
    def from_dict(cls, d):
        it = cls(d["id"], d["component"], d.get("values", {}), d.get("parent", ""), d.get("goal", ""))
        it.date = d.get("date", it.date)
        it.time = d.get("time", it.time)
        return it


class Goal:
    def __init__(self, name, root_id):
        self.name = name
        self.root = Step(root_id, START_POINT_NAME)

    def to_dict(self):
        return {"name": self.name, "root": self.root.to_dict()}

    @classmethod
    def from_dict(cls, d):
        g = cls(d["name"], d["root"]["id"])
        g.root = Step.from_dict(d["root"])
        return g


class Project:
    """A visual source file (*.pwct)."""

    def __init__(self, language="Python"):
        self.language = language      # the Visual Programming Language (languages/<id>)
        self.next_id = 1
        self.goals = []
        self.interactions = []
        self.filename = None
        self.modified = False
        self.add_goal("Main")
        self.modified = False

    # ---------------------------------------------------------------- ids
    def new_id(self):
        sid = "%d_" % self.next_id
        self.next_id += 1
        return sid

    # -------------------------------------------------------------- goals
    def add_goal(self, name):
        g = Goal(name, "SP_" + self.new_id())
        self.goals.append(g)
        self.modified = True
        return g

    def goal(self, name):
        for g in self.goals:
            if g.name.lower() == name.lower():
                return g
        return None

    def remove_goal(self, goal):
        ids = {s.interaction_id for s in goal.root.walk() if s.interaction_id}
        self.interactions = [i for i in self.interactions if i.id not in ids]
        self.goals.remove(goal)
        self.modified = True

    def goal_of(self, step):
        root = step
        while root.parent is not None:
            root = root.parent
        for g in self.goals:
            if g.root is root:
                return g
        return None

    # -------------------------------------------------------------- steps
    def find_step(self, sid):
        for g in self.goals:
            for s in g.root.walk():
                if s.id == sid:
                    return s
        return None

    def interaction_steps(self, iid):
        out = []
        for g in self.goals:
            out.extend(s for s in g.root.walk() if s.interaction_id == iid)
        out.sort(key=lambda s: s.internum)
        return out

    def interaction_root(self, iid):
        steps = self.interaction_steps(iid)
        return steps[0] if steps else None

    # ------------------------------------------------------- interactions
    def interaction(self, iid):
        for it in self.interactions:
            if it.id == iid:
                return it
        return None

    def goal_interactions(self, goal):
        used = {s.interaction_id for s in goal.root.walk() if s.interaction_id}
        return [i for i in self.interactions if i.id in used]

    def purge_interactions(self):
        """Delete history records that no longer own any step (like Release in rpwi.scx)."""
        used = set()
        for g in self.goals:
            used.update(s.interaction_id for s in g.root.walk() if s.interaction_id)
        self.interactions = [i for i in self.interactions if i.id in used]

    def component_use_count(self, component_key):
        return sum(1 for i in self.interactions if i.component == component_key)

    # --------------------------------------------------------------- file
    def to_dict(self):
        return {"format": "PyPWCT", "version": VERSION, "language": self.language, "next_id": self.next_id,
                "goals": [g.to_dict() for g in self.goals],
                "interactions": [i.to_dict() for i in self.interactions]}

    def save(self, filename=None):
        if filename:
            self.filename = filename
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=1)
        self.modified = False

    @classmethod
    def load(cls, filename):
        with open(filename, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("format") != "PyPWCT":
            raise ValueError("The file is not valid - Process Canceled")
        p = cls.__new__(cls)
        p.language = d.get("language", "Python")
        p.next_id = d.get("next_id", 1)
        p.goals = [Goal.from_dict(g) for g in d.get("goals", [])]
        p.interactions = [Interaction.from_dict(i) for i in d.get("interactions", [])]
        p.filename = filename
        p.modified = False
        if not p.goals:
            p.add_goal("Main")
        return p
