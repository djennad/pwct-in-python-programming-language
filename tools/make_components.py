"""Build the standard PythonPWCT components (languages/Python/components/*.json).

Each component = interaction page(s) + code mask + rules, like the PWCT
transporter files.  Run:  python tools/make_components.py
"""

import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
LANG_DIR = os.path.join(os.path.dirname(HERE), "languages", "Python")
OUT = os.path.join(LANG_DIR, "components")

PY_KEYWORDS = ("False None True and as assert async await break class continue def del elif else except "
               "finally for from global if import in is lambda nonlocal not or pass raise return try while "
               "with yield print input range len str int float")
LANGUAGE = {
    "name": "PythonPWCT", "title": "Python", "extension": ".py", "comment": "#", "indent": "    ",
    "empty_block": "pass", "prelude": "", "build": [], "run": ['"{python}" "{file}"'], "check": [],
    "keywords": PY_KEYWORDS, "syntax": "python", "start": "",
    "description": "Python 3 - the same Python that runs PyPWCT (Tkinter for the GUI)",
}

PAGE_W = 620
LABEL_X, LABEL_W = 20, 190
CTRL_X, CTRL_W = 215, 380
ROW_H = 38
TOP = 64

DOMAINS = [
    ("General", "#404040"),
    ("Variables", "#1f6f8b"),
    ("Input and Output", "#2e7d32"),
    ("Control Structure", "#400040"),
    ("Functions", "#b71c1c"),
    ("Classes", "#ad1457"),
    ("Data Structures", "#00838f"),
    ("Strings", "#e65100"),
    ("Math", "#283593"),
    ("Files", "#5d4037"),
    ("GUI (Tkinter)", "#0277bd"),
    ("System", "#455a64"),
]
COLORS = dict(DOMAINS)


# ------------------------------------------------------------ field specs

def T(var, title, text="", kind="any", escape=False, allow_empty=False, focus=False, w=None):
    return {"type": "textbox", "var": var, "title": title, "text": text, "kind": kind,
            "escape": escape, "allow_empty": allow_empty, "focus": focus, "_w": w}


def L(var, title, items, values=None, selected=0, mode="item"):
    c = {"type": "listbox", "var": var, "title": title, "items": items, "selected": selected, "mode": mode}
    if values:
        c["values"] = values
    return c


def C(var, title, caption, value=0):
    return {"type": "checkbox", "var": var, "title": title, "caption": caption, "value": value}


def layout(name, domain, fields, note=None, color=None):
    color = color or COLORS.get(domain, "#400040")
    controls = [{"type": "label", "x": 0, "y": 0, "w": PAGE_W, "h": 44, "caption": "  " + name,
                 "fg": "#ffffff", "bg": color, "font": ["Arial", 14, "bold"]}]
    y = TOP
    first_text = True
    for f in fields:
        f = dict(f)
        w = f.pop("_w", None) or CTRL_W
        if f["type"] != "checkbox":
            controls.append({"type": "label", "x": LABEL_X, "y": y + 3, "w": LABEL_W, "h": 22,
                             "caption": f["title"] + " :", "fg": "#000000", "bg": "",
                             "font": ["Arial", 10, "bold"]})
        if f["type"] == "textbox":
            if first_text:
                f["focus"] = True
                first_text = False
            h = 26
        elif f["type"] == "listbox":
            h = 22 * min(len(f["items"]), 6) + 6
        else:
            h = 26
            f["fg"] = "#000000"
            f["bg"] = ""
            f["font"] = ["Arial", 10, "bold"]
        f.update({"x": CTRL_X if f["type"] != "checkbox" else LABEL_X, "y": y, "w": w, "h": h})
        if f["type"] == "textbox":
            f.update({"fg": "#000080", "bg": "#ffffff", "font": ["Consolas", 11]})
            for k in ("escape", "allow_empty", "focus"):
                if not f[k]:
                    del f[k]
        if f["type"] == "listbox":
            f.update({"fg": "#000000", "bg": "#ffffff", "font": ["Arial", 10]})
        controls.append(f)
        y += max(ROW_H, h + 12)
    if note:
        controls.append({"type": "label", "x": LABEL_X, "y": y + 4, "w": PAGE_W - 40, "h": 40,
                         "caption": note, "fg": "#606060", "bg": "", "font": ["Arial", 9, "italic"]})
        y += 44
    return [{"name": name, "bgcolor": "#ffffff", "width": PAGE_W, "height": y + 16, "controls": controls}]


COMPONENTS = []


def comp(domain, name, fields, mask, desc, allow_interaction=(), allow_root=(1,), requires=(), note=None,
         extra_pages=(), designer=None):
    """extra_pages: [(page name, fields)] - designer: Form Designer mapping (see pwct/forms.py)."""
    pages = layout(name, domain, fields, note)
    for pname, pfields in extra_pages:
        page = layout(name + " - " + pname, domain, pfields)[0]
        page["name"] = pname
        pages.append(page)
    data = {
        "name": name,
        "description": desc,
        "order": len(COMPONENTS),
        "pages": pages,
        "mask": mask.strip("\n"),
        "rules": {"allow_root": list(allow_root), "allow_interaction": list(allow_interaction),
                  "requires_ancestor": list(requires)},
    }
    if designer:
        data["designer"] = designer
    COMPONENTS.append({"domain": domain, "data": data})


def block(open_code, step, end_step, extra=""):
    """Mask of a simple block: root step + Start Here + End."""
    return """
<RPWI:NEWSTEP> %s
%s
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
%s
<RPWI:NEWSTEP> %s
<RPWI:TABPOP>
""" % (step, open_code, extra, end_step)


