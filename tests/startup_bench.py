#!/usr/bin/env python
"""Startup benchmark: how long the NLP Suite takes to start, compared across builds or environments.

WHY THIS EXISTS
docs/future-work.md §6 measured where GUI opening time goes (9 Nov 2026, Windows, Python 3.10) by hand.
This script repeats those measurements on any number of Pythons, so a change of Python, a dependency
bump or a lazy-import PR can be compared against the build before it with the same commands (§6.10
step 5).

It times, in a fresh process each time:
  python     the interpreter alone (`python -c pass`)
  libs       each heavy third-party library imported alone
  gui_util   `import GUI_util` (with its Tk window hidden): what every GUI pays before its own code
  guis       every src/*_main.py built under the real Tk, windows hidden, event loop skipped, popups
             recorded (the harness of tests/bundle_gate.py), from process start to the end of the build

Targets are given as LABEL=PATH, where PATH is an unzipped NLP Suite (its python-env and src/ are used)
or LABEL=PYTHON:SRC for a dev environment and a source checkout. Each measurement is repeated
--repeat times and the median kept, with the first run kept apart as "first" (on a fresh unzip, that
is a student's first open: Python compiles and caches whatever the zip did not ship as .pyc); the targets take turns on every repeat, so background load falls on
all of them alike.

USAGE
  python tests/startup_bench.py run 1.6.46=<unzipped 1.6.46> 1.6.47=<unzipped 1.6.47> -o bench.json
  python tests/startup_bench.py report bench.json            # Markdown tables, ratio to the first target

It writes only a temporary HOME and the -o file.
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bundle_gate  # noqa: E402

LIBS = [
    "pandas",
    "numpy",
    "scipy",
    "sklearn",
    "openpyxl",
    "matplotlib",
    "plotly",
    "seaborn",
    "nltk",
    "spacy",
    "stanza",
    "gensim",
    "textblob",
    "textstat",
    "spacy_langdetect",
    "torch",
    "transformers",
    "sentence_transformers",
    "fastcoref",
    "bertopic",
    "pyLDAvis",
    "wordcloud",
    "folium",
    "geopy",
    "requests",
    "customtkinter",
]

_GUI_UTIL = (
    "import os, sys, tkinter; src = sys.argv[1]; sys.path.insert(0, src); os.chdir(src)\n"
    "_i = tkinter.Tk.__init__\n"
    "def h(self, *a, **k):\n    _i(self, *a, **k); self.withdraw()\n"
    "tkinter.Tk.__init__ = h\n"
    "import GUI_util\n"
    "os._exit(0)\n"
)


def parse_target(spec):
    """LABEL=BUNDLE or LABEL=PYTHON:SRC -> (label, python, src)."""
    label, sep, path = spec.partition("=")
    if not sep or not label or not path:
        raise SystemExit("A target is LABEL=PATH or LABEL=PYTHON:SRC, not " + repr(spec))
    if os.path.isdir(path):
        return label, bundle_gate.bundle_python(path), os.path.join(os.path.abspath(path), "src")
    py, sep, src = path.partition(":")
    if not sep:
        raise SystemExit(path + " is not a folder; for a dev env give PYTHON:SRC")
    return label, py, os.path.abspath(src)


def _timed(cmd, cwd, home, timeout=300):
    # Unlike bundle_gate, let Python write bytecode, as it does on a user's machine: otherwise every run
    # recompiles whatever the zip did not ship as .pyc, and the medians measure the compiler.
    env = bundle_gate._env(home)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    start = time.perf_counter()
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        code, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        code, out, err = None, "", "timed out after " + str(timeout) + " s"
    return time.perf_counter() - start, code, out, err


def measure(py, src, kind, name, home):
    """One fresh-process measurement: (seconds, error or '')."""
    if kind == "python":
        secs, code, _, err = _timed([py, "-c", "pass"], src, home)
    elif kind == "libs":
        secs, code, _, err = _timed([py, "-c", "import " + name], tempfile.gettempdir(), home)
    elif kind == "gui_util":
        secs, code, _, err = _timed([py, "-c", _GUI_UTIL, src], src, home)
    else:
        secs, code, out, err = _timed([py, "-c", bundle_gate._GUI_HARNESS, src, name], src, home, 240)
        rec = next(
            (json.loads(x[len(bundle_gate.MARK) :]) for x in out.splitlines() if x.startswith(bundle_gate.MARK)), None
        )
        if rec is None:
            return secs, bundle_gate._last_line(err) or "no result"
        return secs, "" if rec["status"] == "ok" else rec["status"] + ": " + rec["error"]
    return secs, "" if code == 0 else (bundle_gate._last_line(err) or "exit code " + str(code))


def plan(targets, libs, guis_filter=None):
    """The (kind, name) list, in the order measured."""
    src = targets[0][2]
    guis = sorted(fn for fn in os.listdir(src) if fn.endswith("_main.py"))
    if guis_filter:
        guis = [g for g in guis if g in guis_filter]
    return [("python", "")] + [("libs", n) for n in libs] + [("gui_util", "")] + [("guis", g) for g in guis]


def run(targets, repeat, out_path, *, kinds=None, guis_filter=None, log=bundle_gate.out):
    home = tempfile.mkdtemp(prefix="startup_bench_home_")
    for _label, _py, src in targets:
        bundle_gate.seed_config(os.path.dirname(src))
    items = [i for i in plan(targets, LIBS, guis_filter) if not kinds or i[0] in kinds]
    result = {
        "started": time.strftime("%Y-%m-%d %H:%M"),
        "machine": os.uname().machine if hasattr(os, "uname") else sys.platform,
        "repeat": repeat,
        "targets": {},
    }
    for label, py, src in targets:
        ver = subprocess.run(
            [py, "-c", "import sys, tkinter; print(sys.version.split()[0], tkinter.TkVersion)"],
            capture_output=True,
            text=True,
        ).stdout.split()
        result["targets"][label] = {"python": py, "src": src, "version": ver, "times": {}}
    for kind, name in items:
        key = kind + ":" + name if name else kind
        samples = {label: [] for label, _, _ in targets}
        errors = {label: "" for label, _, _ in targets}
        for _ in range(repeat):
            for label, py, src in targets:
                secs, err = measure(py, src, kind, name, home)
                samples[label].append(secs)
                errors[label] = errors[label] or err
        for label in samples:
            result["targets"][label]["times"][key] = {
                "median": round(statistics.median(samples[label][1:] or samples[label]), 2),
                "first": round(samples[label][0], 2),
                "samples": [round(s, 2) for s in samples[label]],
                "error": errors[label],
            }
        log(key + "  " + "  ".join(f"{lb} {s[0]:.2f}/{statistics.median(s[1:] or s):.2f}" for lb, s in samples.items()))
        with open(out_path, "w") as f:
            json.dump(result, f, indent=1)
    return result


def report(result):
    """Markdown tables: for each target the first run and the median of the rest, then warm ratios."""
    labels = list(result["targets"])
    base = labels[0]
    warm_of = "median of runs 2-" + str(result["repeat"]) if result["repeat"] > 1 else "one run"
    head = "| | " + " | ".join(lb + " first | " + lb + " warm" for lb in labels)
    head += "".join(" | " + lb + " / " + base for lb in labels[1:]) + " |"
    rule = "|" + "---|" * (1 + 2 * len(labels) + len(labels) - 1)
    lines = []
    sections = (
        ("python", "Interpreter"),
        ("gui_util", "import GUI_util"),
        ("libs", "Libraries alone"),
        ("guis", "GUI open"),
    )
    for kind, title in sections:
        keys = [k for k in result["targets"][base]["times"] if k.split(":")[0] == kind]
        if not keys:
            continue
        lines += ["", "### " + title + " (s; warm = " + warm_of + ")", "", head, rule]
        tot = {lb: [0.0, 0.0] for lb in labels}
        for k in keys:
            row = []
            for lb in labels:
                t = result["targets"][lb]["times"].get(k, {})
                tot[lb][0] += t.get("first", 0)
                tot[lb][1] += t.get("median", 0)
                mark = " ✗" if t.get("error") else ""
                row += [f"{t.get('first', float('nan')):.2f}", f"{t.get('median', float('nan')):.2f}" + mark]
            b = result["targets"][base]["times"][k]["median"]
            row += [f"{result['targets'][lb]['times'][k]['median'] / b:.2f}" if b else "-" for lb in labels[1:]]
            lines.append("| " + (k.split(":", 1)[1] if ":" in k else k) + " | " + " | ".join(row) + " |")
        if len(keys) > 1:
            row = [f"{v:.1f}" for lb in labels for v in tot[lb]]
            row += [f"{tot[lb][1] / tot[base][1]:.2f}" if tot[base][1] else "-" for lb in labels[1:]]
            lines.append("| **total** | " + " | ".join(row) + " |")
    errs = [(lb, k, t["error"]) for lb in labels for k, t in result["targets"][lb]["times"].items() if t["error"]]
    if errs:
        lines += ["", "✗ = did not build or import:"] + [f"- {lb} {k}: {e}" for lb, k, e in errs]
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("run")
    pr.add_argument("targets", nargs="+")
    pr.add_argument("-o", "--out", required=True)
    pr.add_argument("--repeat", type=int, default=3)
    pr.add_argument("--only", nargs="*", help="kinds to measure: python libs gui_util guis")
    pr.add_argument("--guis", nargs="*", help="only these *_main.py files")
    pp = sub.add_parser("report")
    pp.add_argument("file")
    a = p.parse_args(argv)
    if a.cmd == "run":
        run([parse_target(t) for t in a.targets], a.repeat, a.out, kinds=a.only, guis_filter=a.guis)
        bundle_gate.out(report(json.load(open(a.out))))
    else:
        bundle_gate.out(report(json.load(open(a.file))))


if __name__ == "__main__":
    main()
