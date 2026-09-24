"""Build the sample visual source files (samples/*.pwct) using the components.

Each sample is made exactly like a user makes it: interactions with the
components through the code generator.  Run: python tools/make_samples.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, BASE)

from pwct import codegen  # noqa: E402
from pwct.components import Library  # noqa: E402
from pwct.engine import Generator, default_values  # noqa: E402
from pwct.model import Project, Step  # noqa: E402

LIB = Library(os.path.join(BASE, "languages", "Python", "components"))
OUT = os.path.join(BASE, "languages", "Python", "samples")


class Builder:
    def __init__(self):
        self.p = Project()
        self.g = self.p.goals[0]
        self.gen = Generator(self.p, LIB)

    def i(self, key, parent, **vals):
        c = LIB.get(key)
        if c is None:
            raise KeyError(key)
        v = default_values(c, self.p)
        v.update(vals)
        _, created = self.gen.run(c, v, self.g, parent)
        return created

    @staticmethod
    def start(created, name="Start Here"):
        return next(s for s in created if s.name == name)

    def note(self, parent, name):
        return parent.add(Step(self.p.new_id(), name))

    def save(self, name):
        path = os.path.join(OUT, name + ".pwct")
        self.p.save(path)
        code, _ = codegen.generate(self.p)
        compile(code, name, "exec")
        print("sample :", path)


def hello_world():
    b = Builder()
    r = b.g.root
    m = b.note(r, "Hello World Program")
    b.i("Input and Output/Print_Text", m, text="Hello, World!")
    b.i("Input and Output/Input", m, var="name", prompt="What is your name? ")
    b.i("Input and Output/Print_Text_and_Value", m, text="Welcome", value="name")
    b.save("01_Hello_World")


def guess_the_number():
    b = Builder()
    r = b.g.root
    m = b.note(r, "Guess The Number Game")
    b.i("Math/Random_Number", m, var="secret", start="1", end="100")
    b.i("Variables/Assignment", m, var="tries", value="0")
    b.i("Input and Output/Print_Text", m, text="I have a number between 1 and 100, guess it!")
    loop = b.i("Control Structure/While_Loop", m, cond="True")
    body = b.start(loop)
    b.i("Input and Output/Input", body, var="guess", prompt="Your guess : ", type=1)
    b.i("Variables/Increment_-_Decrement", body, var="tries", op=0, value="1")
    cond = b.i("Control Structure/If_Statement", body, cond="guess < secret", elif1="guess > secret", **{"else": 1})
    b.i("Input and Output/Print_Text", b.start(cond), text="Bigger...")
    b.i("Input and Output/Print_Text", b.start(cond, "Else If guess > secret"), text="Smaller...")
    other = b.start(cond, "Else")
    b.i("Input and Output/Print_Text_and_Value", other, text="Great! You found it. Tries :", value="tries")
    b.i("Control Structure/Exit_Loop_(Break)", other)
    b.save("02_Guess_The_Number")


def multiplication_table():
    b = Builder()
    r = b.g.root
    m = b.note(r, "Multiplication Table")
    outer = b.i("Control Structure/For_Loop", m, var="x", start="1", end="10", step="1")
    body = b.start(outer)
    inner = b.i("Control Structure/For_Loop", body, var="y", start="1", end="10", step="1")
    b.i("General/Python_Code", b.start(inner), code='print(str(x * y).rjust(4), end="")')
    b.i("Input and Output/Print_New_Line", body)
    b.save("03_Multiplication_Table")


def functions_and_classes():
    b = Builder()
    r = b.g.root
    f = b.note(r, "Functions")
    fn = b.i("Functions/Define_Function", f, name="factorial", params="n")
    body = b.start(fn)
    cond = b.i("Control Structure/If_Statement", body, cond="n <= 1")
    b.i("Functions/Return", b.start(cond), value="1")
    b.i("Functions/Return", body, value="n * factorial(n - 1)")
    c = b.note(r, "Classes")
    cls = b.i("Classes/Define_Class", c, name="Person")
    cb = b.start(cls)
    ctor = b.i("Classes/Constructor", cb, params="name, age")
    b.i("Classes/Set_Attribute", b.start(ctor), attr="name", value="name")
    b.i("Classes/Set_Attribute", b.start(ctor), attr="age", value="age")
    meth = b.i("Classes/Define_Method", cb, name="show")
    b.i("Input and Output/Print_Expression", b.start(meth), value='"Name :", self.name, " Age :", self.age')
    m = b.note(r, "Main Program")
    b.i("Functions/Call_Function", m, name="factorial", args="5", result="result")
    b.i("Input and Output/Print_Text_and_Value", m, text="5! =", value="result")
    b.i("Classes/Create_Object", m, var="p1", cls="Person", args='"Mahmoud", 30')
    b.i("Functions/Call_Function", m, name="p1.show", args="")
    b.i("Data Structures/Create_List", m, var="numbers", items="5, 3, 9, 1")
    b.i("Data Structures/Sort_List", m, list="numbers", order=0)
    each = b.i("Control Structure/For_Each", m, var="n", seq="numbers")
    b.i("Input and Output/Print_Text_and_Value", b.start(each), text="Number :", value="n")
    b.save("04_Functions_and_Classes")


def gui_calculator():
    b = Builder()
    r = b.g.root
    ev = b.note(r, "Events")
    fn = b.i("Functions/Define_Function", ev, name="add_numbers")
    body = b.start(fn)
    t = b.i("Control Structure/Try_-_Catch_Errors", body, var="error")
    ts = b.start(t)
    b.i("GUI (Tkinter)/Get_Text_Box_Value", ts, var="a", box="text1")
    b.i("GUI (Tkinter)/Get_Text_Box_Value", ts, var="b", box="text2")
    b.i("Variables/Assignment", ts, var="total", value="float(a) + float(b)")
    b.i("GUI (Tkinter)/Set_Label_Text", ts, label="label3", value='"Result : " + str(total)')
    b.i("GUI (Tkinter)/Message_Box", b.start(t, "Catch Exception as error"), kind=2, title="Error",
        msg='"Please enter numbers"')
    w = b.note(r, "The window")
    win = b.i("GUI (Tkinter)/Create_Window", w, name="win1", title="PyPWCT Calculator", width="360",
              height="220", bg="#f0f0ff")
    ws = b.start(win)
    b.i("GUI (Tkinter)/Label", ws, name="label1", win="win1", text="First number", x="20", y="20", size="11")
    b.i("GUI (Tkinter)/Text_Box", ws, name="text1", win="win1", x="150", y="22", width="20")
    b.i("GUI (Tkinter)/Label", ws, name="label2", win="win1", text="Second number", x="20", y="60", size="11")
    b.i("GUI (Tkinter)/Text_Box", ws, name="text2", win="win1", x="150", y="62", width="20")
    b.i("GUI (Tkinter)/Button", ws, name="button1", win="win1", text="  Add  ", x="150", y="100",
        cmd="add_numbers")
    b.i("GUI (Tkinter)/Label", ws, name="label3", win="win1", text="Result :", x="20", y="150", size="14")
    b.save("05_GUI_Calculator")


def files():
    b = Builder()
    r = b.g.root
    m = b.note(r, "Files")
    b.i("Files/Write_to_File", m, file="pypwct_test.txt", content='"Line 1\\nLine 2\\nLine 3\\n"', mode=0)
    b.i("Files/Write_to_File", m, file="pypwct_test.txt", content='"Line 4\\n"', mode=1)
    b.i("Files/Read_File", m, var="lines", file="pypwct_test.txt", how=1)
    each = b.i("Control Structure/For_Each", m, var="line", seq="lines")
    b.i("Input and Output/Print_Expression", b.start(each), value="line")
    b.i("Data Structures/Get_Length", m, var="count", obj="lines")
    b.i("Input and Output/Print_Text_and_Value", m, text="Lines count :", value="count")
    b.i("Files/Delete_File", m, file="pypwct_test.txt")
    b.save("06_Files")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    hello_world()
    guess_the_number()
    multiplication_table()
    functions_and_classes()
    gui_calculator()
    files()
