"""Shared UI helpers: images, the PWCT silver gradient, tooltips, dialogs."""

import os
import tkinter as tk
from tkinter import ttk

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")

SILVER_TOP = (242, 242, 242)
SILVER_BOTTOM = (210, 210, 210)
PURPLE = "#400040"
UI_FONT = ("Segoe UI", 9)
UI_BOLD = ("Segoe UI", 9, "bold")
TITLE_FONT = ("Segoe UI", 10, "bold")

_images = {}


def image(name):
    """Load assets/<name>.png once (kept alive in a cache)."""
    if name not in _images:
        path = os.path.join(ASSETS, name + ".png")
        try:
            _images[name] = tk.PhotoImage(file=path)
        except tk.TclError:
            _images[name] = None
    return _images[name]


def hex_color(rgb):
    return "#%02x%02x%02x" % rgb


class Gradient(tk.Canvas):
    """A frame with the silver gradient background (silvergradient.png)."""

    def __init__(self, master, height=34, top=SILVER_TOP, bottom=SILVER_BOTTOM, **kw):
        super().__init__(master, height=height, highlightthickness=0, bd=0, **kw)
        self._top, self._bottom = top, bottom
        self.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        self.delete("gradient")
        w, h = self.winfo_width(), self.winfo_height()
        for y in range(h):
            t = y / max(h - 1, 1)
            c = tuple(int(a + (b - a) * t) for a, b in zip(self._top, self._bottom))
            self.create_line(0, y, w, y, fill=hex_color(c), tags="gradient")
        self.tag_lower("gradient")


class ToolTip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tip, self.job = widget, text, None, None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _e=None):
        self._cancel()
        self.job = self.widget.after(500, self._show)

    def _cancel(self):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None

    def _show(self):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        tk.Label(tw, text=self.text, background="#ffffe1", relief="solid", borderwidth=1,
                 font=UI_FONT, padx=4, pady=1).pack()

    def _hide(self, _e=None):
        self._cancel()
        if self.tip:
            self.tip.destroy()
            self.tip = None


def icon_button(master, img_name, tip, command, text="", width=None, **kw):
    img = image(img_name) if img_name else None
    b = tk.Button(master, image=img, text=text, compound="left" if text else "center",
                  command=command, relief="flat", bd=1, bg="#ffffff", activebackground="#dde8f6",
                  cursor="hand2", font=UI_FONT, overrelief="raised", **kw)
    if width:
        b.config(width=width)
    if tip:
        ToolTip(b, tip)
    return b


def center(win, parent=None, w=None, h=None):
    win.update_idletasks()
    w = w or win.winfo_reqwidth()
    h = h or win.winfo_reqheight()
    if parent is not None and parent.winfo_viewable():
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    else:
        x = (win.winfo_screenwidth() - w) // 2
        y = (win.winfo_screenheight() - h) // 3
    win.geometry("%dx%d+%d+%d" % (w, h, max(x, 0), max(y, 0)))


