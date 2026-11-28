"""Windows only: what DPI mode does this Python's Tk put the process in, and what does Tk measure?

PLAN 1.6.49 step 3: the Suite does not declare itself DPI-aware. If Tk 9 does so on its own, Windows
stops scaling the window as one picture and text outgrows the placed coordinates. This prints the
process's DPI awareness before and after creating a Tk root, plus Tk's own measurements.
"""

import ctypes
import sys
import tkinter as tk
import tkinter.font as tkfont

user32 = ctypes.windll.user32
shcore = ctypes.windll.shcore


def awareness():
    v = ctypes.c_int(-1)
    try:
        shcore.GetProcessDpiAwareness(None, ctypes.byref(v))
    except OSError as e:
        return f"GetProcessDpiAwareness failed: {e}"
    names = {0: "UNAWARE", 1: "SYSTEM_AWARE", 2: "PER_MONITOR_AWARE"}
    return f"{v.value} ({names.get(v.value, '?')})"


print("python", sys.version.split()[0])
print("before Tk: awareness", awareness())
r = tk.Tk()
print("tk", r.tk.call("info", "patchlevel"))
print("after Tk:  awareness", awareness())
try:
    print("GetDpiForSystem", user32.GetDpiForSystem())
    print("GetDpiForWindow(root)", user32.GetDpiForWindow(int(r.wm_frame(), 16)))
except (AttributeError, OSError, ValueError) as e:
    print("GetDpiFor* failed:", e)
print("tk scaling", r.tk.call("tk", "scaling"))
print("winfo fpixels 1i", r.winfo_fpixels("1i"))
print("screen", r.winfo_screenwidth(), "x", r.winfo_screenheight())
for fam, size in (("Courier", 12), ("Arial", 12), ("TkDefaultFont", 0)):
    f = tkfont.Font(family=fam, size=size) if size else tkfont.nametofont(fam)
    print(f"font {fam} {size or f.cget('size')}: width('NLP Suite tool')={f.measure('NLP Suite tool')} linespace={f.metrics('linespace')}")
r.destroy()
