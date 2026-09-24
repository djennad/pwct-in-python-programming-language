"""VPL rules: step types (StepsColors.prg) and the syntax directed editor
(AvoidErrors.prg / VPLRules.prg)."""

CREATED = 1
GENERATED = 2
ROOT = 3
ALLOW_SUB = 4
LEAF = 5
ALLOW_SUB_LEAF = 6

TYPE_NAMES = {
    CREATED: "Created",
    GENERATED: "Generated",
    ROOT: "Generated (Root)",
    ALLOW_SUB: "Generated (Allow Sub Steps)",
    LEAF: "Generated (Leaf)",
    ALLOW_SUB_LEAF: "Generated (AllowSub & Leaf)",
}


class Rules:
    def __init__(self, project, library, syntax_directed=True):
        self.project = project
        self.library = library
        self.syntax_directed = syntax_directed

    def component_of(self, step):
        if not step.interaction_id:
            return None
        it = self.project.interaction(step.interaction_id)
        return self.library.get(it.component) if it else None

    def is_root(self, step):
        if not step.interaction_id:
            return False
        if step.internum == 1:
            return True
        comp = self.component_of(step)
        return comp is None or comp.allow_root(step.internum)

    def allow_sub(self, step):
        """Can the user add steps (Interact / New Step) under this step?"""
        if step.parent is None or not step.interaction_id or not self.syntax_directed:
            return True
        comp = self.component_of(step)
        return comp is None or comp.allow_interaction(step.internum)

    def step_type(self, step):
        if not step.interaction_id:
            return CREATED
        comp = self.component_of(step)
        t = GENERATED
        if step.internum == 1 or comp is None or comp.allow_root(step.internum):
            t = ROOT
        if comp is None or comp.allow_interaction(step.internum):
            t = ALLOW_SUB if step.children else ALLOW_SUB_LEAF
        if t == GENERATED and not step.children:
            t = LEAF
        return t

    def locked(self, step):
        """Generated steps that are not roots can't be moved/deleted/ignored."""
        return (self.syntax_directed and step.interaction_id != ""
                and step.internum != 1 and not self.is_root(step))

    def component_allowed(self, component, parent):
        """Rules checked before using a component under the parent step:
        requires_ancestor (ALLOWPARENT) : a parent component is needed (Break in a loop...)
        requires_step                   : a parent step is needed (a C function in "Functions")
        allow (ALLOW) of the parent     : the parent step accepts only some components
        """
        if not self.syntax_directed:
            return True
        # ALLOW: the nearest generated step decides which components are accepted
        s = parent
        while s is not None and s.parent is not None and not s.interaction_id:
            s = s.parent
        if s is not None and s.interaction_id:
            comp = self.component_of(s)
            only = comp.allowed_under(s.internum) if comp is not None else None
            if only is not None and component.name.lower() not in [n.lower() for n in only]:
                return False
        need = [n.lower() for n in component.requires_ancestor]
        if need and not any(c is not None and c.name.lower() in need
                            for c in (self.component_of(x) for x in _self_and_ancestors(parent))):
            return False
        steps = [n.lower() for n in component.rules.get("requires_step", [])]
        if steps and not any(x.name.lower() in steps for x in _self_and_ancestors(parent)):
            return False
        return True


def _self_and_ancestors(step):
    s = step
    while s is not None:
        yield s
        s = s.parent
