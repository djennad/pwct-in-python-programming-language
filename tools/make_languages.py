"""Build the Visual Programming Languages CPWCT, C#PWCT, JavaPWCT and JavaScriptPWCT
(languages/<id>/language.json + components + start.pwct + samples).

Like PWCT, the same environment is used with any programming language behind
the scene: only the components (interaction pages + code masks) change.
Run:  python tools/make_languages.py     (after tools/make_components.py for Python)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, BASE)

from make_components import T, L, C, layout, write_components, write_language  # noqa: E402

LANG_ROOT = os.path.join(BASE, "languages")
IDS = ["C", "CSharp", "Java", "JavaScript"]
ORDER = ["Python", "C", "CSharp", "Java", "JavaScript"]

DOMAINS = [("General", "#404040"), ("Variables", "#1f6f8b"), ("Input and Output", "#2e7d32"),
           ("Control Structure", "#400040"), ("Functions", "#b71c1c"), ("Arrays", "#00838f"),
           ("Strings", "#e65100"), ("Math", "#283593"), ("GUI", "#0277bd"), ("System", "#455a64")]
COLOR = dict(DOMAINS)

C_KEYWORDS = ("auto break case char const continue default do double else enum extern float for goto if "
              "int long register return short signed sizeof static struct switch typedef union unsigned "
              "void volatile while printf scanf include main NULL")
CS_KEYWORDS = ("abstract bool break case catch char class const continue decimal default do double else "
               "enum false finally float for foreach if in int long namespace new null object private "
               "protected public return static string struct switch this throw true try using var void "
               "while Console Math")
JAVA_KEYWORDS = ("abstract boolean break case catch char class continue default do double else extends "
                 "false final finally float for if import int long new null private protected public "
                 "return static String switch this throw true try var void while System Math")
JS_KEYWORDS = ("break case catch class const continue default delete do else false finally for function "
               "if in let new null of return switch this throw true try typeof undefined var while "
               "console Math")

JS_INPUT = r'''const fs = require("fs");

// PyPWCT: read a line from the keyboard (synchronous input for Node.js)
function input(prompt) {
    process.stdout.write(String(prompt));
    const bytes = [];
    const buffer = Buffer.alloc(1);
    while (true) {
        let n = 0;
        try {
            n = fs.readSync(0, buffer, 0, 1, null);
        } catch (e) {
            if (e.code === "EAGAIN") { continue; }
            if (e.code === "EOF") { break; }
            throw e;
        }
        if (n === 0 || buffer[0] === 10) { break; }
        if (buffer[0] !== 13) { bytes.push(buffer[0]); }
    }
    return Buffer.from(bytes).toString("utf8");
}'''

CSC = r"%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
CSC32 = r"%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe"

LANGS = {
    "C": {
        "name": "CPWCT", "title": "C", "extension": ".c", "comment": "//", "indent": "    ", "empty_block": "",
        "prelude": "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n"
                   "#include <time.h>\n#ifdef _WIN32\n#include <windows.h>\n#endif",
        "build": ['gcc "{file}" -o "{exe}" -lm', 'clang "{file}" -o "{exe}"', 'tcc "{file}" -o "{exe}"'],
        "run": ['"{exe}"'],
        "check": ['gcc -fsyntax-only "{file}"', 'clang -fsyntax-only "{file}"'],
        "keywords": C_KEYWORDS, "syntax": "", "start": "start.pwct",
        "description": "C language (needs gcc, clang or tcc)",
    },
    "CSharp": {
        "name": "C#PWCT", "title": "C#", "extension": ".cs", "comment": "//", "indent": "    ", "empty_block": "",
        "prelude": "using System;\nusing System.Collections.Generic;",
        "build": ['"%s" /nologo /out:"{exe}" "{file}"' % CSC, '"%s" /nologo /out:"{exe}" "{file}"' % CSC32,
                  'csc /nologo /out:"{exe}" "{file}"'],
        "run": ['"{exe}"'],
        "check": ['"%s" /nologo /out:"{tmpdir}\\check.exe" "{file}"' % CSC,
                  'csc /nologo /out:"{tmpdir}\\check.exe" "{file}"'],
        "keywords": CS_KEYWORDS, "syntax": "", "start": "start.pwct",
        "description": "C# (.NET Framework compiler csc.exe - included in Windows)",
    },
    "Java": {
        "name": "JavaPWCT", "title": "Java", "extension": ".java", "comment": "//", "indent": "    ",
        "empty_block": "", "prelude": "import java.util.*;",
        "build": [], "run": ['java "{file}"'],
        "check": ['javac -d "{tmpdir}" "{file}"'],
        "keywords": JAVA_KEYWORDS, "syntax": "", "start": "start.pwct",
        "description": "Java (needs JDK 11 or newer: java runs the source file)",
    },
    "JavaScript": {
        "name": "JavaScriptPWCT", "title": "JavaScript", "extension": ".js", "comment": "//", "indent": "    ",
        "empty_block": "", "prelude": JS_INPUT,
        "build": [], "run": ['node "{file}"'], "check": ['node --check "{file}"'],
        "keywords": JS_KEYWORDS, "syntax": "", "start": "",
        "description": "JavaScript (needs Node.js)",
    },
}

COMPONENTS = {lid: [] for lid in IDS}
LOOPS = ["While Loop", "Do While Loop", "For Loop", "For Each"]


def comp(domain, name, fields, masks, desc, allow_interaction=(), allow_root=(1,), requires=(),
         requires_step=(), allow=None, langs=None):
    """masks: {lang id: mask} or a function(lang id) -> mask (None = not in this language)."""
    for lid in (langs or IDS):
        mask = masks(lid) if callable(masks) else masks.get(lid)
        if mask is None:
            continue
        flds = fields(lid) if callable(fields) else fields
        rs = requires_step(lid) if callable(requires_step) else requires_step
        al = allow(lid) if callable(allow) else allow
        rules = {"allow_root": list(allow_root), "allow_interaction": list(allow_interaction),
                 "requires_ancestor": list(requires)}
        if rs:
            rules["requires_step"] = list(rs)
        if al:
            rules["allow"] = al
        nm = name(lid) if callable(name) else name
        COMPONENTS[lid].append({"domain": domain, "data": {
            "name": nm, "description": desc, "order": len(COMPONENTS[lid]),
            "pages": layout(nm, domain, flds, color=COLOR[domain]),
            "mask": mask.strip("\n"), "rules": rules}})


def by(c=None, cs=None, java=None, js=None):
    return {"C": c, "CSharp": cs, "Java": java, "JavaScript": js}


def block(head, step, end, close="}"):
    return """
