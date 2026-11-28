"""tests/gui_layout_gate.py with every dialog answered at once (no_popups.py). Same output and exit code."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tests"))
import gui_layout_gate  # noqa: E402
from no_popups import PRELUDE  # noqa: E402

gui_layout_gate._WORKER = PRELUDE + gui_layout_gate._WORKER
sys.exit(gui_layout_gate.main())
