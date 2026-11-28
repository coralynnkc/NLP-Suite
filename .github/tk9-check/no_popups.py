"""Code put in front of the layout gate's and the gallery's per-GUI worker: answers every dialog at once.

On a runner nobody clicks, so a GUI that shows a popup while it opens (14 do: "requires a csv FILE in INPUT;
RUN is disabled" and the like) waited for the worker's 300 s timeout, twice per GUI (Tk 8.6 and Tk 9), and
the layout gate ran over two hours in run 46120257866. The answers are bundle_gate.py's: OK, No, Cancel.
Windows are NOT hidden here (the gallery screenshots them).
"""

import os

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
# Nothing a GUI starts while it opens may run (another GUI via run_script, a program, a shell command), as in
# bundle_gate.py: a child that outlives the worker keeps its output pipe open, and the gate then waits forever.
import subprocess as _sp, os as _os
class _FakePopen:
    def __init__(self, args, *a, **k):
        print("LAUNCH", str(args)[:120], file=_sys.stderr)
        self.args, self.returncode, self.pid, self.stdout, self.stderr, self.stdin = args, 0, 0, None, None, None
        text = k.get("text") or k.get("universal_newlines") or k.get("encoding") or k.get("errors")
        self._empty = "" if text else b""
    def poll(self): return 0
    def wait(self, timeout=None): return 0
    def communicate(self, input=None, timeout=None): return (self._empty, self._empty)
    def kill(self): pass
    def terminate(self): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
_sp.Popen = _FakePopen
_os.system = lambda cmd: (print("LAUNCH", str(cmd)[:120], file=_sys.stderr), 0)[1]
if hasattr(_os, "startfile"):
    _os.startfile = lambda *a, **k: print("LAUNCH startfile", a[:1], file=_sys.stderr)
"""


def run_bounded(cmd, timeout, cwd=None):
    """subprocess.run(cmd, capture_output=True, text=True, timeout=timeout), except that on a timeout the
    whole process tree is killed and the call returns. subprocess.run kills only the child and then waits
    for the pipes to close, which never happens while a grandchild holds them."""
    import signal
    import subprocess

    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace", **kw)
    try:
        out, err = p.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd, p.returncode, out, err)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
        try:
            p.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        raise subprocess.TimeoutExpired(cmd, timeout) from None
