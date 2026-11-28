"""gui_harness_util: the unattended prelude and the bounded run used by gui_layout_gate and gui_gallery."""

import os
import subprocess
import sys
import time

import gui_harness_util as h
import pytest

try:
    import tkinter  # noqa: F401  # the prelude patches tkinter's dialogs

    HAVE_TK = True
except ImportError:
    HAVE_TK = False


def test_run_bounded_returns_at_the_timeout_although_a_grandchild_holds_the_pipe():
    child = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); time.sleep(60)"
    start = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        h.run_bounded([sys.executable, "-c", child], 2)
    assert time.monotonic() - start < 20  # subprocess.run waited the whole 60 s for the grandchild's pipe


def test_run_bounded_returns_output_and_code():
    r = h.run_bounded(
        [sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"], 30
    )
    assert (r.returncode, r.stdout.strip(), r.stderr.strip()) == (3, "out", "err")


@pytest.mark.skipif(not HAVE_TK, reason="needs tkinter")
def test_unattended_answers_dialogs_and_starts_nothing(tmp_path):
    marker = tmp_path / "ran.txt"
    code = h.UNATTENDED + (
        "\nimport tkinter.messagebox as mb, subprocess, os, sys"
        "\nprint(mb.showwarning(title='t', message='m'), mb.askyesno('q', 'm'))"
        f'\np = subprocess.Popen([sys.executable, \'-c\', \'open(r"{marker}", "w").write("x")\'])'
        "\nprint('wait', p.wait())"
        f"\nos.system('echo x > \"{marker}\"')"
    )
    r = h.run_bounded([sys.executable, "-c", code], 60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["ok", "False", "wait", "0"]
    assert "POPUP showwarning" in r.stderr and "LAUNCH" in r.stderr
    assert not os.path.exists(marker)