LOOPS = ["While Loop", "For Loop", "For Each"]
FUNCS = ["Define Function", "Define Method", "Constructor"]

# ================================================================ General
comp("General", "Python Code",
     [T("code", "Code", "", kind="stmt")],
     """
<RPWI:NEWSTEP> Python Code : #{code}
#{code}
""", "Write one line of Python code directly (for experts).")

comp("General", "Comment",
     [T("text", "Comment", "")],
     """
<RPWI:NEWSTEP> Comment : #{text}
# #{text}
""", "Add a comment line to the generated source code.")

comp("General", "Import Module",
     [T("module", "Module", "math", kind="module"),
      T("alias", "Import as (optional)", "", kind="name", allow_empty=True)],
     """
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{alias}
  <RPWI:NEWSTEP> Import Module #{module}
  import #{module}
<RPWI:ENDTEST>
<RPWI:NEGATIVE>
<RPWI:TEST> #{alias}
  <RPWI:NEWSTEP> Import Module #{module} as #{alias}
  import #{module} as #{alias}
<RPWI:ENDTEST>
""", "Import a Python module (math, random, os, ...).", allow_root=(1, 2))

comp("General", "From Module Import",
     [T("module", "Module", "math", kind="module"),
      T("names", "Import names", "sqrt, pi")],
     """
<RPWI:NEWSTEP> From #{module} Import #{names}
from #{module} import #{names}
""", "Import names from a module.")

comp("General", "Pass (Do Nothing)",
     [],
     """
<RPWI:NEWSTEP> Pass (Do Nothing)
pass
""", "An empty statement.")

comp("General", "Main Program Block",
     [],
     block('if __name__ == "__main__":', "Main Program", "End of Main Program"),
     "The main block of the program (runs when the file is executed directly).",
     allow_interaction=(2,))