class Dialog(tk.Toplevel):
    """Base PWCT window: silver header with a centered title and a line under it."""

    def __init__(self, parent, title, header=None, size=None, resizable=True):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.transient(parent.winfo_toplevel())
        self.configure(bg="#ffffff")
        self.resizable(resizable, resizable)
        ic = image("app_icon")
        if ic:
            self.iconphoto(False, ic)
        self.header = Gradient(self, height=34)
        self.header.pack(fill="x")
        self.header.create_text(0, 17, text=header or title, font=TITLE_FONT, tags="title")
        self.header.bind("<Configure>", lambda e: self.header.coords("title", e.width // 2, 17), add="+")
        tk.Frame(self, height=2, bg="#808080").pack(fill="x")
        self.body = tk.Frame(self, bg="#ffffff")
        self.body.pack(fill="both", expand=True)
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda e: self.cancel())
        self._size = size

    def show(self, modal=True):
        if self._size:
            center(self, self.master, *self._size)
        else:
            center(self, self.master)
        self.deiconify()
        if modal:
            self.grab_set()
            self.focus_set()
            self.wait_window(self)
        return self.result

    def cancel(self):
        self.result = None
        self.destroy()

    def button_bar(self, buttons):
        bar = Gradient(self, height=40)
        bar.pack(fill="x", side="bottom")
        inner = tk.Frame(bar, bg=hex_color(SILVER_BOTTOM))
        bar.create_window(0, 0, window=inner, anchor="ne", tags="btns")
        bar.bind("<Configure>", lambda e: bar.coords("btns", e.width - 8, 6), add="+")
        for b in buttons:
            img = image(b[2]) if len(b) > 2 else None
            ttk.Button(inner, text=b[0], command=b[1], width=10, image=img or "",
                       compound="left" if img else "none").pack(side="left", padx=3)
        return inner


def ask_string(parent, title, prompt, initial=""):
    dlg = Dialog(parent, title, size=(420, 150), resizable=False)
    tk.Label(dlg.body, text=prompt, bg="#ffffff", font=UI_BOLD).pack(anchor="w", padx=14, pady=(10, 2))
    var = tk.StringVar(value=initial)
    ent = ttk.Entry(dlg.body, textvariable=var, font=("Segoe UI", 10))
    ent.pack(fill="x", padx=14)

    def ok(_e=None):
        dlg.result = var.get().strip()
        dlg.destroy()

    dlg.button_bar([("Ok", ok), ("Cancel", dlg.cancel)])
    ent.bind("<Return>", ok)
    dlg.after(50, lambda: (ent.focus_set(), ent.select_range(0, "end")))
    return dlg.show()


class ScrolledText(tk.Frame):
    """Text + scrollbars, used by the code views."""

    def __init__(self, master, **kw):
        super().__init__(master)
        kw.setdefault("undo", True)
        self.text = tk.Text(self, wrap="none", **kw)
        ys = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        xs = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def set(self, content, readonly=False):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.edit_reset()
        if readonly:
            self.text.configure(state="disabled")

    def get(self):
        return self.text.get("1.0", "end-1c")


class ClassicTree(tk.Frame):
    """The look of the Windows TreeView (MSComctlLib.TreeCtrl) used by PWCT in the Components
    Browser: dotted lines, +/- boxes, and the selection color that is gray without focus."""

    ROW = 21
    INDENT = 26
    TEXT_X = 15

    def __init__(self, master, font=("Segoe UI", 10), on_select=None, **kw):
        super().__init__(master, bg="#ffffff", **kw)
        self.canvas = tk.Canvas(self, bg="#ffffff", highlightthickness=0, bd=0, takefocus=1,
                                yscrollincrement=self.ROW)
        ys = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=ys.set, width=200, height=200)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.font = font
        self.on_select = on_select
        self.nodes = {}
        self.roots = []
        self.sel = None
        self._rows = []
        self._pending_see = None
        c = self.canvas
        c.bind("<Configure>", lambda e: self._pending_see and self.see(self._pending_see))
        c.bind("<Button-1>", self._click)
        c.bind("<Double-Button-1>", self._double)
        c.bind("<MouseWheel>", lambda e: c.yview_scroll(-1 * (e.delta // 120) * 3, "units"))
        c.bind("<FocusIn>", lambda e: self.redraw())
        c.bind("<FocusOut>", lambda e: self.redraw())
        for key, fn in (("<Up>", lambda: self._move(-1)), ("<Down>", lambda: self._move(1)),
                        ("<Prior>", lambda: self._move(-10)), ("<Next>", lambda: self._move(10)),
                        ("<Home>", lambda: self._move(-10 ** 6)), ("<End>", lambda: self._move(10 ** 6)),
                        ("<Right>", self._right), ("<Left>", self._left),
                        ("<KP_Add>", lambda: self.item_open(self.sel, True)),
                        ("<plus>", lambda: self.item_open(self.sel, True)),
                        ("<KP_Subtract>", lambda: self.item_open(self.sel, False)),
                        ("<minus>", lambda: self.item_open(self.sel, False))):
            c.bind(key, lambda e, f=fn: (f(), "break")[1])

    # ------------------------------------------------------------ data
    def insert(self, parent, iid, text, open=True):
        self.nodes[iid] = {"text": text, "parent": parent or None, "children": [], "open": open}
        if parent:
            self.nodes[parent]["children"].append(iid)
        else:
            self.roots.append(iid)
        return iid

    def exists(self, iid):
        return iid in self.nodes

    def selection(self):
        return (self.sel,) if self.sel is not None else ()

    def parent(self, iid):
        return self.nodes[iid]["parent"]

    def item_open(self, iid, flag):
        if iid in self.nodes and self.nodes[iid]["children"] and self.nodes[iid]["open"] != flag:
            self.nodes[iid]["open"] = flag
            self.redraw()

    def selection_set(self, iid, notify=True):
        if iid not in self.nodes:
            return
        p = self.nodes[iid]["parent"]
        while p is not None:
            self.nodes[p]["open"] = True
            p = self.nodes[p]["parent"]
        self.sel = iid
        self.redraw()
        self.see(iid)
        if notify and self.on_select:
            self.on_select(iid)

    def see(self, iid):
        rows = [r[0] for r in self._rows]
        if iid not in rows:
            return
        if self.canvas.winfo_height() < 4 * self.ROW:      # not shown yet: see it at <Configure>
            self._pending_see = iid
            return
        self._pending_see = None
        i = rows.index(iid)
        top = int(round(self.canvas.canvasy(0) / self.ROW))
        visible = max(int(self.canvas.winfo_height() // self.ROW) - 1, 1)
        if i < top:
            self.canvas.yview_moveto(i / max(len(rows), 1))
        elif i >= top + visible:
            self.canvas.yview_moveto((i - visible + 1) / max(len(rows), 1))

    # ------------------------------------------------------------ drawing
    def _visible(self):
        out = []

        def walk(ids, level):
            for iid in ids:
                out.append((iid, level))
                if self.nodes[iid]["open"]:
                    walk(self.nodes[iid]["children"], level + 1)
        walk(self.roots, 0)
        return out

    def _y(self, i):
        return i * self.ROW + self.ROW // 2 + 2

    def redraw(self):
        c = self.canvas
        c.delete("all")
        self._rows = self._visible()
        index = {iid: i for i, (iid, _) in enumerate(self._rows)}
        focused = self.focus_get() is c
        line = dict(fill="#a0a0a0", dash=(1, 1))
        width = 0
        for i, (iid, level) in enumerate(self._rows):
            node = self.nodes[iid]
            x, y = 12 + level * self.INDENT, self._y(i)
            c.create_line(x, y, x + self.TEXT_X - 3, y, **line)
            sibs = self.nodes[node["parent"]]["children"] if node["parent"] else self.roots
            k = sibs.index(iid)
            if k > 0:
                c.create_line(x, self._y(index[sibs[k - 1]]), x, y, **line)
            elif node["parent"] is not None:
                c.create_line(x, self._y(index[node["parent"]]) + self.ROW // 2 - 2, x, y, **line)
            tx = x + self.TEXT_X
            t = c.create_text(tx + 3, y, text=node["text"], anchor="w", font=self.font, fill="#000000")
            if iid == self.sel:
                x1, y1, x2, y2 = c.bbox(t)
                r = c.create_rectangle(x1 - 2, y - self.ROW // 2 + 1, x2 + 2, y + self.ROW // 2 - 1,
                                       fill="#0078d7" if focused else "#e5e5e5",
                                       outline="#0078d7" if focused else "#e5e5e5")
                c.tag_lower(r, t)
                if focused:
                    c.itemconfigure(t, fill="#ffffff")
            width = max(width, c.bbox(t)[2] + 10)
        # the boxes over the lines
        for i, (iid, level) in enumerate(self._rows):
            node = self.nodes[iid]
            if not node["children"]:
                continue
            x, y = 12 + level * self.INDENT, self._y(i)
            c.create_rectangle(x - 4, y - 4, x + 4, y + 4, fill="#ffffff", outline="#919191")
            c.create_line(x - 2, y, x + 3, y, fill="#000000")
            if not node["open"]:
                c.create_line(x, y - 2, x, y + 3, fill="#000000")
        c.configure(scrollregion=(0, 0, width, len(self._rows) * self.ROW + 6))

    # ------------------------------------------------------------ events
    def _hit(self, event):
        y = self.canvas.canvasy(event.y)
        i = int((y - 2) // self.ROW)
        if 0 <= i < len(self._rows):
            iid, level = self._rows[i]
            x = self.canvas.canvasx(event.x)
            bx = 12 + level * self.INDENT
            return iid, abs(x - bx) <= 7 and self.nodes[iid]["children"], x > bx - 7
        return None, False, False

    def _click(self, event):
        self.canvas.focus_set()
        iid, on_box, on_row = self._hit(event)
        if iid is None:
            return
        if on_box:
            self.nodes[iid]["open"] = not self.nodes[iid]["open"]
            if not self.nodes[iid]["open"] and self.sel and self._inside(self.sel, iid):
                self.selection_set(iid)
            else:
                self.redraw()
        elif on_row and iid != self.sel:
            self.selection_set(iid)

    def _double(self, event):
        iid, on_box, on_row = self._hit(event)
        if iid is not None and on_row and not on_box and self.nodes[iid]["children"]:
            self.item_open(iid, not self.nodes[iid]["open"])

    def _inside(self, iid, ancestor):
        p = self.nodes[iid]["parent"]
        while p is not None:
            if p == ancestor:
                return True
            p = self.nodes[p]["parent"]
        return False

    def _move(self, delta):
        rows = [r[0] for r in self._rows]
        if not rows:
            return
        i = rows.index(self.sel) if self.sel in rows else 0
        self.selection_set(rows[max(0, min(len(rows) - 1, i + delta))])

    def _right(self):
        n = self.nodes.get(self.sel)
        if n and n["children"]:
            if n["open"]:
                self.selection_set(n["children"][0])
            else:
                self.item_open(self.sel, True)

    def _left(self):
        n = self.nodes.get(self.sel)
        if n is None:
            return
        if n["children"] and n["open"]:
            self.item_open(self.sel, False)
        elif n["parent"] is not None:
            self.selection_set(n["parent"])


PY_KEYWORDS = ("False None True and as assert async await break class continue def del elif else "
               "except finally for from global if import in is lambda nonlocal not or pass raise "
               "return try while with yield print input range len str int float").split()


def highlight_python(text_widget, lang=None):
    """Very small syntax highlighter for the code views (keywords/comment of the language)."""
    import re
    t = text_widget
    for tag in ("kw", "str", "com", "num"):
        t.tag_remove(tag, "1.0", "end")
    t.tag_configure("kw", foreground="#0000c0", font=("Consolas", 11, "bold"))
    t.tag_configure("str", foreground="#a31515")
    t.tag_configure("com", foreground="#008000")
    t.tag_configure("num", foreground="#098658")
    content = t.get("1.0", "end-1c")
    keywords = lang.keywords.split() if lang is not None and lang.keywords else PY_KEYWORDS
    comment = re.escape(lang.comment if lang is not None else "#") + r"[^\n]*"
    patterns = [("com", comment), ("str", r"(\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*')"),
                ("num", r"\b\d+(\.\d+)?\b"), ("kw", r"\b(%s)\b" % "|".join(re.escape(k) for k in keywords))]
    if lang is not None and lang.comment != "#":
        patterns.insert(0, ("kw", r"(?m)^\s*#\s*\w+"))  # #include, #ifdef ...
    taken = []
    for tag, pat in patterns:
        for m in re.finditer(pat, content):
            s, e = m.span()
            if any(a <= s < b for a, b in taken):
                continue
            if tag in ("com", "str"):
                taken.append((s, e))
            t.tag_add(tag, "1.0+%dc" % s, "1.0+%dc" % e)
