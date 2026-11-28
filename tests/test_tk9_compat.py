"""src/ runs on Tcl/Tk 9 as well as 8.6 (docs/future-work.md §3.3, 1.6.49).

Tcl 9 removed `trace variable`, which tkinter's Variable.trace() / trace_variable() call: in the first 1.6.47
candidate, built on a Python with Tcl/Tk 9, every GUI with a `.trace("w", ...)` crashed as it opened (54 GUIs).
Variable.trace_add("write", ...) exists on both 8.6 and 9. This fails on any old-style trace left in src/,
comments included, so a line that is uncommented later is already ported.
"""

import glob
import os
import re

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
OLD = re.compile(r"\.(trace|trace_variable|trace_vdelete|trace_vinfo)\(\s*['\"]?[wru]?['\"]?")


def test_no_old_style_variable_traces():
    found = []
    for path in sorted(glob.glob(os.path.join(SRC, "*.py"))):
        with open(path, encoding="utf-8-sig") as f:
            for n, line in enumerate(f, 1):
                for m in OLD.finditer(line):
                    if line[: m.start()].rstrip().endswith("np"):  # numpy.trace (the matrix trace)
                        continue
                    found.append(f"{os.path.basename(path)}:{n}: {line.strip()[:100]}")
    assert not found, "use .trace_add('write', callback):\n" + "\n".join(found)