# ============================================================== Variables
comp("Variables", "Assignment",
     [T("var", "Variable", "x", kind="target"),
      T("value", "Value (Expression)", "0", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = #{value}
#{var} = #{value}
""", "Set the value of a variable using an expression.")

comp("Variables", "Assignment (Text)",
     [T("var", "Variable", "name", kind="target"),
      T("text", "Text", "", escape=True, allow_empty=True)],
     """
<RPWI:NEWSTEP> #{var} = "#{text:item}"
#{var} = "#{text}"
""", "Set a variable to a text value (no need to write quotes).")

comp("Variables", "Increment / Decrement",
     [T("var", "Variable", "x", kind="target"),
      L("op", "Operation", ["Increment (+)", "Decrement (-)", "Multiply (*)", "Divide (/)"],
        ["+=", "-=", "*=", "/="]),
      T("value", "By", "1", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} #{op} #{value}
#{var} #{op} #{value}
""", "Change the value of a variable.")

comp("Variables", "Type Conversion",
     [T("var", "Variable", "x", kind="target"),
      L("func", "Convert to", ["Integer", "Float", "String", "Boolean"], ["int", "float", "str", "bool"]),
      T("value", "Value", "x", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = #{func}(#{value})
#{var} = #{func}(#{value})
""", "Convert a value to another type.")

comp("Variables", "Swap Variables",
     [T("a", "First variable", "a", kind="target"),
      T("b", "Second variable", "b", kind="target")],
     """
<RPWI:NEWSTEP> Swap #{a} , #{b}
#{a}, #{b} = #{b}, #{a}
""", "Swap the values of two variables.")

comp("Variables", "Global Variables",
     [T("names", "Variables", "x", kind="params")],
     """
<RPWI:NEWSTEP> Global #{names}
global #{names}
""", "Use global variables inside a function.", requires=FUNCS)

# ======================================================= Input and Output
comp("Input and Output", "Print Text",
     [T("text", "Text", "Hello, World!", escape=True, allow_empty=True)],
     """
<RPWI:NEWSTEP> Print : #{text:item}
print("#{text}")
""", "Print a text message on the screen.")

comp("Input and Output", "Print Expression",
     [T("value", "Expression", "x", kind="args")],
     """
<RPWI:NEWSTEP> Print : #{value}
print(#{value})
""", "Print the value of variables or expressions (separate them with commas).")

comp("Input and Output", "Print Text and Value",
     [T("text", "Text", "The result is :", escape=True),
      T("value", "Expression", "x", kind="expr")],
     """
<RPWI:NEWSTEP> Print : #{text:item} #{value}
print("#{text}", #{value})
""", "Print a message followed by a value.")

comp("Input and Output", "Print New Line",
     [],
     """
<RPWI:NEWSTEP> Print New Line
print()
""", "Print an empty line.")

comp("Input and Output", "Input",
     [T("var", "Variable", "x", kind="target"),
      T("prompt", "Message", "Enter a value : ", escape=True, allow_empty=True),
      L("type", "Data type", ["Text (String)", "Integer Number", "Float Number"], ["str", "int", "float"])],
     """
<RPWI:NEWSTEP> #{var} = Input #{type:item} : #{prompt:item}
#{var} = #{type}(input("#{prompt}"))
""", "Get a value from the user (keyboard).")

comp("Input and Output", "Wait for Enter Key",
     [T("text", "Message", "Press Enter to continue...", escape=True, allow_empty=True)],
     """
<RPWI:NEWSTEP> Wait : #{text:item}
input("#{text}")
""", "Wait until the user presses Enter.")

# ====================================================== Control Structure
comp("Control Structure", "If Statement",
     [T("cond", "Condition", "x > 0", kind="expr"),
      T("elif1", "Else If (optional)", "", kind="expr", allow_empty=True),
      T("elif2", "Else If (optional)", "", kind="expr", allow_empty=True),
      T("elif3", "Else If (optional)", "", kind="expr", allow_empty=True),
      C("else", "Else", "Add Else branch")],
     """
<RPWI:NEWSTEP> If #{cond}
if #{cond}:
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:VALUE>
<RPWI:TEST> #{elif1}
  <RPWI:NEWSTEP> Else If #{elif1}
  <RPWI:TABPOP>
  elif #{elif1}:
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:TEST> #{elif2}
  <RPWI:NEWSTEP> Else If #{elif2}
  <RPWI:TABPOP>
  elif #{elif2}:
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:TEST> #{elif3}
  <RPWI:NEWSTEP> Else If #{elif3}
  <RPWI:TABPOP>
  elif #{elif3}:
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:VALUE> 0
<RPWI:TEST> #{else}
  <RPWI:NEWSTEP> Else
  <RPWI:TABPOP>
  else:
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:NEWSTEP> End of If
<RPWI:TABPOP>
""", "Execute steps when a condition is true (with optional Else If / Else).",
     allow_interaction=(2, 3, 4, 5, 6))

comp("Control Structure", "While Loop",
     [T("cond", "Condition", "x < 10", kind="expr")],
     block("while #{cond}:", "While #{cond}", "End of While"),
     "Repeat steps while a condition is true.", allow_interaction=(2,))

comp("Control Structure", "For Loop",
     [T("var", "Variable", "x", kind="name"),
      T("start", "From", "1", kind="expr"),
      T("end", "To", "10", kind="expr"),
      T("step", "Step", "1", kind="expr")],
     block("for #{var} in range(#{start}, (#{end}) + (1 if (#{step}) > 0 else -1), #{step}):",
           "For #{var} = #{start} To #{end} Step #{step}", "Next"),
     "Repeat steps for a counter from a start value to an end value.", allow_interaction=(2,))

comp("Control Structure", "For Each",
     [T("var", "Item variable", "item", kind="target"),
      T("seq", "In (List/Text/...)", "mylist", kind="expr")],
     block("for #{var} in #{seq}:", "For Each #{var} In #{seq}", "End of For Each"),
     "Repeat steps for each item in a list, text, dictionary...", allow_interaction=(2,))

comp("Control Structure", "Exit Loop (Break)",
     [],
     """
<RPWI:NEWSTEP> Exit Loop
break
""", "Exit from the current loop.", requires=LOOPS)

comp("Control Structure", "Loop (Continue)",
     [],
     """
<RPWI:NEWSTEP> Loop (Continue)
continue
""", "Skip to the next iteration of the loop.", requires=LOOPS)

comp("Control Structure", "Try / Catch Errors",
     [T("exc", "Error type", "Exception", kind="expr"),
      T("var", "Error variable", "error", kind="name"),
      C("fin", "Finally", "Add Finally branch (always executed)")],
     """
<RPWI:NEWSTEP> Try
try:
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> Catch #{exc} as #{var}
<RPWI:TABPOP>
except #{exc} as #{var}:
<RPWI:TABPUSH>
<RPWI:TEST> #{fin}
  <RPWI:NEWSTEP> Finally
  <RPWI:TABPOP>
  finally:
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:NEWSTEP> End of Try
<RPWI:TABPOP>
""", "Execute steps and catch the errors.", allow_interaction=(2, 3, 4))

comp("Control Structure", "Raise Error",
     [T("exc", "Error", 'ValueError("Invalid value")', kind="expr")],
     """
<RPWI:NEWSTEP> Raise Error #{exc}
raise #{exc}
""", "Raise an error (exception).")

# ============================================================== Functions
comp("Functions", "Define Function",
     [T("name", "Function name", "myfunction", kind="name"),
      T("params", "Parameters", "", kind="params", allow_empty=True)],
     """
<RPWI:NEWSTEP> Function #{name} (#{params})
def #{name}(#{params}):
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> End of Function
<RPWI:TABPOP>
<pwct:newline>
""", "Define a new function (procedure).", allow_interaction=(2,))

comp("Functions", "Return",
     [T("value", "Value", "", kind="expr", allow_empty=True)],
     """
<RPWI:NEWSTEP> Return #{value}
return #{value}
""", "Return from the function (with an optional value).", requires=FUNCS)

comp("Functions", "Call Function",
     [T("name", "Function", "myfunction", kind="expr"),
      T("args", "Parameters", "", kind="args", allow_empty=True),
      T("result", "Result variable (optional)", "", kind="target", allow_empty=True)],
     """
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{result}
  <RPWI:NEWSTEP> Call #{name}(#{args})
  #{name}(#{args})
<RPWI:ENDTEST>
<RPWI:NEGATIVE>
<RPWI:TEST> #{result}
  <RPWI:NEWSTEP> #{result} = Call #{name}(#{args})
  #{result} = #{name}(#{args})
<RPWI:ENDTEST>
""", "Call a function (or a method like obj.method).", allow_root=(1, 2))

# ================================================================ Classes
comp("Classes", "Define Class",
     [T("name", "Class name", "MyClass", kind="name"),
      T("parent", "Parent class (optional)", "", kind="args", allow_empty=True)],
     """
<RPWI:NEWSTEP> Class #{name} (#{parent})
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{parent}
  class #{name}:
<RPWI:ENDTEST>
<RPWI:NEGATIVE>
<RPWI:TEST> #{parent}
  class #{name}(#{parent}):
<RPWI:ENDTEST>
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> End of Class
<RPWI:TABPOP>
<pwct:newline>
""", "Define a new class (Object Oriented Programming).", allow_interaction=(2,))

comp("Classes", "Constructor",
     [T("params", "Parameters", "", kind="params", allow_empty=True)],
     """
<RPWI:NEWSTEP> Constructor (#{params})
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{params}
  def __init__(self):
<RPWI:ENDTEST>
<RPWI:NEGATIVE>
<RPWI:TEST> #{params}
  def __init__(self, #{params}):
<RPWI:ENDTEST>
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> End of Constructor
<RPWI:TABPOP>
""", "The method that is called when a new object is created.", allow_interaction=(2,),
     requires=["Define Class"])

comp("Classes", "Define Method",
     [T("name", "Method name", "mymethod", kind="name"),
      T("params", "Parameters", "", kind="params", allow_empty=True)],
     """
<RPWI:NEWSTEP> Method #{name} (#{params})
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{params}
  def #{name}(self):
<RPWI:ENDTEST>
<RPWI:NEGATIVE>
<RPWI:TEST> #{params}
  def #{name}(self, #{params}):
<RPWI:ENDTEST>
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> End of Method
<RPWI:TABPOP>
""", "Define a method inside a class.", allow_interaction=(2,), requires=["Define Class"])

comp("Classes", "Set Attribute",
     [T("attr", "Attribute", "name", kind="name"),
      T("value", "Value", "None", kind="expr")],
     """
<RPWI:NEWSTEP> self.#{attr} = #{value}
self.#{attr} = #{value}
""", "Set an attribute of the current object (self).", requires=FUNCS)

comp("Classes", "Create Object",
     [T("var", "Object variable", "obj", kind="target"),
      T("cls", "Class", "MyClass", kind="expr"),
      T("args", "Parameters", "", kind="args", allow_empty=True)],
     """
<RPWI:NEWSTEP> #{var} = New #{cls}(#{args})
#{var} = #{cls}(#{args})
""", "Create a new object from a class.")

# ======================================================== Data Structures
comp("Data Structures", "Create List",
     [T("var", "List variable", "mylist", kind="target"),
      T("items", "Items", "1, 2, 3", kind="args", allow_empty=True)],
     """
<RPWI:NEWSTEP> #{var} = List [#{items}]
#{var} = [#{items}]
""", "Create a new list.")

comp("Data Structures", "Add Item to List",
     [T("list", "List", "mylist", kind="expr"),
      T("value", "Item", "0", kind="expr")],
     """
<RPWI:NEWSTEP> Add #{value} to #{list}
#{list}.append(#{value})
""", "Add an item at the end of a list.")

comp("Data Structures", "Remove Item from List",
     [T("list", "List", "mylist", kind="expr"),
      T("value", "Item", "0", kind="expr")],
     """
<RPWI:NEWSTEP> Remove #{value} from #{list}
#{list}.remove(#{value})
""", "Remove an item from a list.")

comp("Data Structures", "Sort List",
     [T("list", "List", "mylist", kind="expr"),
      L("order", "Order", ["Ascending", "Descending"], ["False", "True"])],
     """
<RPWI:NEWSTEP> Sort #{list} #{order:item}
#{list}.sort(reverse=#{order})
""", "Sort the items of a list.")

comp("Data Structures", "Create Dictionary",
     [T("var", "Dictionary variable", "mydict", kind="target")],
     """
<RPWI:NEWSTEP> #{var} = New Dictionary
#{var} = {}
""", "Create a new empty dictionary (key/value table).")

comp("Data Structures", "Dictionary Set Item",
     [T("dict", "Dictionary", "mydict", kind="expr"),
      T("key", "Key", '"name"', kind="expr"),
      T("value", "Value", "0", kind="expr")],
     """
<RPWI:NEWSTEP> #{dict}[#{key}] = #{value}
#{dict}[#{key}] = #{value}
""", "Set the value of a key in a dictionary.")

comp("Data Structures", "Get Length",
     [T("var", "Variable", "n", kind="target"),
      T("obj", "List/Text/Dictionary", "mylist", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = Length of #{obj}
#{var} = len(#{obj})
""", "Get the number of items (or letters).")

# ================================================================ Strings
comp("Strings", "Text Operation",
     [T("var", "Result variable", "result", kind="target"),
      T("text", "Text", "name", kind="expr"),
      L("op", "Operation", ["Upper Case", "Lower Case", "Title Case", "Remove Spaces (Trim)", "Reverse"],
        [".upper()", ".lower()", ".title()", ".strip()", "[::-1]"])],
     """
<RPWI:NEWSTEP> #{var} = #{op:item} (#{text})
#{var} = (#{text})#{op}
""", "Change the letters of a text.")

comp("Strings", "Concatenate",
     [T("var", "Result variable", "result", kind="target"),
      T("a", "First", "a", kind="expr"),
      T("b", "Second", "b", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = #{a} + #{b}
#{var} = str(#{a}) + str(#{b})
""", "Join two values as text.")

comp("Strings", "Replace Text",
     [T("var", "Result variable", "result", kind="target"),
      T("text", "Text", "mytext", kind="expr"),
      T("old", "Find", "", escape=True),
      T("new", "Replace with", "", escape=True, allow_empty=True)],
     """
<RPWI:NEWSTEP> #{var} = Replace "#{old:item}" with "#{new:item}" in #{text}
#{var} = (#{text}).replace("#{old}", "#{new}")
""", "Replace a part of a text.")

comp("Strings", "Split Text",
     [T("var", "Result list", "words", kind="target"),
      T("text", "Text", "mytext", kind="expr"),
      T("sep", "Separator (empty = spaces)", "", escape=True, allow_empty=True)],
     """
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{sep}
  <RPWI:NEWSTEP> #{var} = Split #{text}
  #{var} = (#{text}).split()
<RPWI:ENDTEST>
<RPWI:NEGATIVE>
<RPWI:TEST> #{sep}
  <RPWI:NEWSTEP> #{var} = Split #{text} by "#{sep:item}"
  #{var} = (#{text}).split("#{sep}")
<RPWI:ENDTEST>
""", "Split a text into a list of words.", allow_root=(1, 2))

comp("Strings", "Format Text",
     [T("var", "Result variable", "msg", kind="target"),
      T("template", "Template", "Hello {name}", escape=True)],
     """
<RPWI:NEWSTEP> #{var} = Format "#{template:item}"
#{var} = f"#{template}"
""", "Build a text using variables between { }.")

# =================================================================== Math
comp("Math", "Arithmetic Operation",
     [T("var", "Result variable", "result", kind="target"),
      T("a", "First value", "a", kind="expr"),
      L("op", "Operation", ["+  Add", "-  Subtract", "*  Multiply", "/  Divide", "// Integer Divide",
                            "%  Remainder", "** Power"], ["+", "-", "*", "/", "//", "%", "**"]),
      T("b", "Second value", "b", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = #{a} #{op} #{b}
#{var} = #{a} #{op} #{b}
""", "Calculate the result of two values.")

comp("Math", "Math Function",
     [T("var", "Result variable", "result", kind="target"),
      L("func", "Function", ["Square Root", "Power (x, y)", "Absolute", "Round", "Floor", "Ceil",
                             "Sine", "Cosine", "Tangent", "Logarithm", "Minimum", "Maximum"],
        ["math.sqrt", "math.pow", "abs", "round", "math.floor", "math.ceil",
         "math.sin", "math.cos", "math.tan", "math.log", "min", "max"]),
      T("args", "Value(s)", "x", kind="args")],
     """
<RPWI:NEWSTEP> #{var} = #{func:item} (#{args})
import math
#{var} = #{func}(#{args})
""", "Use a mathematical function.")

comp("Math", "Random Number",
     [T("var", "Variable", "number", kind="target"),
      T("start", "From", "1", kind="expr"),
      T("end", "To", "100", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = Random Number (#{start} To #{end})
import random
#{var} = random.randint(#{start}, #{end})
""", "Get a random integer number.")

# ================================================================== Files
comp("Files", "Write to File",
     [T("file", "File name", "myfile.txt", escape=True),
      T("content", "Content", "text", kind="expr"),
      L("mode", "Mode", ["Write (replace the file)", "Append (add to the end)"], ["w", "a"])],
     """
<RPWI:NEWSTEP> Write #{content} to file "#{file:item}"
with open("#{file}", "#{mode}", encoding="utf-8") as _pwct_file:
<RPWI:TABPUSH>
_pwct_file.write(str(#{content}))
<RPWI:TABPOP>
""", "Write a text to a file.")

comp("Files", "Read File",
     [T("var", "Variable", "content", kind="target"),
      T("file", "File name", "myfile.txt", escape=True),
      L("how", "Read as", ["Text", "List of lines"], [".read()", ".read().splitlines()"])],
     """
<RPWI:NEWSTEP> #{var} = Read file "#{file:item}" as #{how:item}
with open("#{file}", "r", encoding="utf-8") as _pwct_file:
<RPWI:TABPUSH>
#{var} = _pwct_file#{how}
<RPWI:TABPOP>
""", "Read the content of a file.")

comp("Files", "File Exists",
     [T("var", "Variable", "found", kind="target"),
      T("file", "File name", "myfile.txt", escape=True)],
     """
<RPWI:NEWSTEP> #{var} = File Exists "#{file:item}"
import os
#{var} = os.path.exists("#{file}")
""", "Check if a file exists (True/False).")

comp("Files", "Delete File",
     [T("file", "File name", "myfile.txt", escape=True)],
     """
<RPWI:NEWSTEP> Delete file "#{file:item}"
import os
os.remove("#{file}")
""", "Delete a file from the disk.")

# ========================================================== GUI (Tkinter)
comp("GUI (Tkinter)", "Create Window",
     [T("name", "Window name", "win<autonumber>", kind="name"),
      T("title", "Title", "My Application", escape=True),
      T("width", "Width", "400", kind="expr"),
      T("height", "Height", "300", kind="expr"),
      T("bg", "Back color", "white", escape=True),
      C("show", "Show", "Show the window at the end (mainloop)", 1)],
     """
<RPWI:NEWSTEP> Window #{name} : #{title:item}
import tkinter as tk
#{name} = tk.Tk()
#{name}.title("#{title}")
#{name}.geometry(str(#{width}) + "x" + str(#{height}))
#{name}.configure(bg="#{bg}")
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> End of Window #{name}
<RPWI:VALUE> 0
<RPWI:NEGATIVE>
<RPWI:TEST> #{show}
  #{name}.mainloop()
<RPWI:ENDTEST>
""", "Create a new window: put its controls in Start Here. The window is shown at End of Window (mainloop). "
     "Design it with the Form Designer (Ctrl+F).", allow_interaction=(2,),
     note="The controls go in (Start Here). Tip : design the window with the Form Designer (Ctrl+F).",
     designer={"type": "window", "container": 2,
               "props": {"name": "name", "title": "title", "w": "width", "h": "height", "bg": "bg",
                         "show": "show"}})


def gui_style():
    """Colors + position/size of a GUI control (Width/Height are optional)."""
    return """
<RPWI:VALUE>
<RPWI:NEGATIVE>
<RPWI:TEST> #{fg}
  #{name}.config(fg="#{fg}")
<RPWI:ENDTEST>
<RPWI:TEST> #{bg}
  #{name}.config(bg="#{bg}")
<RPWI:ENDTEST>
#{name}.place(x=#{x}, y=#{y})
<RPWI:TEST> #{w}
  #{name}.place_configure(width=#{w})
<RPWI:ENDTEST>
<RPWI:TEST> #{h}
  #{name}.place_configure(height=#{h})
<RPWI:ENDTEST>
"""


def appearance(size, w="", h=""):
    return [("Appearance", [
        T("w", "Width (pixels, optional)", w, kind="expr", allow_empty=True),
        T("h", "Height (pixels, optional)", h, kind="expr", allow_empty=True),
        T("size", "Font size", size, kind="expr"),
        T("fg", "Text color (optional)", "", escape=True, allow_empty=True),
        T("bg", "Back color (optional)", "", escape=True, allow_empty=True)])]


def gui_designer(kind, **extra):
    props = {"name": "name", "window": "win", "x": "x", "y": "y", "w": "w", "h": "h", "size": "size",
             "fg": "fg", "bg": "bg"}
    props.update(extra)
    return {"type": kind, "props": props}


def gui_place(name, default, x, y):
    return [T("name", name, default + "<autonumber>", kind="name"), T("win", "Window", "win1", kind="expr"),
            T("x", "Left (x)", x, kind="expr"), T("y", "Top (y)", y, kind="expr")]


GUI_NOTE = "Tip : design the window visually with the Form Designer (Ctrl+F)."

comp("GUI (Tkinter)", "Label",
     [T("name", "Label name", "label<autonumber>", kind="name"),
      T("win", "Window", "win1", kind="expr"),
      T("text", "Text", "Hello", escape=True, allow_empty=True),
      T("x", "Left (x)", "20", kind="expr"),
      T("y", "Top (y)", "20", kind="expr")],
     """
<RPWI:NEWSTEP> Label #{name} : #{text:item}
#{name} = tk.Label(#{win}, text="#{text}", font=("Arial", #{size}))
""" + gui_style(), "Add a label (text) to a window.", note=GUI_NOTE,
     extra_pages=appearance("12"), designer=gui_designer("label", text="text"))

comp("GUI (Tkinter)", "Button",
     [T("name", "Button name", "button<autonumber>", kind="name"),
      T("win", "Window", "win1", kind="expr"),
      T("text", "Caption", "OK", escape=True),
      T("x", "Left (x)", "20", kind="expr"),
      T("y", "Top (y)", "60", kind="expr"),
      T("cmd", "Function to call (optional)", "", kind="expr", allow_empty=True)],
     """
<RPWI:NEWSTEP> Button #{name} : #{text:item}
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{cmd}
  #{name} = tk.Button(#{win}, text="#{text}", font=("Arial", #{size}))
<RPWI:ENDTEST>
<RPWI:NEGATIVE>
<RPWI:TEST> #{cmd}
  #{name} = tk.Button(#{win}, text="#{text}", font=("Arial", #{size}), command=#{cmd})
<RPWI:ENDTEST>
""" + gui_style(), "Add a button. Define the function before the button.", note=GUI_NOTE,
     extra_pages=appearance("10"), designer=gui_designer("button", text="text", command="cmd"))

comp("GUI (Tkinter)", "Text Box",
     [T("name", "Text box name", "text<autonumber>", kind="name"),
      T("win", "Window", "win1", kind="expr"),
      T("x", "Left (x)", "20", kind="expr"),
      T("y", "Top (y)", "100", kind="expr"),
      T("width", "Width (letters)", "20", kind="expr")],
     """
<RPWI:NEWSTEP> Text Box #{name}
#{name} = tk.Entry(#{win}, width=#{width}, font=("Arial", #{size}))
""" + gui_style(), "Add a text box (Entry) to get text from the user.", note=GUI_NOTE,
     extra_pages=appearance("11"), designer=gui_designer("textbox"))

comp("GUI (Tkinter)", "Text Area",
     gui_place("Text area name", "area", "20", "140"),
     """
<RPWI:NEWSTEP> Text Area #{name}
#{name} = tk.Text(#{win}, font=("Arial", #{size}))
""" + gui_style(), "Add a multi-line text area.", note=GUI_NOTE,
     extra_pages=appearance("11", "200", "100"), designer=gui_designer("textarea"))

comp("GUI (Tkinter)", "Check Box",
     gui_place("Check box name", "check", "20", "140") + [
         T("text", "Caption", "Option", escape=True, allow_empty=True),
         C("checked", "Checked", "Checked at start")],
     """
<RPWI:NEWSTEP> Check Box #{name} : #{text:item}
#{name}_value = tk.IntVar(value=#{checked})
#{name} = tk.Checkbutton(#{win}, text="#{text}", variable=#{name}_value, font=("Arial", #{size}))
""" + gui_style(), "Add a check box. Its value (0/1) is in the variable <name>_value.", note=GUI_NOTE,
     extra_pages=appearance("10"), designer=gui_designer("checkbox", text="text"))

comp("GUI (Tkinter)", "List Box",
     gui_place("List box name", "list", "20", "140") + [
         T("items", "Items", '"One", "Two", "Three"', kind="args", allow_empty=True)],
     """
<RPWI:NEWSTEP> List Box #{name}
#{name} = tk.Listbox(#{win}, font=("Arial", #{size}), exportselection=False)
<RPWI:VALUE>
<RPWI:NEGATIVE>
<RPWI:TEST> #{items}
  for _pwct_item in [#{items}]:
  <RPWI:TABPUSH>
  #{name}.insert(tk.END, _pwct_item)
  <RPWI:TABPOP>
<RPWI:ENDTEST>
""" + gui_style(), "Add a list box.", note=GUI_NOTE,
     extra_pages=appearance("11", "150", "100"), designer=gui_designer("listbox", items="items"))

comp("GUI (Tkinter)", "Get Text Box Value",
     [T("var", "Variable", "value", kind="target"),
      T("box", "Text box", "text1", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = Value of #{box}
#{var} = #{box}.get()
""", "Get the text written in a text box.")

comp("GUI (Tkinter)", "Set Text Box Value",
     [T("box", "Text box", "text1", kind="expr"),
      T("value", "Value", '""', kind="expr")],
     """
<RPWI:NEWSTEP> Set #{box} = #{value}
#{box}.delete(0, tk.END)
#{box}.insert(0, str(#{value}))
""", "Change the text of a text box.")

comp("GUI (Tkinter)", "Set Label Text",
     [T("label", "Label", "label1", kind="expr"),
      T("value", "Value", '"Hello"', kind="expr")],
     """
<RPWI:NEWSTEP> Set #{label} text = #{value}
#{label}.config(text=str(#{value}))
""", "Change the text of a label.")

comp("GUI (Tkinter)", "Message Box",
     [L("kind", "Type", ["Information", "Warning", "Error"], ["showinfo", "showwarning", "showerror"]),
      T("title", "Title", "Message", escape=True),
      T("msg", "Message", '"Hello"', kind="expr")],
     """
<RPWI:NEWSTEP> Message Box (#{kind:item}) : #{msg}
from tkinter import messagebox
messagebox.#{kind}("#{title}", str(#{msg}))
""", "Show a message box.")

comp("GUI (Tkinter)", "Get Check Box Value",
     [T("var", "Variable", "checked", kind="target"),
      T("box", "Check box", "check1", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = Value of #{box} (0/1)
#{var} = #{box}_value.get()
""", "Get the value of a check box (1 = checked).")

comp("GUI (Tkinter)", "Get List Box Selection",
     [T("var", "Variable", "item", kind="target"),
      T("box", "List box", "list1", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = Selected item of #{box}
#{var} = #{box}.get(#{box}.curselection()[0]) if #{box}.curselection() else ""
""", "Get the text of the selected item (empty if nothing is selected).")

comp("GUI (Tkinter)", "Add Item to List Box",
     [T("box", "List box", "list1", kind="expr"),
      T("value", "Item", '"New item"', kind="expr")],
     """
<RPWI:NEWSTEP> Add #{value} to #{box}
#{box}.insert(tk.END, #{value})
""", "Add an item at the end of a list box.")

comp("GUI (Tkinter)", "Get Text Area Value",
     [T("var", "Variable", "text", kind="target"),
      T("area", "Text area", "area1", kind="expr")],
     """
<RPWI:NEWSTEP> #{var} = Text of #{area}
#{var} = #{area}.get("1.0", "end-1c")
""", "Get the text written in a text area.")

comp("GUI (Tkinter)", "Set Text Area Value",
     [T("area", "Text area", "area1", kind="expr"),
      T("value", "Value", '""', kind="expr")],
     """
<RPWI:NEWSTEP> Set #{area} text = #{value}
#{area}.delete("1.0", tk.END)
#{area}.insert("1.0", str(#{value}))
""", "Change the text of a text area.")

comp("GUI (Tkinter)", "Start Event Loop",
     [T("win", "Window", "win1", kind="expr")],
     """
<RPWI:NEWSTEP> Show Window #{win} (Event Loop)
#{win}.mainloop()
""", "Show the window and wait for the user events. Not needed when (Show the window) is checked in "
     "Create Window.", designer={"type": "eventloop", "props": {"window": "win"}})

comp("GUI (Tkinter)", "Close Window",
     [T("win", "Window", "win1", kind="expr")],
     """
<RPWI:NEWSTEP> Close Window #{win}
#{win}.destroy()
""", "Close a window.")

# ================================================================= System
comp("System", "Sleep (Wait)",
     [T("sec", "Seconds", "1", kind="expr")],
     """
<RPWI:NEWSTEP> Sleep #{sec} second(s)
import time
time.sleep(#{sec})
""", "Wait for some seconds.")

comp("System", "Date and Time",
     [T("var", "Variable", "now", kind="target"),
      L("fmt", "Get", ["Date and Time", "Date", "Time"], ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%H:%M:%S"])],
     """
<RPWI:NEWSTEP> #{var} = Current #{fmt:item}
import datetime
#{var} = datetime.datetime.now().strftime("#{fmt}")
""", "Get the current date/time as text.")

comp("System", "Run System Command",
     [T("cmd", "Command", "dir", escape=True)],
     """
<RPWI:NEWSTEP> Run command "#{cmd:item}"
import os
os.system("#{cmd}")
""", "Run an operating system command.")

comp("System", "Exit Program",
     [],
     """
<RPWI:NEWSTEP> Exit Program
raise SystemExit
""", "Stop the program.")


# ============================================================ Domain Tree
# Like HarbourPWCT, the domains are nested (User Interface > GUI Application > Windows ...).
# comp() uses a short domain name; tree_path() gives its folder in the Domain Tree.
TREE = {
    "General": "Programming Basics/General",
    "Variables": "Programming Basics/Variables",
    "Control Structure": "Programming Basics/Control Structure",
    "Data Structures": "Programming Basics/Data Structures",
    "Arrays": "Programming Basics/Arrays",
    "Strings": "Programming Basics/Strings",
    "Math": "Programming Basics/Operations/Arithmetic",
    "Files": "Programming Basics/Files and Folders",
    "Functions": "Programming Paradigm/Structure Programming",
    "Classes": "Programming Paradigm/Object Oriented Programming (OOP)",
    "GUI": "User Interface/GUI Application",
    "System": "System",
}
TREE_ORDER = [
    "User Interface",
    "User Interface/GUI Application",
    "User Interface/GUI Application/Windows",
    "User Interface/GUI Application/Controls",
    "User Interface/GUI Application/Controls/Get and Set Values",
    "User Interface/Console Application",
    "User Interface/Print Text",
    "Programming Basics",
    "Programming Basics/General",
    "Programming Basics/Control Structure",
    "Programming Basics/Variables",
    "Programming Basics/Data Structures",
    "Programming Basics/Arrays",
    "Programming Basics/Strings",
    "Programming Basics/Operations",
    "Programming Basics/Operations/Arithmetic",
    "Programming Basics/Files and Folders",
    "Programming Paradigm",
    "Programming Paradigm/Structure Programming",
    "Programming Paradigm/Object Oriented Programming (OOP)",
    "System",
]
GUI_WINDOWS = ("Create Window", "Start Event Loop", "Close Window", "Message Box")
GUI_CONTROLS = ("Label", "Button", "Text Box", "Text Area", "Check Box", "List Box")
MANIFEST = "_generated.txt"


def tree_path(domain, name):
    """The folder of a component in the Domain Tree."""
    if domain == "Input and Output":
        return "User Interface/" + ("Print Text" if name.lower().startswith("print") else "Console Application")
    if domain == "GUI (Tkinter)":
        base = "User Interface/GUI Application/"
        if name in GUI_WINDOWS:
            return base + "Windows"
        if name in GUI_CONTROLS:
            return base + "Controls"
        return base + "Controls/Get and Set Values"
    return TREE.get(domain, domain)


def write_order(folder):
    """_order.txt in each folder = the order of its sub domains (TREE_ORDER)."""
    rank = {p.lower(): i for i, p in enumerate(TREE_ORDER)}
    for dp, dn, _ in os.walk(folder):
        if not dn:
            continue
        rel = os.path.relpath(dp, folder).replace("\\", "/")
        rel = "" if rel == "." else rel + "/"
        names = sorted(dn, key=lambda d: (rank.get((rel + d).lower(), len(rank)), d.lower()))
        with open(os.path.join(dp, "_order.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(names) + "\n")


def clean_generated(out):
    """Delete the files made by the last run, but not the components made by the user.
    The generated files are listed in _generated.txt (before it existed: order < 1000)."""
    man = os.path.join(out, MANIFEST)
    files = []
    if os.path.exists(man):
        with open(man, encoding="utf-8") as f:
            files = [ln.strip() for ln in f if ln.strip()]
    else:
        for dp, _, fn in os.walk(out):
            for name in fn:
                if not name.lower().endswith(".json"):
                    continue
                path = os.path.join(dp, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        order = json.load(f).get("order", 1000)
                except (OSError, ValueError):
                    continue
                if isinstance(order, int) and order < 1000:
                    files.append(os.path.relpath(path, out))
    folders = set()
    for rel in files:
        path = os.path.join(out, rel)
        if os.path.isfile(path):
            os.remove(path)
            folders.add(os.path.dirname(path))
    # the folders that are empty now (their _order.txt is written again)
    for folder in sorted(folders, key=len, reverse=True):
        while os.path.normcase(folder) != os.path.normcase(out) and os.path.isdir(folder):
            rest = [e for e in os.listdir(folder) if e != "_order.txt"]
            if rest:
                break
            shutil.rmtree(folder)
            folder = os.path.dirname(folder)


def write_components(components, out):
    os.makedirs(out, exist_ok=True)
    clean_generated(out)
    written = []
    for c in components:
        rel = tree_path(c["domain"], c["data"]["name"])
        folder = os.path.join(out, *rel.split("/"))
        os.makedirs(folder, exist_ok=True)
        fname = c["data"]["name"].replace("/", "-").replace(" ", "_").replace("#", "Sharp") + ".json"
        with open(os.path.join(folder, fname), "w", encoding="utf-8") as f:
            json.dump(c["data"], f, ensure_ascii=False, indent=1)
        written.append(rel + "/" + fname)
    with open(os.path.join(out, MANIFEST), "w", encoding="utf-8") as f:
        f.write("\n".join(written) + "\n")
    write_order(out)


def write_language(folder, data):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "language.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def main():
    write_language(LANG_DIR, LANGUAGE)
    write_components(COMPONENTS, OUT)
    print("%d components written to %s" % (len(COMPONENTS), OUT))


if __name__ == "__main__":
    main()
