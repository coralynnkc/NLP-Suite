import sys
import tkinter as tk
from tkinter import ttk

r = tk.Tk()
t = r.tk
print("python", sys.version.split()[0], "| tk", t.call("info", "patchlevel"))


def ev(s):
    try:
        return repr(t.eval(s))
    except tk.TclError as e:
        return "ERR: " + str(e)[:110]


# 1. Non-BMP text
for w in (tk.Text(r), tk.Entry(r)):
    s = "emoji \U0001f600 math \U0001d400 x"
    try:
        w.insert("end", s)
        got = w.get("1.0", "end-1c") if isinstance(w, tk.Text) else w.get()
        print(f"non-BMP {type(w).__name__}: roundtrip={got == s} len={len(got)} expected={len(s)}")
    except Exception as e:
        print(f"non-BMP {type(w).__name__}: ERR {e}")
lab = tk.Label(r, text="\U0001f600")
print("non-BMP Label cget:", lab.cget("text") == "\U0001f600")

# 2. SVG photo
svg = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><circle cx="10" cy="10" r="8" fill="red"/></svg>'
for fmt in ("svg", "svg -scale 2"):
    try:
        im = tk.PhotoImage(data=svg, format=fmt)
        print(f"svg photo format={fmt!r}: {im.width()}x{im.height()}")
    except tk.TclError as e:
        print(f"svg photo format={fmt!r}: ERR {e}")

# 3-5. tk subcommands
print("tk print:", ev("tk print"))
print("tk systray:", ev("tk systray"))
print("tk sysnotify:", ev("tk sysnotify"))
print("tk accessible:", ev("tk accessible"))
print("tk subcommands:", ev("tk bogus"))

# 6. events
print("bind <TouchpadScroll>:", ev("bind . <TouchpadScroll> {}"))
print("bind <Shift-MouseWheel>:", ev("bind . <Shift-MouseWheel> {}"))

# 7. ttk scaling
print("tk scaling:", ev("tk scaling"))
print("ttk themes:", ev("ttk::style theme names"))
print("ttk::checkbutton indicator elements:", ev("ttk::style element names"))

# context: removed command
print("trace variable (old API):", ev("set ::x 1; trace variable ::x w {}"))
print("tcl_version:", ev("info tclversion"))
