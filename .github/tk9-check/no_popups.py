"""Code put in front of the layout gate's and the gallery's per-GUI worker: answers every dialog at once.

On a runner nobody clicks, so a GUI that shows a popup while it opens (14 do: "requires a csv FILE in INPUT;
RUN is disabled" and the like) waited for the worker's 300 s timeout, twice per GUI (Tk 8.6 and Tk 9), and
the layout gate ran over two hours in run 46120257866. The answers are bundle_gate.py's: OK, No, Cancel.
Windows are NOT hidden here (the gallery screenshots them).
"""

PRELUDE = r"""
import tkinter.messagebox as _mb, tkinter.filedialog as _fd, webbrowser as _wb, sys as _sys
def _answer(kind, value):
    def f(*a, **k):
        print("POPUP", kind, str(k.get("title", a[0] if a else ""))[:80], file=_sys.stderr)
        return value
    return f
for _k in ("showinfo", "showwarning", "showerror"):
    setattr(_mb, _k, _answer(_k, "ok"))
for _k in ("askyesno", "askokcancel", "askretrycancel", "askyesnocancel"):
    setattr(_mb, _k, _answer(_k, False))
_mb.askquestion = _answer("askquestion", "no")
for _k in ("askopenfilename", "askopenfilenames", "askdirectory", "asksaveasfilename"):
    setattr(_fd, _k, _answer(_k, ""))
_wb.open = _wb.open_new = _wb.open_new_tab = _answer("webbrowser", True)
import tkinter as _tk
_tk.Misc.wait_window = lambda self, window=None: None
"""