<RPWI:NEWSTEP> %s
%s {
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> %s
<RPWI:TABPOP>
%s
""" % (step, head, end, close)


def decl_test(declared, plain):
    """Code with/without the declaration (checkbox #{decl})."""
    return """
<RPWI:VALUE> 0
<RPWI:NEGATIVE>
<RPWI:TEST> #{decl}
  %s
<RPWI:ENDTEST>
<RPWI:VALUE> 0
<RPWI:POSITIVE>
<RPWI:TEST> #{decl}
  %s
<RPWI:ENDTEST>
""" % (declared, plain)


LANG_NAME = {"C": "C", "CSharp": "C#", "Java": "Java", "JavaScript": "JavaScript"}
DECL = C("decl", "Declare", "Declare the variable", 1)

# ================================================================= General
comp("General", "Comment", [T("text", "Comment", "")],
     {lid: "<RPWI:NEWSTEP> Comment : #{text}\n// #{text}" for lid in IDS},
     "Add a comment line to the generated source code.")

comp("General", lambda lid: LANG_NAME[lid] + " Code", [T("code", "Code", "")],
     {lid: "<RPWI:NEWSTEP> %s Code : #{code}\n#{code}" % LANG_NAME[lid] for lid in IDS},
     "Write one line of code directly (for experts).")

C_PROGRAM = """
<RPWI:NEWSTEP> Program
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Functions
<RPWI:NEWSTEP> Main
int main(void)
{
<RPWI:TABPUSH>
srand((unsigned) time(NULL));
<RPWI:PUTMARK> 3
<RPWI:SETMARK> 3
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> End of Main
return 0;
<RPWI:TABPOP>
}
"""
CLASS_PROGRAM = """
<RPWI:NEWSTEP> Program
class %s
{
<RPWI:TABPUSH>
%s
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Functions (Methods)
<RPWI:NEWSTEP> Main
%s
{
<RPWI:TABPUSH>
<RPWI:PUTMARK> 3
<RPWI:SETMARK> 3
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> End of Main
<RPWI:TABPOP>
}
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> End of Program
<RPWI:TABPOP>
}
"""
comp("General", "Program", [],
     by(c=C_PROGRAM,
        cs=CLASS_PROGRAM % ("Program", "static Random pwctRandom = new Random();", "static void Main(string[] args)"),
        java=CLASS_PROGRAM % ("Main", "static Scanner input = new Scanner(System.in);",
                              "public static void main(String[] args)")),
     "The structure of the program: the functions and the main function (File > New creates it).",
     allow_interaction=(2, 4),
     allow=lambda lid: {"2": ["Define Function", "Comment", LANG_NAME[lid] + " Code"]
                        + (["Declare Variable", "Declare Array", "Array with Values"] if lid == "C" else [])})

# =============================================================== Variables
C_TYPES = L("type", "Type", ["Integer (int)", "Double (double)", "Character (char)", "Text (char[256])"],
            ["int", "double", "char", "text"])
TYPES = {
    "CSharp": L("type", "Type", ["Integer (int)", "Double (double)", "Text (string)", "Boolean (bool)",
                                 "Character (char)"], ["int", "double", "string", "bool", "char"]),
    "Java": L("type", "Type", ["Integer (int)", "Double (double)", "Text (String)", "Boolean (boolean)",
                               "Character (char)"], ["int", "double", "String", "boolean", "char"]),
    "JavaScript": L("type", "Kind", ["Variable (let)", "Constant (const)"], ["let", "const"]),
}


def declare_fields(lid):
    t = C_TYPES if lid == "C" else TYPES[lid]
    return [T("name", "Variable name", "x", kind="name"), t,
            T("value", "Initial value (optional)", "0", kind="expr", allow_empty=True)]


def empty_test(empty, full):
    return """
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{value}
  %s
<RPWI:ENDTEST>
<RPWI:VALUE>
<RPWI:NEGATIVE>
<RPWI:TEST> #{value}
  %s
<RPWI:ENDTEST>
""" % (empty, full)


C_DECLARE = ("<RPWI:NEWSTEP> Declare #{name} As #{type:item} : #{value}\n"
             "<RPWI:VALUE> text\n<RPWI:POSITIVE>\n<RPWI:TEST> #{type}\n"
             + empty_test('char #{name}[256] = "";', "char #{name}[256] = #{value};") +
             "<RPWI:ENDTEST>\n<RPWI:VALUE> text\n<RPWI:NEGATIVE>\n<RPWI:TEST> #{type}\n"
             + empty_test("#{type} #{name};", "#{type} #{name} = #{value};") + "<RPWI:ENDTEST>")
TYPED_DECLARE = ("<RPWI:NEWSTEP> Declare #{name} As #{type:item} : #{value}\n"
                 + empty_test("#{type} #{name};", "#{type} #{name} = #{value};"))
comp("Variables", "Declare Variable", declare_fields,
     by(c=C_DECLARE, cs=TYPED_DECLARE, java=TYPED_DECLARE, js=TYPED_DECLARE),
     "Declare a new variable (with an optional initial value).")

comp("Variables", "Assignment",
     [T("var", "Variable", "x", kind="target"), T("value", "Value (Expression)", "0", kind="expr")],
     {lid: "<RPWI:NEWSTEP> #{var} = #{value}\n#{var} = #{value};" for lid in IDS},
     "Set the value of a variable using an expression.")

comp("Variables", "Increment / Decrement",
     [T("var", "Variable", "x", kind="target"),
      L("op", "Operation", ["Increment (+)", "Decrement (-)", "Multiply (*)", "Divide (/)", "Remainder (%)"],
        ["+=", "-=", "*=", "/=", "%="]),
      T("value", "By", "1", kind="expr")],
     {lid: "<RPWI:NEWSTEP> #{var} #{op} #{value}\n#{var} #{op} #{value};" for lid in IDS},
     "Change the value of a variable.")

# ======================================================== Input and Output
comp("Input and Output", "Print Text", [T("text", "Text", "Hello, World!", escape=True, allow_empty=True)],
     {lid: "<RPWI:NEWSTEP> Print : #{text:item}\n" + code for lid, code in by(
         c='printf("%s\\n", "#{text}");', cs='Console.WriteLine("#{text}");',
         java='System.out.println("#{text}");', js='console.log("#{text}");').items()},
     "Print a text message on the screen.")

comp("Input and Output", "Print Text (Same Line)", [T("text", "Text", "Enter a value : ", escape=True)],
     {lid: "<RPWI:NEWSTEP> Print (Same Line) : #{text:item}\n" + code for lid, code in by(
         c='printf("%s", "#{text}");', cs='Console.Write("#{text}");',
         java='System.out.print("#{text}");', js='process.stdout.write("#{text}");').items()},
     "Print a text without moving to a new line.")

C_FMT = L("fmt", "Value type", ["Integer (%d)", "Double (%g)", "Text (%s)", "Character (%c)"],
          ["%d", "%g", "%s", "%c"])
comp("Input and Output", "Print Value",
     lambda lid: [T("value", "Expression", "x", kind="expr")] + ([C_FMT] if lid == "C" else []),
     {lid: "<RPWI:NEWSTEP> Print : #{value}\n" + code for lid, code in by(
         c='printf("#{fmt}\\n", #{value});', cs="Console.WriteLine(#{value});",
         java="System.out.println(#{value});", js="console.log(#{value});").items()},
     "Print the value of a variable or an expression.")

comp("Input and Output", "Print Text and Value",
     lambda lid: [T("text", "Text", "The result is :", escape=True), T("value", "Expression", "x", kind="expr")]
     + ([C_FMT] if lid == "C" else []),
     {lid: "<RPWI:NEWSTEP> Print : #{text:item} #{value}\n" + code for lid, code in by(
         c='printf("%s #{fmt}\\n", "#{text}", #{value});', cs='Console.WriteLine("#{text} " + #{value});',
         java='System.out.println("#{text} " + #{value});', js='console.log("#{text}", #{value});').items()},
     "Print a message followed by a value.")

comp("Input and Output", "Print New Line", [],
     {lid: "<RPWI:NEWSTEP> Print New Line\n" + code for lid, code in by(
         c='printf("\\n");', cs="Console.WriteLine();", java="System.out.println();",
         js="console.log();").items()},
     "Print an empty line.")


def input_fields(lid):
    types = {
        "C": L("type", "Data type", ["Integer Number", "Double Number", "Text"], ["int", "double", "text"]),
        "CSharp": L("type", "Data type", ["Integer Number", "Double Number", "Text"],
                    ["int.Parse(Console.ReadLine())", "double.Parse(Console.ReadLine())", "Console.ReadLine()"]),
        "Java": L("type", "Data type", ["Integer Number", "Double Number", "Text"],
                  ["Integer.parseInt(input.nextLine().trim())", "Double.parseDouble(input.nextLine().trim())",
                   "input.nextLine()"]),
        "JavaScript": L("type", "Data type", ["Integer Number", "Double Number", "Text"],
                        ["parseInt", "parseFloat", "String"]),
    }
    return [T("var", "Variable", "x", kind="target"),
            T("prompt", "Message", "Enter a value : ", escape=True, allow_empty=True), types[lid], DECL]


C_INPUT = """
<RPWI:NEWSTEP> #{var} = Input #{type:item} : #{prompt:item}
printf("%s", "#{prompt}");
<RPWI:VALUE> 0
<RPWI:NEGATIVE>
<RPWI:TEST> #{decl}
  <RPWI:VALUE> text
  <RPWI:POSITIVE>
  <RPWI:TEST> #{type}
    char #{var}[256];
  <RPWI:ENDTEST>
  <RPWI:VALUE> text
  <RPWI:NEGATIVE>
  <RPWI:TEST> #{type}
    #{type} #{var};
  <RPWI:ENDTEST>
<RPWI:ENDTEST>
<RPWI:POSITIVE>
<RPWI:VALUE> int
<RPWI:TEST> #{type}
  scanf("%d", &#{var});
<RPWI:ENDTEST>
<RPWI:VALUE> double
<RPWI:TEST> #{type}
  scanf("%lf", &#{var});
<RPWI:ENDTEST>
<RPWI:VALUE> text
<RPWI:TEST> #{type}
  scanf(" %255[^\\n]", #{var});
<RPWI:ENDTEST>
"""
INPUT_HEAD = "<RPWI:NEWSTEP> #{var} = Input #{type:item} : #{prompt:item}\n"
comp("Input and Output", "Input", input_fields,
     by(c=C_INPUT,
        cs=INPUT_HEAD + 'Console.Write("#{prompt}");' + decl_test("var #{var} = #{type};", "#{var} = #{type};"),
        java=INPUT_HEAD + 'System.out.print("#{prompt}");' + decl_test("var #{var} = #{type};", "#{var} = #{type};"),
        js=INPUT_HEAD + decl_test('let #{var} = #{type}(input("#{prompt}"));', '#{var} = #{type}(input("#{prompt}"));')),
     "Get a value from the user (keyboard).")

# ======================================================= Control Structure
IF_MASK = """
<RPWI:NEWSTEP> If #{cond}
if (#{cond}) {
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:VALUE>
<RPWI:NEGATIVE>
<RPWI:TEST> #{elif1}
  <RPWI:NEWSTEP> Else If #{elif1}
  <RPWI:TABPOP>
  } else if (#{elif1}) {
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:TEST> #{elif2}
  <RPWI:NEWSTEP> Else If #{elif2}
  <RPWI:TABPOP>
  } else if (#{elif2}) {
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:TEST> #{elif3}
  <RPWI:NEWSTEP> Else If #{elif3}
  <RPWI:TABPOP>
  } else if (#{elif3}) {
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:VALUE> 0
<RPWI:TEST> #{else}
  <RPWI:NEWSTEP> Else
  <RPWI:TABPOP>
  } else {
  <RPWI:TABPUSH>
<RPWI:ENDTEST>
<RPWI:NEWSTEP> End of If
<RPWI:TABPOP>
}
"""
comp("Control Structure", "If Statement",
     [T("cond", "Condition", "x > 0", kind="expr"),
      T("elif1", "Else If (optional)", "", kind="expr", allow_empty=True),
      T("elif2", "Else If (optional)", "", kind="expr", allow_empty=True),
      T("elif3", "Else If (optional)", "", kind="expr", allow_empty=True),
      C("else", "Else", "Add Else branch")],
     {lid: IF_MASK for lid in IDS},
     "Execute steps when a condition is true (with optional Else If / Else).",
     allow_interaction=(2, 3, 4, 5, 6))

comp("Control Structure", "While Loop", [T("cond", "Condition", "x < 10", kind="expr")],
     {lid: block("while (#{cond})", "While #{cond}", "End of While") for lid in IDS},
     "Repeat steps while a condition is true.", allow_interaction=(2,))

comp("Control Structure", "Do While Loop", [T("cond", "Condition", "x < 10", kind="expr")],
     {lid: block("do", "Do (While #{cond})", "Loop While #{cond}", "} while (#{cond});") for lid in IDS},
     "Repeat steps (at least one time) while a condition is true.", allow_interaction=(2,))

FOR_HEAD = ("for (%s #{var} = #{start}; (#{step}) > 0 ? #{var} <= (#{end}) : #{var} >= (#{end}); "
            "#{var} += #{step})")
comp("Control Structure", "For Loop",
     [T("var", "Variable", "x", kind="name"), T("start", "From", "1", kind="expr"),
      T("end", "To", "10", kind="expr"), T("step", "Step", "1", kind="expr")],
     {lid: block(FOR_HEAD % ("let" if lid == "JavaScript" else "int"),
                 "For #{var} = #{start} To #{end} Step #{step}", "Next") for lid in IDS},
     "Repeat steps for a counter from a start value to an end value.", allow_interaction=(2,))

comp("Control Structure", "For Each",
     [T("var", "Item variable", "item", kind="name"), T("seq", "In (Array/List)", "items", kind="expr")],
     by(cs=block("foreach (var #{var} in #{seq})", "For Each #{var} In #{seq}", "End of For Each"),
        java=block("for (var #{var} : #{seq})", "For Each #{var} In #{seq}", "End of For Each"),
        js=block("for (const #{var} of #{seq})", "For Each #{var} In #{seq}", "End of For Each")),
     "Repeat steps for each item in an array or a list.", allow_interaction=(2,))

comp("Control Structure", "Exit Loop (Break)", [],
     {lid: "<RPWI:NEWSTEP> Exit Loop\nbreak;" for lid in IDS}, "Exit from the current loop.", requires=LOOPS)

comp("Control Structure", "Loop (Continue)", [],
     {lid: "<RPWI:NEWSTEP> Loop (Continue)\ncontinue;" for lid in IDS},
     "Skip to the next iteration of the loop.", requires=LOOPS)

# =============================================================== Functions
RET_TYPES = {
    "C": L("type", "Return type", ["void", "int", "double", "char", "char*"]),
    "CSharp": L("type", "Return type", ["void", "int", "double", "string", "bool"]),
    "Java": L("type", "Return type", ["void", "int", "double", "String", "boolean"]),
}
FUNC = """
<RPWI:NEWSTEP> Function #{name} (#{params})%s
%s
{
<RPWI:TABPUSH>
<RPWI:PUTMARK> 2
<RPWI:SETMARK> 2
<RPWI:NEWSTEP> Start Here
<RPWI:NEWSTEP> End of Function
<RPWI:TABPOP>
}
<pwct:newline>
"""
comp("Functions", "Define Function",
     lambda lid: [T("name", "Function name", "myfunction", kind="name")]
     + ([RET_TYPES[lid]] if lid in RET_TYPES else [])
     + [T("params", "Parameters" + ("" if lid == "JavaScript" else " (with types)"),
          "" if lid == "JavaScript" else "", kind="params", allow_empty=True)],
     by(c=FUNC % (" : #{type}", "#{type} #{name}(#{params})"),
        cs=FUNC % (" : #{type}", "static #{type} #{name}(#{params})"),
        java=FUNC % (" : #{type}", "static #{type} #{name}(#{params})"),
        js=FUNC % ("", "function #{name}(#{params})")),
     "Define a new function. Example of parameters: int a, int b",
     allow_interaction=(2,),
     requires_step=lambda lid: {"C": ["Functions"], "CSharp": ["Functions (Methods)"],
                                "Java": ["Functions (Methods)"]}.get(lid, []))

comp("Functions", "Return", [T("value", "Value", "", kind="expr", allow_empty=True)],
     {lid: "<RPWI:NEWSTEP> Return #{value}\nreturn #{value};" for lid in IDS},
     "Return from the function (with an optional value).", requires=["Define Function"])

CALL = """
<RPWI:VALUE>
<RPWI:POSITIVE>
<RPWI:TEST> #{result}
  <RPWI:NEWSTEP> Call #{name}(#{args})
  #{name}(#{args});
<RPWI:ENDTEST>
<RPWI:NEGATIVE>
<RPWI:TEST> #{result}
  <RPWI:NEWSTEP> #{result} = Call #{name}(#{args})
  #{result} = #{name}(#{args});
<RPWI:ENDTEST>
"""
comp("Functions", "Call Function",
     [T("name", "Function", "myfunction", kind="expr"),
      T("args", "Parameters", "", kind="args", allow_empty=True),
      T("result", "Result variable (optional)", "", kind="target", allow_empty=True)],
     {lid: CALL for lid in IDS}, "Call a function.", allow_root=(1, 2))

# ================================================================== Arrays
ARR_TYPES = {
    "C": L("type", "Type", ["int", "double", "char"]),
    "CSharp": L("type", "Type", ["int", "double", "string", "bool"]),
    "Java": L("type", "Type", ["int", "double", "String", "boolean"]),
}
comp("Arrays", "Declare Array",
     lambda lid: [T("name", "Array name", "numbers", kind="name")]
     + ([ARR_TYPES[lid]] if lid in ARR_TYPES else []) + [T("size", "Size", "10", kind="expr")],
     by(c="<RPWI:NEWSTEP> Declare Array #{name}[#{size}] : #{type}\n#{type} #{name}[#{size}];\n"
          "memset(#{name}, 0, sizeof(#{name}));",
        cs="<RPWI:NEWSTEP> Declare Array #{name}[#{size}] : #{type}\n#{type}[] #{name} = new #{type}[#{size}];",
        java="<RPWI:NEWSTEP> Declare Array #{name}[#{size}] : #{type}\n#{type}[] #{name} = new #{type}[#{size}];",
        js="<RPWI:NEWSTEP> Declare Array #{name}[#{size}]\nlet #{name} = new Array(#{size}).fill(0);"),
     "Declare an array (the items start with 0).")

comp("Arrays", "Array with Values",
     lambda lid: [T("name", "Array name", "numbers", kind="name")]
     + ([ARR_TYPES[lid]] if lid in ARR_TYPES else []) + [T("items", "Items", "5, 3, 9, 1", kind="args")],
     by(c="<RPWI:NEWSTEP> #{name} = { #{items} }\n#{type} #{name}[] = { #{items} };",
        cs="<RPWI:NEWSTEP> #{name} = { #{items} }\n#{type}[] #{name} = { #{items} };",
        java="<RPWI:NEWSTEP> #{name} = { #{items} }\n#{type}[] #{name} = { #{items} };",
        js="<RPWI:NEWSTEP> #{name} = [ #{items} ]\nlet #{name} = [#{items}];"),
     "Declare an array with its items.")

comp("Arrays", "Array Length",
     lambda lid: [T("var", "Variable", "n", kind="name"), T("name", "Array", "numbers", kind="expr"), DECL],
     by(c="<RPWI:NEWSTEP> #{var} = Length of #{name}\n"
          + decl_test("int #{var} = sizeof(#{name}) / sizeof(#{name}[0]);",
                      "#{var} = sizeof(#{name}) / sizeof(#{name}[0]);"),
        cs="<RPWI:NEWSTEP> #{var} = Length of #{name}\n"
           + decl_test("int #{var} = #{name}.Length;", "#{var} = #{name}.Length;"),
        java="<RPWI:NEWSTEP> #{var} = Length of #{name}\n"
             + decl_test("int #{var} = #{name}.length;", "#{var} = #{name}.length;"),
        js="<RPWI:NEWSTEP> #{var} = Length of #{name}\n"
           + decl_test("let #{var} = #{name}.length;", "#{var} = #{name}.length;")),
     "Get the number of items in an array.")

# ================================================================= Strings
comp("Strings", "Copy Text (strcpy)",
     [T("var", "Text variable", "name", kind="target"), T("value", "Text", '"Hello"', kind="expr")],
     by(c="<RPWI:NEWSTEP> #{var} = #{value}\nstrcpy(#{var}, #{value});"),
     "Copy a text to a text variable (char[]).", langs=["C"])

comp("Strings", "Concatenate Text (strcat)",
     [T("var", "Text variable", "name", kind="target"), T("value", "Text to add", '" World"', kind="expr")],
     by(c="<RPWI:NEWSTEP> #{var} = #{var} + #{value}\nstrcat(#{var}, #{value});"),
     "Add a text at the end of a text variable.", langs=["C"])

comp("Strings", "Text Length",
     [T("var", "Variable", "n", kind="name"), T("text", "Text", "name", kind="expr"), DECL],
     by(c="<RPWI:NEWSTEP> #{var} = Length of #{text}\n"
          + decl_test("int #{var} = (int) strlen(#{text});", "#{var} = (int) strlen(#{text});")),
     "Get the number of letters of a text.", langs=["C"])

TEXT_OPS = {
    "CSharp": [".ToUpper()", ".ToLower()", ".Trim()", ".Length"],
    "Java": [".toUpperCase()", ".toLowerCase()", ".trim()", ".length()"],
    "JavaScript": [".toUpperCase()", ".toLowerCase()", ".trim()", ".length"],
}
DECL_KW = {"C": "int", "CSharp": "var", "Java": "var", "JavaScript": "let"}
comp("Strings", "Text Operation",
     lambda lid: [T("var", "Result variable", "result", kind="name"), T("text", "Text", "name", kind="expr"),
                  L("op", "Operation", ["Upper Case", "Lower Case", "Remove Spaces (Trim)", "Length"],
                    TEXT_OPS[lid]), DECL],
     {lid: "<RPWI:NEWSTEP> #{var} = #{op:item} (#{text})\n"
           + decl_test("%s #{var} = (#{text})#{op};" % DECL_KW[lid], "#{var} = (#{text})#{op};")
      for lid in TEXT_OPS},
     "Change the letters of a text, or get its length.", langs=["CSharp", "Java", "JavaScript"])

# ==================================================================== Math
RANDOM = {
    "C": "(#{start}) + rand() % ((#{end}) - (#{start}) + 1)",
    "CSharp": "pwctRandom.Next(#{start}, (#{end}) + 1)",
    "Java": "(#{start}) + (int) (Math.random() * ((#{end}) - (#{start}) + 1))",
    "JavaScript": "Math.floor(Math.random() * ((#{end}) - (#{start}) + 1)) + (#{start})",
}
INT_KW = {"C": "int", "CSharp": "int", "Java": "int", "JavaScript": "let"}
comp("Math", "Random Number",
     [T("var", "Variable", "number", kind="name"), T("start", "From", "1", kind="expr"),
      T("end", "To", "100", kind="expr"), DECL],
     {lid: "<RPWI:NEWSTEP> #{var} = Random Number (#{start} To #{end})\n"
           + decl_test("%s #{var} = %s;" % (INT_KW[lid], RANDOM[lid]), "#{var} = %s;" % RANDOM[lid])
      for lid in IDS},
     "Get a random integer number.")

MATH = {
    "C": ["sqrt", "pow", "fabs", "round", "floor", "ceil", "sin", "cos", "tan", "log", "fmin", "fmax"],
    "CSharp": ["Math.Sqrt", "Math.Pow", "Math.Abs", "Math.Round", "Math.Floor", "Math.Ceiling",
               "Math.Sin", "Math.Cos", "Math.Tan", "Math.Log", "Math.Min", "Math.Max"],
    "Java": ["Math.sqrt", "Math.pow", "Math.abs", "Math.round", "Math.floor", "Math.ceil",
             "Math.sin", "Math.cos", "Math.tan", "Math.log", "Math.min", "Math.max"],
    "JavaScript": ["Math.sqrt", "Math.pow", "Math.abs", "Math.round", "Math.floor", "Math.ceil",
                   "Math.sin", "Math.cos", "Math.tan", "Math.log", "Math.min", "Math.max"],
}
MATH_NAMES = ["Square Root", "Power (x, y)", "Absolute", "Round", "Floor", "Ceil", "Sine", "Cosine",
              "Tangent", "Logarithm", "Minimum (x, y)", "Maximum (x, y)"]
DBL_KW = {"C": "double", "CSharp": "var", "Java": "var", "JavaScript": "let"}
comp("Math", "Math Function",
     lambda lid: [T("var", "Result variable", "result", kind="name"),
                  L("func", "Function", MATH_NAMES, MATH[lid]), T("args", "Value(s)", "x", kind="args"), DECL],
     {lid: "<RPWI:NEWSTEP> #{var} = #{func:item} (#{args})\n"
           + decl_test("%s #{var} = #{func}(#{args});" % DBL_KW[lid], "#{var} = #{func}(#{args});")
      for lid in IDS},
     "Use a mathematical function.")

# ===================================================================== GUI
MSG_KINDS = {
    "C": ["MB_ICONINFORMATION", "MB_ICONWARNING", "MB_ICONERROR"],
    "CSharp": ["Information", "Warning", "Error"],
    "Java": ["INFORMATION_MESSAGE", "WARNING_MESSAGE", "ERROR_MESSAGE"],
}
comp("GUI", "Message Box",
     lambda lid: [L("kind", "Type", ["Information", "Warning", "Error"], MSG_KINDS[lid]),
                  T("title", "Title", "Message", escape=True), T("msg", "Message", '"Hello"', kind="expr")],
     by(c="<RPWI:NEWSTEP> Message Box (#{kind:item}) : #{msg}\n"
          'MessageBoxA(NULL, #{msg}, "#{title}", MB_OK | #{kind});',
        cs="<RPWI:NEWSTEP> Message Box (#{kind:item}) : #{msg}\n"
           'System.Windows.Forms.MessageBox.Show(Convert.ToString(#{msg}), "#{title}", '
           "System.Windows.Forms.MessageBoxButtons.OK, System.Windows.Forms.MessageBoxIcon.#{kind});",
        java="<RPWI:NEWSTEP> Message Box (#{kind:item}) : #{msg}\n"
             'javax.swing.JOptionPane.showMessageDialog(null, #{msg}, "#{title}", '
             "javax.swing.JOptionPane.#{kind});"),
     "Show a message box (Windows).", langs=["C", "CSharp", "Java"])

# ================================================================== System
comp("System", "Sleep (Wait)", [T("ms", "Milliseconds", "1000", kind="expr")],
     {lid: "<RPWI:NEWSTEP> Sleep #{ms} ms\n" + code for lid, code in by(
         c="Sleep(#{ms});", cs="System.Threading.Thread.Sleep(#{ms});",
         java="try { Thread.sleep(#{ms}); } catch (InterruptedException e) { }",
         js="Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, #{ms});").items()},
     "Wait for some milliseconds.")

comp("System", "Exit Program", [],
     {lid: "<RPWI:NEWSTEP> Exit Program\n" + code for lid, code in by(
         c="exit(0);", cs="Environment.Exit(0);", java="System.exit(0);", js="process.exit(0);").items()},
     "Stop the program.")


# ============================================================ start + samples
class Builder:
    """Build visual source files with the engine (like a user)."""

    def __init__(self, lid, library):
        from pwct.engine import Generator
        from pwct.languages import Language
        from pwct.model import Project
        self.lid = lid
        self.lib = library
        self.lang = Language(lid, os.path.join(LANG_ROOT, lid), LANGS[lid])
        self.p = Project(lid)
        self.g = self.p.goals[0]
        self.gen = Generator(self.p, library, self.lang)

    def i(self, cname, parent, **vals):
        from pwct.engine import default_values
        comp_ = next((c for c in self.lib.all() if c.name == cname), None)
        if comp_ is None:
            raise KeyError("%s : %s" % (self.lid, cname))
        v = default_values(comp_, self.p)
        v.update(vals)
        _, created = self.gen.run(comp_, v, self.g, parent)
        return created

    def find(self, name):
        return next(s for s in self.g.root.walk() if s.name == name)

    @staticmethod
    def start(created, name="Start Here"):
        return next(s for s in created if s.name == name)

    def note(self, parent, name):
        from pwct.model import Step
        return parent.add(Step(self.p.new_id(), name))

    def program(self):
        if self.lid == "JavaScript":
            return self.g.root, self.g.root
        self.i("Program", self.g.root)
        funcs = self.find("Functions (Methods)" if self.lid != "C" else "Functions")
        return funcs, self.find("Start Here")


def make_samples(lid, lang_dir):
    from pwct.components import Library
    lib = Library(os.path.join(lang_dir, "components"))
    out = os.path.join(lang_dir, "samples")
    os.makedirs(out, exist_ok=True)
    files = []
    # start file (File > New)
    b = Builder(lid, lib)
    b.program()
    if lid != "JavaScript":
        b.p.save(os.path.join(lang_dir, "start.pwct"))

    # 1 - Hello World
    b = Builder(lid, lib)
    _, main = b.program()
    m = b.note(main, "Hello World Program")
    b.i("Print Text", m, text="Hello, World!")
    b.i("Input", m, var="name", prompt="What is your name? ", type=2)
    if lid == "C":
        b.i("Print Text and Value", m, text="Welcome", value="name", fmt=2)
    else:
        b.i("Print Text and Value", m, text="Welcome", value="name")
    files.append(("01_Hello_World", b))

    # 2 - Guess the number
    b = Builder(lid, lib)
    _, main = b.program()
    m = b.note(main, "Guess The Number Game")
    b.i("Random Number", m, var="secret", start="1", end="100")
    b.i("Declare Variable", m, name="tries", type=0, value="0")
    b.i("Print Text", m, text="I have a number between 1 and 100, guess it!")
    loop = b.i("While Loop", m, cond="1" if lid == "C" else "true")
    body = b.start(loop)
    b.i("Input", body, var="guess", prompt="Your guess : ", type=0)
    b.i("Increment / Decrement", body, var="tries", op=0, value="1")
    cond = b.i("If Statement", body, cond="guess < secret", elif1="guess > secret", **{"else": 1})
    b.i("Print Text", b.start(cond), text="Bigger...")
    b.i("Print Text", b.start(cond, "Else If guess > secret"), text="Smaller...")
    other = b.start(cond, "Else")
    b.i("Print Text and Value", other, text="Great! You found it. Tries :", value="tries",
        **({"fmt": 0} if lid == "C" else {}))
    b.i("Exit Loop (Break)", other)
    files.append(("02_Guess_The_Number", b))

    # 3 - Functions and loops
    b = Builder(lid, lib)
    funcs, main = b.program()
    ftype = {"C": 1, "CSharp": 1, "Java": 1}.get(lid)
    params = "n" if lid == "JavaScript" else "int n"
    fn = b.i("Define Function", funcs, name="factorial", params=params, **({"type": ftype} if ftype else {}))
    fbody = b.start(fn)
    c1 = b.i("If Statement", fbody, cond="n <= 1")
    b.i("Return", b.start(c1), value="1")
    b.i("Return", fbody, value="n * factorial(n - 1)")
    m = b.note(main, "Main Program")
    loop = b.i("For Loop", m, var="i", start="1", end="10", step="1")
    b.i("Call Function", b.start(loop), name="factorial", args="i",
        result="result")
    lbody = b.start(loop)
    # declare result before the loop
    decl = b.i("Declare Variable", m, name="result", type=0, value="0")
    m.children.remove(decl[0])
    m.children.insert(0, decl[0])
    b.i("Print Text and Value", lbody, text="Factorial :", value="result", **({"fmt": 0} if lid == "C" else {}))
    arr = b.i("Array with Values", m, name="numbers", items="5, 3, 9, 1", **({"type": 0} if lid != "JavaScript" else {}))
    if lid == "C":
        b.i("Array Length", m, var="count", name="numbers")
        loop2 = b.i("For Loop", m, var="k", start="0", end="count - 1", step="1")
        b.i("Print Text and Value", b.start(loop2), text="Item :", value="numbers[k]", fmt=0)
    else:
        each = b.i("For Each", m, var="item", seq="numbers")
        b.i("Print Text and Value", b.start(each), text="Item :", value="item")
    files.append(("03_Functions_and_Loops", b))

    for name, bb in files:
        path = os.path.join(out, name + ".pwct")
        bb.p.save(path)
        print("sample :", os.path.relpath(path, BASE))


def main():
    os.makedirs(LANG_ROOT, exist_ok=True)
    with open(os.path.join(LANG_ROOT, "_order.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ORDER) + "\n")
    for lid in IDS:
        folder = os.path.join(LANG_ROOT, lid)
        write_language(folder, LANGS[lid])
        write_components(COMPONENTS[lid], os.path.join(folder, "components"))
        print("%-11s %d components" % (lid, len(COMPONENTS[lid])))
        make_samples(lid, folder)


if __name__ == "__main__":
    main()
