"""tests/gui_layout_gate.py with every dialog answered at once (no_popups.py). Same output and exit code."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tests"))
import gui_layout_gate  # noqa: E402
import subprocess  # noqa: E402

from no_popups import PRELUDE, run_bounded  # noqa: E402

PER_GUI_TIMEOUT = 120  # the gate's own 300 s, times two Pythons, is too long for a CI step


class _Bounded:
    """Stands in for the subprocess module inside gui_layout_gate: run() kills the whole tree on timeout."""

    TimeoutExpired = subprocess.TimeoutExpired

    @staticmethod
    def run(cmd, capture_output=True, text=True, timeout=None, cwd=None):
        return run_bounded(cmd, min(timeout or PER_GUI_TIMEOUT, PER_GUI_TIMEOUT), cwd=cwd)


gui_layout_gate.subprocess = _Bounded

gui_layout_gate._WORKER = PRELUDE + gui_layout_gate._WORKER
sys.exit(gui_layout_gate.main())
