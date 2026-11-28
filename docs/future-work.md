# Future work — NLP Suite

The findings behind the "Future work" list in [PLAN.md](../PLAN.md): evidence, line numbers, proposed fixes. PLAN.md says what is next; this file says why and how. What has shipped is in [CHANGELOG.md](../CHANGELOG.md): this file lists open items only, so delete an item (or the fixed part of it) in the PR that fixes it.

Moved out of PLAN.md on 11 Nov 2026. The sections keep their scan dates; nothing here was re-checked by the move. The issue lists are proposals for Roberto: nothing in them has been closed or commented on.

## Contents

- [1. Dead code (scan of 10 Nov 2026)](#1-dead-code-scan-of-10-nov-2026)
- [2. Bundle size (scan of 11 Nov 2026)](#2-bundle-size-scan-of-11-nov-2026)
- [3. Python and pinned dependencies (after 1.6.47)](#3-python-and-pinned-dependencies-after-1647)
- [5. Outdated copy and flows (scan of 9 Nov 2026)](#5-outdated-copy-and-flows-scan-of-9-nov-2026)
- [6. Performance: slow GUI opening and "downloading"](#6-performance-slow-gui-opening-and-downloading)
- [7. UI overhaul: findings (10 Nov 2026)](#7-ui-overhaul-findings-10-nov-2026)
- [9. Open pull requests](#9-open-pull-requests)
- [10. Recent issues (2025–2026)](#10-recent-issues-20252026)
- [11. The 2021–2024 backlog](#11-the-20212024-backlog)
- [12. Tech debt](#12-tech-debt)
- [13. Branches](#13-branches)
- [14. Requirements, release checks and settled decisions](#14-requirements-release-checks-and-settled-decisions)
- [15. The updater: known limits](#15-the-updater-known-limits)

---

## 1. Dead code (scan of 10 Nov 2026)

**How it was found:** every `src/*.py` whose module name appears nowhere else in `src/`, `tests/`, `lib/`, the specs, the workflows or the setup scripts (`grep -w`), plus the §5.1 findings. A mention in a comment counts as a use, so the list is short of complete (`videos_util` was found only by reading). Not swept: dead functions and branches inside live modules (§12.7 counts 496 unused variables); `lib/` data files; TIPS pdfs no GUI names.

### 1.1 Kept from #1706

#1706 (1.6.48) deleted the files §1.1 listed except `post_build_fixup.py`: `NLP_Suite.spec` names it as the local-build counterpart of the workflow's "Copy data directories to dist" step, and it patches `python-env/bin` shebangs (`194365c5`). It is not dead while anyone builds locally. Delete it only together with a note in the spec on how to build locally without it.

### 1.2 Looks dead, is not

- `src/network_graph_app.py` and `NetworkGraphViewer.spec`: the standalone Network Graph Viewer, built by `build-network-viewer.yml` on `ngv-*` tags.
- `setup_SRL.py`: sets up the SRL environment for source runs (§5.1 #2).
- `requirements-mac.txt`, `requirements-windows.txt` (root): installed by `build-installers.yml`.

### 1.3 Later

- `NLP_menu_main`: `setup_external_software_warning` is never called (§5.1 #7). `setup_external_programs_checkbox` is called and runs `java -version` at every start (§6.8), so it goes with that decision, not here.
- `MEMO_Development_Notes.md`, `docs/CustomTkinter-Migration-Plan.md`: a "historical" banner or delete (§5.1 #19).
- `NLP_welcome_main.py`: dead once §5.1 #6 removes the redirect.
- Stale remote branches (§13).
- A `vulture src/` pass for dead functions. Expect false positives: GUI callbacks are bound by name and modules are launched by string.

## 2. Bundle size (scan of 11 Nov 2026)

**Where it stands:** 1.6.44 trimmed the spec to what the menu runs, dropped TensorFlow and 14 packages nothing imports, and recompressed 42 TIPS pdfs (1,332 → 775 MB on the Mac, 1,541 → 863 MB on Windows, CI builds of 13 Nov). Zips since: 1.6.46 723 MB (Mac) and 792 MB (Windows); 1.6.47 789 and 859 MB: Python 3.11 with torch 2.15 and transformers 5 grew the unpacked `python-env` from 1,792 to 2,037 MB (`bundle_gate.py`, 23 Nov). What is left is below.

**How it was found:** `gh release view` for the asset sizes; reading `NLP_Suite.spec`, `build-installers.yml` and `run_script_util.py`; a `grep` of `src/*.py` for an `import`/`from` of each package in `requirements*.txt`, then for any mention of the ones with no import. **Not measured:** per-package sizes inside the zip. The figures below that say "estimate" need one release zip unpacked and `du` run on `_internal/` and `python-env/.../site-packages` by package (not possible on Cora's machine; do it on the machine that runs the pre-tag build).

### 2.1 What is left in `_internal/`

The PyInstaller executable runs only the menu; every tool runs on `python-env`. `release/v1.6.44` trims the spec to what the menu reaches, but keeps spacy, numpy, pandas, scipy, matplotlib, plotly and openpyxl because the menu's language advisor imported `spaCy_util` in-process. Since #1732 (1.6.43) the advisor runs on `python-env` and imports no package util, so those can probably go too: check with a probe build (an entry script importing every module the menu imports) before cutting.

**No PyInstaller at all** stays the larger option: a small launcher that runs `python-env/python src/NLP_menu_main.py`. It removes `_internal/` entirely but changes the Mac `codesign` step, the `.command` launcher, the Windows DLL copy step, and what `get_java_executable()` and the updater take as the app dir (`sys.executable`'s folder). Only if the trim leaves too much.

### 2.2 Requirements and data, still open

- `umap-learn`, `hdbscan`: not imported, but BERTopic depends on them; keep.
- `lib/namesGender` (34 MB of CSV) compresses well in the zip already; leave it.
- A §1.3 `vulture` pass is cleanup, not size.

### 2.5 The checks

On each candidate:
- `tests/bundle_gate.py` against the last release (`DO_NOT_TRACK=1`).
- zip size on both OSes; the menu opens from the zip on Windows and on a Mac; `gui_smoke.py`; one tool from each family run from the zip (BERT NER and sentiment, BERTopic, coreference with fastcoref, a CoreNLP parse via the bundled JRE, GIS map, wordclouds, an Excel chart).
- 14.1: the self-updater 1.6.(n−1) → n still finds its manifest and keeps user files.

## 3. Python and pinned dependencies (after 1.6.47)

### 3.1 What 1.6.47 closed

1.6.47 (23 Nov 2026) moved the build and the bundled `python-env` to Python 3.11, Pillow to 13.0.0 and transformers to 5.x, and deleted `src/requirements*.txt` and `bert-extractive-summarizer` (nothing called it; it held transformers below 4.52). Dependabot on `current-stable` right after the promotion: **0 open, 179 fixed that day.** Re-read it when a requirement changes; `.github/dependabot.yml` is still not wanted (version-update PRs would fight the deliberate pins below).

Not seen by Dependabot: the SRL env (`setup_SRL.py`: `transformer-srl==2.4.6`, torch 1.7, allennlp, spaCy 2, Python 3.8). Old, with advisories of its own, but opt-in and local, with no newer release to move to.

### 3.2 Held back on purpose

Each of these was found while testing 1.6.47 and is pinned or patched so that release changed only Python and the security packages. Each is its own later change, checked with the tool sweep.

| What | Where | Why it is held | To move it |
|---|---|---|---|
| Tcl/Tk 8.6: python-build-standalone `20251217`, CPython 3.11.14 | `build-installers.yml` (`PBS_TAG`, and a step that fails the build if python-env's Tcl is not 8.6) | From `20260113` on, the Mac (and Linux) 3.11 builds carry Tcl/Tk 9 (`20261110`: 3.11.18 with 9.0.4); the Windows 3.11.18 of `20261124` still carries 8.6.15 (its build log, 28 Nov). Tcl 9 removed `trace variable`, so every GUI that calls `.trace("w", ...)` crashed at open (54 in the first candidate). 3.11.14 lacks four CPython patch releases | §3.3: ported on `chore/tcl9-trace-add`, the bump on `chore/1.6.49-python-3.11.18` (1.6.49) |
| `pandas>=2.2,<3` | `requirements.txt` | Python 3.10 held it at 2.x; on 3.11 it resolves to 3.1 (default string dtype, copy-on-write). Two tests failed on it (`test_conll_sentence_table`, `test_shape_of_stories_clustering`) | A migration of its own: the pandas 3 deprecation warnings on 2.3 first, then the sweep |
| `folium<1`, `ipython<9` | `requirements.txt` | 3.11 lifts them to 1.0 and 9; held so GIS maps and pyLDAvis change only when tested for it | Lift one at a time; the GIS and topic-modeling recipes |
| fastcoref 2.1.6 patched at load | `coreference_neural_util.patch_fastcoref_post_init` | Unmaintained since 2023; on transformers 5 `FCorefModel` misses `post_init()` ("no attribute 'all_tied_weights_keys'"). The patch calls it; weights and clusters match 4.51.3 | Drop the patch if fastcoref gets a release, or replace fastcoref |
| Transitive moves 3.11 brought | python-dateutil 3 → 4, datasets 2.14 → 5.2 (fastcoref), numpy 2.2 → 2.4, scikit-learn 1.7 → 1.9, scipy 1.15 → 1.17 | Not pinned: the 1.6.47 sweep showed no change from them | Watch in the next sweeps |

The local dev env for 3.11 is `NLP311` (conda, Python 3.11.18, Tcl 8.6.15). It did not catch the Tcl 9 crash, because conda's Python has Tcl 8.6: only a sweep or `bundle_gate.py` on the built zip did.

### 3.3 Tcl/Tk 9 (1.6.49)

Goal: bundle the newest CPython 3.11 from python-build-standalone, which on the Mac now comes only with Tcl/Tk 9; the Windows build of the same release (`20261124`, 3.11.18) still has Tcl/Tk 8.6.15. Where each step stands (27 Nov; Windows 28 Nov):

1. **A Tcl 9 dev env: done.** `~/Documents/NLP_output/candidates/tcl9-env/python` is `cpython-3.11.18+20261124` for the Mac (Tcl/Tk 9.0.4, SHA256 checked), with `requirements.txt`, `requirements-mac.txt` and `en_core_web_sm` installed. Every `*_main.py` built on it with `bundle_gate.py`'s harness (real Tk, windows hidden): with `roberto`'s `src/`, 54 crash at open (`bad option "variable": must be add, info, or remove`), as in the first 1.6.47 candidate, so the env reproduces the problem.
2. **Port the traces: done, `chore/tcl9-trace-add`.** 286 `.trace("w", cb)` calls in 51 files (commented-out ones included) became `.trace_add("write", cb)`, which Tcl 8.6 has too, so it can merge before the Python moves. No callback reads the mode argument (an AST scan of every callback). `tests/test_tk9_compat.py` fails on any old-style trace left in `src/`. With the port, 54 GUIs build on Tcl 9 and `NLP_setup_IO_main` exits while opening, as it does on 8.6 (1.6.47's bundle gate).
3. **The rest of Tk 9: done on the Mac, `chore/tcl9-trace-add`.** Two bundles that differ only in their Python (3.11.14/Tk 8.6 and 3.11.18/Tk 9), same `src/`, `config/`, `TIPS/` and `jre/`, in `~/Documents/NLP_output/candidates/tcl9-env/pair-*`:
   - **At open, the same on both:** every GUI's status, and the popups and launches it records, match for all 55 (`pair-tk86.json`, `pair-tk9.json`).
   - **Layout: Tk 9 drew fonts a third larger.** Tk 8.6 on the Mac drew N points as N pixels; Tk 9 draws 4/3 N and ignores `tk scaling` for fonts (Courier 12 measured 260 px at every scaling from 0.5 to 2). `gui_layout_gate.py` (windows made transparent with `-alpha 0`, so nothing showed on screen): Tk 8.6 49 pass, 1 fail (wordclouds, 71 px, already there); Tk 9 11 pass, 39 fail (overflow up to 452 px). `src/tk9_fonts_util.py`, applied by `GUI_util` and `GUI_IO_util` before the first window, turns point size N into pixel size -N in widget options, ttk styles and `tkinter.font.Font`, on macOS with Tk 9 only. With it Tk 9 matches 8.6 exactly: 49 pass, the same wordclouds overflow.
   - **Still to look at:** Windows Tk 9 does not arise in 1.6.49 (below); the shim does nothing on Windows. Left: `tkcolorpicker`'s dialog, `PhotoImage` formats, and a look at a few GUIs by a person (the gate measures geometry, not looks). The frozen menu (`_internal`) runs on the build runner's own Python, which keeps Tcl 8.6, so the Windows Tcl DLL list in `build-installers.yml` does not change; the self-updater's window and the Network Graph app use `pack`, which grows to fit.
4. **The bump: on `chore/1.6.49-python-3.11.18`, not built.** `PBS_TAG` `20261124`, `PY_VER` `3.11.18`, both SHA256 lines from that release's `SHA256SUMS`, and the Tcl check (9 on the Mac, 8.6 on Windows: item 5). Still to do once a candidate is built: the full tool sweep against 1.6.48, the bundle gate, the self-updater (a second python-env swap), and a Windows check (everything above ran on a Mac).
5. **Windows stays on Tk 8.6.** The first Windows build with this branch's `build-installers.yml` (run 46118332937 on `claude/tcl9-gui-upgrades-0fr6u2`) stopped at the build's Tcl check: `python-env has Tcl/Tk 8.6.15` (python-build-standalone `20261124`, `x86_64-pc-windows-msvc`). The check now expects 9 on the Mac and 8.6 on Windows. So on Windows 1.6.49 changes the Python, not the toolkit: the DPI question (whether Tk 9 declares the process DPI-aware, and what 150 % scaling then does to the placed layout) waits until a Windows build moves to Tk 9, and any Tk 9 feature (SVG images, `tk sysnotify`, `tk print`) needs a fallback on Windows.

### 3.4 Tcl/Tk 9 on Windows means Python 3.14 (resolution check, 28 Nov 2026)

Which python-build-standalone `20261124` Windows builds (`x86_64-pc-windows-msvc`) carry which Tcl/Tk, from the DLLs in each archive: 3.11.18, 3.12.16 and 3.13.18 have `tcl86t.dll`/`tk86t.dll` (8.6); 3.14.10 and 3.15.2 have `tcl90.dll`/`tcl9tk90.dll` (9.0). So Windows gets Tk 9 only with Python 3.14. Nothing needs it now (1.6.49 gets the CPython patches on 8.6); it matters for a Tk 9 feature on Windows, and for Python 3.11's end of life (October 2027).

`uv pip compile requirements.txt requirements-<os>.txt` (uv 0.11.32, PyPI on 28 Nov), Windows x64 and macOS arm64, Python 3.11 and 3.14:
- **Both resolve, to the same 174 (Windows) / 175 (Mac) packages.** Only five versions move on 3.14: numpy 2.4.6 → 2.5.5, scipy 1.17.1 → 1.18.1, contourpy 1.3.3 → 1.4.0, networkx 3.6.1 → 3.7, soupsieve 2.10 → 4.1.3. The heavy ones are unchanged and have cp314 wheels for both platforms: torch 2.15.0, transformers 5.24.1, spaCy 3.8.18 (thinc 8.3.14, blis 1.3.4), stanza 1.15.1, sentence-transformers 6.3.0, bertopic 0.17.4 (hdbscan 0.8.44, umap-learn 0.6.0, numba 0.68.1), scikit-learn 1.9.1, pandas 2.3.3, Pillow 13.0.0.
- **gensim is the blocker.** Its latest release, 4.4.0 (Oct 2025), has wheels for cp39–cp313 only, so on 3.14 pip builds it from source (C/Cython, against numpy 2.5 and scipy 1.18) on the build runner. Not tried. It is used by `word2vec_Gensim_util`, `topic_modeling_gensim_util` and `statistics_txt_util`.
- **Source-only on 3.11 too** (pure Python, install today): autocorrect, fastcoref, langdetect, langid, pycorenlp, simplekml.
- **Not checked:** whether anything runs on 3.14 (fastcoref, unmaintained since 2023, subclasses transformers internals; pyLDAvis; tkcolorpicker), the frozen menu's PyInstaller build on 3.14, or SRL (its own 3.8 env, unaffected).

Before a 3.14 release: build gensim from source on both runners (or drop or replace it), then a full candidate with the sweep and the bundle gate, as for 1.6.47.

## 5. Outdated copy and flows (scan of 9 Nov 2026)

A scan of all of `src/`, `reminders/`, the docs and the setup scripts for text and flows that predate how the NLP Suite works now: the zip build (no Anaconda, no pip, no terminal), Stanza as default parser, the bundled Java runtime, the self-updater, the new menu, fastcoref, pandas 2, Python 3.10. Six read-only passes, one per slice; each finding below was checked against the code before it was changed or listed.

**Not read line by line:** the long help/readMe bodies of `DB_PCACE_data_analysis_main`, `DB_PCACE_data_validation_main`, `data_visualization_main`, `file_manager_main`, `DB_SQL_main`; the middle of `GUI_util` (about lines 1100–1750, 2190–2600), `NGrams_CoOccurrences_main` (400–1280), `NLP_setup_IO_main` (630–1050), `knowledge_graphs_main` (240–730). These were keyword-searched only. The TIPS pdfs themselves were not opened (only their names were checked). No web link was tested online.

### 5.1 Decisions for Roberto (not changed)

Deletions and behaviour changes. Each is ready to do once decided.

| # | What | Evidence | Proposal |
|---|---|---|---|
| 2 | SRL in the zip build | `setup_SRL.py` is not shipped and needs conda, so SRL cannot be set up there. The checkboxes in SVO, Semantic analysis and SRL_main stay enabled; the menu entry "SRL Semantic Role Labeling" shows as unavailable although `SRL_main.py` exists | Either disable the SRL checkboxes when frozen, or ship an SRL environment. Then fix the menu entry to match |
| 3 | Java as "external software" | A JRE is bundled, but Setup external software still lists "Java (JDK)" as missing and offers to download it. In the install branch (`IO_libraries_util`, "RF 8/30") the test reads `if Java_errorFound:` → "IS ALREADY INSTALLED" | Hide the Java row when the bundled `jre` is found. Check the RF 8/30 condition |
| 4 | Coreference default | `coreference_main` defaults to Stanford CoreNLP (needs CoreNLP); Stanza and BERT need nothing. Menu labels still say "CoreNLP annotator - coreference", "Pronominal resolution via CoreNLP" (`constants_util` 1011, 1067; `NLP_menu_tools_util` 40, 87, 97) | Default to Stanza; rename the labels (keys change in three files together) |
| 5 | `config_util` fallback | When the package config cannot be read the fallback is Stanford CoreNLP (line 199) | Stanza |
| 6 | First three launches open `NLP_welcome_main` in a second process | Decided before `import GUI_util` since 1.6.44; its video button is disabled, Enter only reopens the menu | Remove the redirect and the file |
| 7 | `NLP_menu_main` external-software reminder | `setup_external_programs_checkbox` returns the module global (always ""), so the reminder never shows; `setup_external_software_warning` is never called | Delete the two |
| 8 | N-grams VIEWER | The checkbox and two menu entries are live; RUN answers "temporarily disconnected" | Hide until it is back, or reconnect |
| 9 | Topic modeling "Run MALLET (coherence)" checkbox | Calls `gensim.models.wrappers`, removed in Gensim 4; always ends in "install Gensim 3.8.3" | Remove, or rewrite with Gensim's CoherenceModel. Help text also says "Gensim uses the MALLET algorithm" (it does not) |
| 10 | OCR menu item | pytesseract/pdf2image are not bundled, so in the zip it can only end in the "missing" message | Hide when frozen, or bundle |
| 11 | `parsers_annotators_main` | Two unreachable "select Stanford CoreNLP as your default package" branches (300–313, 395–408); "Open coreference GUI" checkbox is read and never used; Word2Vec item never matches its own label; coreference item says "via spaCy" (coreferee is gone); Stanza constituency says "not available yet" though Setup offers it | One PR for the annotator menu |
| 12 | Open-GUI launchers that use `sys.executable` | `DB_PCACE_data_analysis_main`, `DB_PCACE_data_validation_main`, `DB_SQL_main` (frozen: that is the app, not Python); `corpus_checker_PCACE_data_main` runs `sudo Python X_main.py` on a Mac and launches `WordNet.py`, which does not exist | Use `run_script_util` everywhere |
| 13 | TIPS menu | "pip install & Anaconda environments", "Python: download, install, run", "Anaconda & pip useful commands" are second in the main TIPS list | Move to the end as developer TIPS, or remove. The pdfs themselves, and the Java / CoreNLP / MALLET install TIPS and "Topic modeling and corpus size", need a read |
| 14 | Dead files | Deleted by #1706 (1.6.48), except `post_build_fixup.py` (§1.1) | Done |
| 16 | Reminders | 51 titles are in `reminders.csv` twice, under a GUI and under `*`. Popups read only the `*` row, the dropdown toggles the GUI row, so switching a reminder off there does nothing. About 12 definitions in `reminders_util` are used nowhere (Java 64-bit `-d64`, "CoreNLP Server is shutting down", tkinter Mac bug, SVO/WordNet/MALLET/Google Earth "system requirements") | Delete the per-GUI duplicates and the unused definitions |
| 18 | wordclouds | Menu offers Wordle (site gone) and Tagxedo (needs Silverlight); "Tagul" is now WordArt; Python WordCloud asks for internet though it needs none | Remove the two, rename the third, drop the check |
| 19 | `MEMO_Development_Notes.md`, `docs/CustomTkinter-Migration-Plan.md` | June 2026 history (Python 3.8 build, Mac Intel CI, files since deleted); a plan that names `setup-app/` and says installers build from `roberto` | A "historical" banner on each, or delete |

### 5.2 Left from the copy pass (18 Nov)

The wording pass on `release/v1.6.44` fixed the rest of the old §5.2. These were left because they change behaviour, not words:

- `IO_libraries_util` (~line 361): the Windows check for a 32-bit Java. The zip bundles a 64-bit JRE, so only source installs can reach it; drop it with §5.1 #3.
- `topic_modeling_mallet_util` (~lines 115 and 139): two "THIS IS A TEMPORARY FIX" warnings about `MALLET_HOME` on every run, though the code sets the variable itself. Print instead of a popup.
- `file_manager_main`: the utf-8 and ASCII checkboxes only answer "not available yet". Hide them.
- `file_classifier_NER_util`, `file_find_non_related_documents_util`: a missing `social-actor-list.csv` ends in `sys.exit()`, closing the GUI. Return instead.
- The MALLET and Google Earth download links in Setup external software: not opened since 9 Nov.

### 5.3 First run from source: the config warning repeats and the window looks frozen

Found 11 Nov, already on `roberto`; the zip ships `lib/config_defaults`, so students do not see it. With no `config/`, `config_util.read_NLP_package_language_config` shows its "config file … could not be found" warning on every call (52 calls in 28 files), so Style analysis and Wordclouds show it 5 times at open and the Parser & language setup GUI itself 3 times. Then `GUI_util` (~2096) opens that setup GUI with the blocking `run_script_util.run_script`, so the tool's window, including the last warning's OK button, looks frozen until the setup GUI (often hidden behind it) is closed. Fix: warn once per process and never inside the setup GUI; open it with `run_script_detached` or say in the warning that a window is opening.

## 6. Performance: slow GUI opening and "downloading"

Evaluated 9 Nov 2026 on `current-stable` @ `43cbca1c` (v1.6.40), Windows 11, NLP env (Python 3.10), warm disk, good connection. Nothing in the code was changed; this section is findings and proposed fixes, ranked.

**Not measured:** the installer (zip) build and its bundled `python-env`; macOS; a cold start after a reboot; a first-time model download; the speed of the analyses themselves after RUN (§6.9 is read from the code only).

**How it was measured.** `python -X importtime -c "import GUI_util"`; each third-party library imported alone in a fresh process; for every `*_main.py`, the libraries it reaches through module-level imports (followed through the local `src` modules, including the `install_all_Python_packages` lists) imported together in one fresh process; `stanza.download("en")` and the Stanza pipeline timed with the model already on disk; `import Stanza_functions_util` and `import statistics_txt_util` run for real. The per-GUI figures in §6.2 are import cost only, from that static trace: no GUI window was opened and clicked.

### 6.0 Summary

| # | Finding | Measured cost | Who pays | Fix size |
|---|---|---|---|---|
| 1 | Heavy libraries imported when the GUI opens, not at RUN | 10–40 s | 32 of 55 GUIs | Medium, file by file |
| 2 | Every GUI starts with 4.6 s of `GUI_util` imports (pandas) | 4.6 s vs 0.9 s for a bare Tk window | Every GUI, every open | Small |
| 3 | "Started/Finished running" alerts and reminders block until their countdown ends | 1–12 s each | Every RUN | Small (a decision first) |
| 4 | Fixed `time.sleep` calls freeze the GUI | 5–10 s each | Config-file edits, CoreNLP, spell checker | Small |
| 5 | Version check on the main thread on every GUI open; other web calls without a timeout | 0.1 s here; up to ~16–18 s on a blocked or dead network | Every GUI | Small |
| 6 | Menu runs `java -version` at every start | Not measured | Menu | Small |
| 7 | Row-by-row pandas loops in the analyses | Not measured | RUN on large corpora | Profile first |

Findings 1–2 are where the opening time goes. Adding up the measured parts, a GUI such as Style analysis takes an estimated half a minute to open (4.6 s base + 29 s of libraries; not timed end to end) and should drop to a few seconds; the menu and the light GUIs should drop from about 5 s to about 1.5 s.

### 6.2 Heavy libraries are imported when the GUI opens

Each `*_util.py` starts with `install_all_Python_packages(...)`, which **imports** every listed package to test that it is installed, and then with module-level imports of the same libraries. A GUI therefore loads everything any of its options might use before it draws. Since #1704 stopped the Stanza model check, this is most of what is left: `import Stanza_functions_util` takes 18.5 s and `import statistics_txt_util` 21.3 s.

Libraries alone, fresh process (seconds): `sentence_transformers` 39.5 · `summarizer` 25.2 · `spacy_langdetect` 23.6 · `tensorflow` 21.0 · `stanza` 16.8 · `contextualSpellCheck` 15.0 · `spacy` 14.6 · `seaborn` 11.4 · `transformers` 9.4 · `textblob` 8.2 · `pyLDAvis` 8.1 · `textstat` 7.5 · `nltk` 7.4 · `sklearn` 5.6 · `gensim` 5.2 · `folium` 3.6 · `openpyxl` 3.4 · `pandas` 3.1–3.5.

Library import cost per GUI (all its libraries together, one process; excludes the Suite's own code):

| Cost | GUIs |
|---|---|
| 3–4 s (23) | menu, welcome, NLP_setup_IO, NLP_setup_external_software, DB_SQL, SRL, corpus_profiler, data_manipulation, file_checker_converter_cleaner, file_handler_ALL, file_manager, file_matcher, file_merger, file_search_ALL, file_splitter, html_annotator, knowledge_graphs, narrative_analysis_ALL, nominalization, sample_corpus, semantic_analysis_ALL, sentiments_emotions_ALL, statistics_txt |
| 10–18 s (11) | GIS_symbolic 9.9, GIS_distance 10.6, charts_Excel 10.9, data_visualization 10.9, statistics_csv 10.9, GIS_Google_Earth 11.2, wordclouds 12.8, word2vec 13.2, CoNLL_table_analyzer 13.7, semantic_aggregation 13.7, NGrams_CoOccurrences 17.5 |
| 22–40 s (21) | file_classifier 22.5, sentiment_analysis 22.9, file_checker_pre_processing_pipeline 25.3, topic_modeling 25.4, file_search_byWord 25.5, corpus_checker_PCACE_data 25.9, shape_of_stories 25.9, NER 28.8, SVO 28.9, semantic_analysis 29.1, style_analysis 29.1, syntactic_analysis_ALL 29.1, html_annotator_gender 29.2, sentence_analysis 30.2, coreference 32.0, parsers_annotators 32.0, DB_PCACE_data_validation 33.2, NLP_setup_package_language 33.2, file_spell_checker 38.2, DB_PCACE_data_analysis 38.8, GIS 39.8 |

The GUIs in the first row already import their logic inside `run()`; they pay the cost at RUN instead, which is the right place.

**Fix, in this order.**
1. **`install_all_Python_packages` (`src/IO_libraries_util.py:102`): test with `importlib.util.find_spec(module)` instead of `__import__`.** It answers "is it installed?" without loading the package. One function, every GUI benefits; the existing name mapping (pdfminer, docx, PIL …) stays. Needs a unit test.
2. **Move the heavy imports into the functions that use them**, starting with the modules shared by most GUIs: `Stanza_util`, `statistics_txt_util`, `Stanza_functions_util`, `charts_util` (plotly, numpy), `IO_csv_util` (§6.3). Then the slow GUIs from the bottom of the table up. One PR per module, each with a `tests/gui_smoke.py` run.
3. In each `X_main.py`, import `X_util` inside `run()` where it is not needed to build the window (the pattern the fast GUIs already follow).

### 6.3 Every GUI pays 4.6 s before its own code runs

`import GUI_util` takes **4.6 s** (4.6–5.6 s across three runs); a bare `tkinter.Tk()` process takes 0.9 s. Each GUI is a new Python process (`run_script_util.run_script`), so this is paid on every open, not once per session.

| Part | Time | Why it is there |
|---|---|---|
| pandas | 2.2 s (3.1–3.5 s alone) | `IO_csv_util`, `reminders_util` and `config_util` import it at the top to read a few small config CSVs |
| Tk window, the rest | about 1.1 s | |

**Fix.**
- `reminders_util`, `config_util`: read `reminders.csv` and the config files with the `csv` module. `getReminders_list` and `checkReminder` each re-read `reminders.csv` with pandas, two or three times per GUI open.
- `IO_csv_util`: `import pandas` inside the functions that need a DataFrame.

`requests` is already imported only where it is used on `release/v1.6.44` (`import GUI_util` 1.50 s -> 0.82 s on a Mac). Expected saving from pandas: about 2 s on every window, the menu included. The menu also imports `customtkinter` (1.4 s), which is needed.

### 6.4 Timed alerts block the run

`IO_user_interface_util.timed_alert` (372 calls in 94 files) calls `GUI_IO_util.message_box_widget`, which ends with `top_message.wait_window()` (`src/GUI_IO_util.py:1384`). The analysis does not start, or the outputs do not open, until the popup closes.

The countdown is also longer than the `timeout` passed: it counts `timeout / 500` seconds, or `timeout / 1500` for "Started running"/"Finished running" messages (`GUI_IO_util.py:1255-1294`). A "2000 ms" alert waits 4 s, a 6000 ms one 12 s, unless the user clicks OK. Reminders wait 30 s.

**Fix (Roberto decides the behaviour):** for OK-type alerts, show the popup and return at once, letting it close itself with `after(timeout, ...)`; make the countdown equal `timeout`. Yes/No reminders must keep waiting for an answer.

### 6.5 Fixed sleeps

- `time.sleep(10)` after opening a config file, on the GUI thread, so the window freezes for 10 s: `src/GUI_util.py:1075`, `src/NLP_setup_external_software_main.py:101`, `src/NLP_setup_package_language_main.py:235`. The stated reason is "give enough time to save any changes"; re-read the file when it is next needed instead.
- `src/Stanford_CoreNLP_util.py:900` `time.sleep(5)` and `src/file_spell_checker_util.py:684` `time.sleep(5)`: waiting for the CoreNLP server. Poll the port until it answers (it is often ready sooner, and sometimes not ready after 5 s).

The 1 s pauses in `GIS_geocode_util` and `charts_util` are Nominatim's rate limit and must stay.

### 6.6 Network calls on the main thread

- `GUI_util.display_release()` runs at the end of `GUI_bottom` for every GUI: `internet_on()` then a GET to GitHub, before the window is usable. Here it took 0.03 s + 0.07 s, so on a good connection it is not the problem. On a dead or filtered network `internet_on()` can take up to 16 s (3 + 3 + 5 + 5 s of timeouts), and the GET up to 18 s (3 tries × 6 s).
- **Fix:** run the check in a background thread and fill the release label with `window.after`; check once per session, not once per window (the menu can pass the result to the GUIs it starts, like `NLP_SUITE_OPEN_WINDOWS`).
- No timeout at all, so a stalled connection hangs the GUI: `GUI_util.watch_video` (line 2168). (`check_CoreNLPVersion` and `open_url` get 5 s and 10 s on `release/v1.6.44`.) The last two fetch the whole page only to test that it exists before opening the browser; open the browser directly. Give the CoreNLP check `timeout=5` and run it at most once a day.

### 6.8 Menu start-up extras (not timed)

- `setup_external_programs_checkbox()` (`NLP_menu_main.py:1280`) → `get_external_software_dir` → `check_java_installation` runs `java -version` in a subprocess on every menu start. Cache the answer in the config file it already updates.

### 6.9 The analyses themselves (not profiled)

Read from the code only: 96 `iterrows()` / row-append patterns in 29 files, most in `DB_PCACE_data_analysis_util` (35), `charts_util` (13) and `corpus_profiler_util` (6). These grow quadratically on large tables. Do not rewrite them blind: time one real corpus run per tool (`python -X importtime` is no help here; use `cProfile`) and fix what the profile shows.

### 6.10 Order of work

1. §6.3 pandas out of the `GUI_util` import chain; §6.2 step 1 (`find_spec`). Every GUI gets faster.
2. §6.5 sleeps; §6.6 the release check in the background, and `watch_video`'s timeout.
3. §6.4 alerts, once Roberto has decided the behaviour.
4. §6.2 steps 2–3, module by module.
5. Re-measure with the same commands, on Windows and on a Mac, and on the zip build. Add a CI check that `import GUI_util` under the test stubs does not import pandas or requests, so the gain is not lost.

Every change follows CLAUDE.md: unit tests for new helpers, `pytest tests/`, and `python tests/gui_smoke.py` after any GUI edit.

### 6.11 Re-measured on Python 3.11 (27 Nov 2026)

`tests/startup_bench.py` on the published Mac zips, Apple M2 (8 GB): 1.6.46 (CPython 3.10.15) against 1.6.47 (CPython 3.11.14), each a fresh unzip, three runs per item in a fresh process, the two releases taking turns. "Warm" is the median of runs 2–3; "first" is run 1, a student's first open after unzipping. Raw data: `~/Documents/NLP_output/bench/startup_1.6.46_vs_1.6.47.json` (rebuild the tables with `startup_bench.py report`).

| | 1.6.46 warm | 1.6.47 warm | 1.6.47 / 1.6.46 |
|---|---|---|---|
| `python -c pass` | 0.02 s | 0.01 s | 0.50 |
| `import GUI_util` | 0.88 s | 0.77 s | 0.88 |
| All 55 GUIs opened, total | 213.4 s | 212.5 s | 1.00 |
| Light GUIs (about 1 s: file tools, setup GUIs, the menu) | | | mostly 0.66–0.86 (html_annotator 1.17) |
| Heavy GUIs (5–13 s: style, syntactic, topic modeling, SVO, spell checker, PC-ACE) | | | 0.79 (word2vec) – 1.14 |
| The 26 heavy libraries alone, total | 32.1 s | 33.7 s | 1.05 |

**What it says.** Python 3.11 made the interpreter and the Suite's own code faster, so most light GUIs open 15–35 % sooner. Heavy GUIs did not, on the whole, get faster, because their time is library import, and the library versions 3.11 brought are a little slower to import: BERTopic 8.6 → 9.7 s, sentence-transformers 4.7 → 5.3 s, Stanza 1.2 → 1.5 s, NLTK 1.1 → 1.3 s (transformers 5 halved, 0.95 → 0.49 s). Overall opening time is unchanged; §6.2–6.3 (import heavy libraries at RUN, not at open) is still the lever.

**The first open after unzipping is the slow one.** Run 1 of each library on a fresh unzip, against warm: BERTopic 40 s (9.7), spaCy 21–26 s (1.2–1.4), scikit-learn 19 s (0.9), seaborn 16 s (1.2), sentence-transformers 13–15 s (5), pandas 13 s (0.3). The same in both releases, and the zip ships its `.pyc` files (22,940 of 23,306 in `site-packages`), so it is not compilation; most likely macOS checking each library file the first time it is loaded. A student pays it once per library, on whichever GUI first imports it: up to about a minute on the first open of a heavy GUI. Not measured on Windows (Defender scans first loads too). A possible fix: after an install or update, import the heavy libraries once in a background process while the welcome screen shows.

**The analyses themselves: no change.** 20 Python-heavy tool-sweep recipes (one or two per family) plus `parser_CoreNLP` as a control, on the same two zips, the releases alternating per recipe, 3 rounds with the first-run order swapped (median of 3; `~/Documents/NLP_output/bench/sweep_interleaved.json`, the script beside it). The 20 together: 629 s on 1.6.46, 615 s on 1.6.47 (0.98). Faster by 10–21 %: SVO with spaCy (0.79), Character Emotion Arcs (0.82), NER with Stanza (0.86), the profiler's characters (0.88), BERTopic and word2vec BERT (0.89). Slower: fastcoref (1.10), BERT sentiment (1.05), the HTML dictionary annotator (1.04); the rest within ±5 %. The CoreNLP control, which Python cannot affect, came out at 0.76 and ranged 44–90 s within a release: differences under about 15 % on one tool are noise. Why so little: 3.11's speed-up is in running pure-Python bytecode, and these tools spend their time in PyTorch, spaCy's compiled code, numpy/pandas/scikit-learn and Java; 3.11 also brought newer libraries (transformers 5, numpy 2.4, scikit-learn 1.9), which the comparison cannot separate from the Python change. Two single full sweeps (1.6.46 and 1.6.47 on 27 Nov, `tool_sweep/1.6.46-rerun`, `tool_sweep/1.6.47`) differed by -38 to +73 % on CoreNLP tools alone, so a single sweep's timings are not a benchmark; `compare`'s SLOWER list is for review only, as it says.

**Compared with §6.2–6.3 (Windows, 9 Nov):** `import GUI_util` is 0.8 s here, not 4.6 s, and the heaviest GUI 13 s, not 30–40 s. Part of that is the Mac, part the work since (1.6.44 moved `requests`, #1704 the Stanza model check). Re-measure on Windows before ranking §6.2's fixes again.


## 7. UI overhaul: findings (10 Nov 2026)

**Decision so far:** stay with CustomTkinter (CTk). A TypeScript front end would mean rewriting 55 GUIs and the way they start each other; CTk keeps every `run()` as it is.

**How it was looked at:** each `*_main.py` built under real Tk on a Mac (macOS, 1470×956 logical screen, the NLP310 env, `config/` seeded from `lib/config_defaults`), screenshotted, and its widgets walked: the `gui_layout_gate.py` method, plus the screenshot step of `tests/gui_gallery.py` from the CTk branch, adapted to `roberto`. All 55 GUIs, Windows not looked at. Counts are from `grep` over `src/`.

### 7.1 Where the migration stands

- **A CTk migration was mostly built in July and never merged.** Branch `ctk/phase1-grid` on the coralynnkc fork (last commit 23 Jul): `GUI_theme_util.py` (theme, widget factories, tooltips; 880 lines), `ctk_bundle_util.py` (the `CTkImage` fix for the bundled Python), `nlp_suite_theme.json`, `tests/ctk_bundle_smoke.py`, `tests/gui_gallery.py`, and Phases 2–3 (all GUIs converted, PRs #7–#20 on the fork). It is 49 commits ahead and 196 behind `roberto`, and 64 files conflict, mostly because v1.6.40 reformatted `src/`. Only the grid half of Phase 1 (`placeWidget` → grid) reached `roberto`.
- **On `roberto` only the menu's tool browser is CTk.** Everything else is plain Tk: 326 `tk.Label`, 321 `tk.Checkbutton`, 273 `tk.Button`, 214 `tk.OptionMenu`, 136 `tk.Entry`, 58 `ttk.Combobox`, 9 `tk.Scale`. 171 raw `.place()` calls bypass the layout helper.
- 9 GUIs opt out of the grid layout (`GUI_IO_util.GRID_OPT_OUT`): 7 on all platforms, `charts_Excel` and `file_manager` on Mac only.
- `docs/CustomTkinter-Migration-Plan.md` describes the branch, not `roberto`. Its Windows bundle smoke test (§12.1 there) was never run.

### 7.2 What the screenshots show

Most of these are about content and chrome, not the widget toolkit; CTk alone fixes only the last few.

| # | Finding | Where |
|---|---|---|
| 1 | The same five-line "Welcome to this Python 3 script…" block tops every GUI (about 110 px): it explains the HELP buttons, TIPS and RUN, and calls the tool a script | `GUI_util.GUI_top`, all 55 |
| 2 | A "? HELP" button starts every row: 597 of them. Some rows have nothing else (`file_classifier`, two in `DB_PCACE_data_validation`) | `place_help_button` |
| 3 | Four blank buttons right of the I/O row (`text=""`, 9 such buttons in `GUI_util`); what they do shows only on hover. The right-most is cut off at the window edge: Wordclouds draws 71 px past its window | `GUI_util` I/O row |
| 4 | "Release 1.6.41/1.6.41": local/GitHub version, not explained | `GUI_util.py:533` |
| 5 | Nine controls of chrome on every analysis GUI: the chart row (Excel, Bar chart, No transformation, Data tools), even in tools that make no chart, plus Read Me, Watch videos, Open TIPS files, Open reminders, Setup. "Watch videos" is red in some GUIs and black in others; the colour code is not explained | `GUI_util.GUI_bottom` |
| 6 | Window titles all start "Graphical User Interface (GUI) for …" | `GUI_label` in each GUI |
| 7 | The grid spreads columns across the full 1350 px, so a value can sit far from its label (GIS "Country bias", N-grams "Options", Sample corpus "Date type"); columns do not line up across rows | grid layout |
| 8 | Disabled controls are very faint, and a disabled RUN looks almost like an enabled one; why it is disabled is said only in a popup at open | all |
| 9 | 14 GUIs show one to three popups before the window can be used, mostly "requires a csv FILE in INPUT; RUN is disabled": CoNLL table analyzer (2), PC-ACE data analysis (3), Excel charts (2), Data manipulation (2), Setup external software (2, one asks to watch a video), the menu (the "three setup options" question, removed in #1705), GIS Google Earth, GIS distance, GIS symbolic, Corpus checker, Data visualization, File classifier, File manager, Statistics csv | `check_IO_requirements`-style code at the end of each GUI |
| 10 | Mixed fonts: tab labels and section headings in red bold Courier (PC-ACE data analysis, Data visualization, Narrative analysis ALL); italic red headings in the welcome window | those GUIs |
| 11 | The five "ALL" hubs (File handler, File search, Semantic analysis, Sentiments & emotions, Syntactic analysis) are lists of "(Open GUI)" buttons, each with a HELP button. The menu's searchable tool list already does this | the `_ALL_main` GUIs |
| 12 | Column groups without headers: SVO's three Lemmatize/Filter groups do not say which parser each is | `SVO_main` |
| 13 | Every window is 1350 px wide (Wordclouds 1450, File search by word 1418) on a 1470 px screen, though most use the left half. None is taller than this screen | `get_GUI_width` |
| 14 | The menu mixes the CTk tool browser with the Tk header and footer; its footer still has RUN beside the browser's own Open button | `NLP_menu_main` |
| 15 | Old-style Tk sliders (`tk.Scale`) | Setup package & language, Semantic analysis (WSI) |

### 7.3 Bugs found along the way

- Not bugs: `NLP_setup_IO_main` refuses to run on its own (by design); `data_manipulation`, the menu and the setup GUIs build their window only under `__main__`.

### 7.4 Proposed order (its own releases)

1. **Content and chrome first, no new toolkit** (11.2 #1–9, #11; decisions for Roberto): cut the welcome block to one line or nothing; replace the HELP column with an ⓘ beside each label that shows the same text; label or icon the four I/O buttons; show the chart row only in GUIs that chart; say why RUN is disabled next to RUN instead of in popups; shorter titles. Almost all of it lives in `GUI_util` and `GUI_IO_util`, so all 55 GUIs change at once.
2. **Bring the CTk groundwork over as new files** (no conflicts): `GUI_theme_util.py`, `ctk_bundle_util.py`, the theme JSON, `tests/ctk_bundle_smoke.py`. Run the bundle smoke test inside a built zip on Windows and on a Mac before anything uses it.
3. **CTk chrome:** `GUI_top`, `GUI_bottom`, the help/tooltip and popup widgets through the factories. Every GUI gets the new look outside its own rows.
4. **Per-GUI conversion in tranches**, re-running the branch's mechanical recipe on today's files instead of rebasing its 49 commits; use the branch commits as the reference for each GUI's quirks.
5. **Fold the hubs into the menu** (11.2 #11) and hide what the zip cannot run (§5.1).

Each PR carries before/after screenshots from a gallery script. Add one to `tests/` that runs on a Mac too (the branch's `gui_gallery.py` reads Windows screen scaling; on a Mac `screencapture -R` works, and the GUIs that build only under `__main__` need `runpy`).

## 9. Open pull requests

Reviewed 9 Nov 2026. The older PRs conflict only because v1.6.40 reformatted all of `src/` (PR #1687).

"Tests" = the PR's own new tests, run on Windows in the NLP env on 9 Nov.

| PR | Opened | What | Merge | Tests | Release | Review |
|---|---|---|---|---|---|---|
| #1682 | 10-16 | spaCy CoNLL ID/HEAD sentence-level and 1-based | Conflict: ruff only, mechanical | 2 pass | Later (shared structure) | Correct: Stanza and CoreNLP already write 1-based, sentence-level, root 0, and no reader compensates for spaCy's old values. Shared structure, so not in a release about the updater. spaCy tables already on disk stay 0-based: say "re-parse" in the CHANGELOG |
| #1683 | 10-16 | Gender dictionary looks up only PERSON tokens | Conflict: ruff only | 5 pass | No | **Needs changes:** hardcodes `Stanford_CoreNLP_util.CoreNLP_annotate` whatever parser is configured (so the option now needs Java); returns `''` with no message when no NER csv comes back; once "Will" is a PERSON anywhere, every "will" is tagged |
| #1528 | 2024-09 | "dictionary functionality" (CallaGong) | — | — | No | **Close**: targets `current-stable`, 2 years old |
| #1525 | 2024-09 | Generalized Excel file reads (esunn0412) | — | — | No | **Close**: targets `current-stable`, 2 years old |
| #1436 | 2024-03 | Document Statistics sentence-length fix (razzak-ammar) | — | — | No | **Close**: check first that v1.6.39's sentence-statistics rewrite fixed it |
| #1383 | 2024-01 | Alternative STEP2 install script (Eli-Todd) | — | — | No | **Close**: install was rebuilt around PyInstaller |

All 2026 PRs are by coralynnkc and target `roberto`.

## 10. Recent issues (2025–2026)

"Retest": a later release says it fixed this or something close. Rerun on v1.6.42 and close if it's gone. All of these were still open on 18 Nov.

| # | Title | Kind | Note |
|---|---|---|---|
| — | MALLET topic modeling crashes in the Mac zip: "Failed to import tkagg backend" (found 22 Nov by `tool_sweep.py`, no issue yet) | Bug | `topic_modeling_gensim_util.py:45` calls `matplotlib.use("TkAgg")` inside a try that falls back to Agg, but `use()` does not load the backend, so it never fails there; the bundled Python's Tk backend then fails at the first figure (`plt.gca()` in the MALLET path). The Suite only saves charts to files: use `Agg` outright, as `charts_util`, `statistics_csv_util` and `GIS_symbolic_util` already do. Gensim's own run passed |
| 1671 | BERT word embeddings are context-free | Design | Each word is encoded alone, so vectors don't depend on the corpus. Affects a homework question. Decide: keep, document, or encode in context |
| 1653 | Windows zip: JavaScript paths too long under `AppData\Local\Programs` | Bug | MAX_PATH in bundled node_modules. Shorten in the build or document the install location. Also matters for the self-updater's `_update` folder |
| 1623 | Boxplot: asks for an option but none appear | Bug | |
| 1620 | pdf → txt converter error | Retest | v1.6.34 fixed several pdf → txt faults |
| 1619 | Selecting a new input file/directory (pdf converter) | Bug | CANCEL path in the I/O setup |
| 1616 | Progress indicator never shows "complete" | Bug | All tools |
| 1614 | GIS country-bias list has only 2 countries | Bug | |
| 1609 | Parser runs but writes nothing | Retest | Needs a reproduction |
| 1607 | CoNLL Table Analyzer RUN does nothing | Bug | No error shown, so it breaks the no-silent-failures rule |
| 1606 | Gensim Word2Vec error | Retest | v1.6.39 fixed Gensim Word2Vec with Lemmatize |
| 1604 | Style analysis error after update | Check | The error is a JSON "detail" message, possibly from a web runner, not this repo |
| 1603 | Google Earth GUI: "Icon for group of values" not implemented | Bug | Values passed but unused in `GIS_pipeline_util` |
| 1599 | PC-ACE analyzer: complex-object frequencies count identifiers | Enhancement | |
| 1598 | Data visualization 1: colormap/heatmap error on SVO csv | Bug | |
| 1593 | Sentiment Analysis GUI fails to open | Retest | Run `tests/gui_smoke.py` |
| 1592 | Readability: negative grade level ("-1th grade") | Bug | Clamp or label below grade 1 |
| 1589 | SVO + CoreNLP coreference error (Mac M2) | Retest | v1.6.40 fixed SVO-with-coreference crashes |
| 1582 | Deprecated `encoding='utf-8', strict=True` warning | Bug | Small |
| 1579 | CoNLL Table Analyzer works only on CoreNLP tables | Enhancement | Extend to Stanza and spaCy. Related: PR #1682 |
| 1575 | WSI output: csv extension, chartable | Enhancement | v1.6.39 fixed the WSI crash, not the output format |
| 1573 | Normalize punctuation frequencies | Enhancement | |
| 1566 | Excel "by Document" charts: no Document ID, no hyperlink | Enhancement | |
| 1564 | Search words by document: chart and word label | Enhancement | 4 comments |
| 1561 | CoNLL analyzer passive verbs: wrong DEPRELs in output | Bug | Possibly the DEPREL filter fixed by PR #1679 |
| 1560 | Bubble chart problem (Mac M2) | Bug | |
| 1558 | utf-8 problem in n-grams VIEWER output (Mac M2) | Bug | |

## 11. The 2021–2024 backlog

229 issues, #44 to #1551. 164 have no comments. 119 were opened by `Emory-NLP` (Roberto's own notes).

| Labels | Count |
|---|---|
| none | 118 |
| enhancement | 65 |
| bug | 22 |
| bug + student-bug | 20 |
| help wanted | 3 |
| OS X + bug | 1 |

Since then the code has had a full RUN-button rewrite (v1.6.2), a chart-engine rewrite (v1.6.3) and a format pass (v1.6.40). Many of these reports describe code that no longer exists.

**Proposal (needs Roberto's yes):**
- **Bugs (43):** close as stale with a comment: "Closing as part of a backlog cleanup; much of this code was rewritten in 2026. If it still happens on v1.6.40 or later, please reopen with the steps." Keep any Roberto marks as still real.
- **Enhancements and unlabelled `Emory-NLP` notes:** Roberto skims and keeps the ones still wanted. Add the kept ones to §10 or to a `wishlist` label, and close the rest.
- **Other unlabelled reports:** treat as bugs.

To do this with `gh` (needs a login): `gh issue close N -c "<comment>"`. Without a login, use the GitHub web UI.

## 12. Tech debt

Re-measured 18 Nov 2026 over `src/` (223 files). The 16 Jul figures are in brackets.



| File | Why it is left |
|---|---|

### 12.3 Silent failures: 212 bare `except:` [221]

Largest reliability lever. Convert to `except Exception`, and on user-facing paths report via `messagebox`. Worst files in July: `IO_files_util`, `GIS_geocode_util`, `file_filename_util`, `charts_util`, `Stanford_CoreNLP_util`.

### 12.4 Wrong-result risks

- **Late-binding closures in loops (B023): 8.** `statistics_csv_util.py` (`col`, `df`/`currentColumn`, `temp_str`), `CoNLL_k_sentences_util.py`, `charts_Plotly_util.py`, `charts_util.py`. Verify each, then bind at definition (`lambda col=col: ...`).
- **Mutable default arguments (B006): 47.** Mechanical fix.
- **Shadowed redefinitions (F811): 5** [37].
- **Ties come out in a different order on every run.** Sweeping the published 1.6.47 against its rc2 (27 Nov) found the same rows and counts but a different order in the CoNLL noun/verb lists, the WordNet/FrameNet/VerbNet frequency tables and charts (WordNet "location" and "cognition", both 49), the WordNet zoom-in person list, and one pyspellchecker correction ("Barkskins": "bearskins" or "buckskins", equally close). Python randomizes string hashing per process, so anything that goes through a `set` (or sorts by count only) orders its ties differently each time. Results are right but not reproducible file for file. **Fixed on `fix/tie-order` (28 Nov):** `CoNLL_util.get_nouns_verbs_CoNLL` writes its lists sorted, so the tables built from them follow; `file_spell_checker_util.stable_correction` replaces pyspellchecker's `correction()` (`max()` over a set) and takes ties in alphabetical order. **Still open:** the WordNet zoom-in person list (`semantic_aggregation_WordNet_util.disaggregate_GoingDOWN`) also changed order between 1.6.47 and the 1.6.49 candidate, on one fixed keyword ("person") whose hyponyms NLTK returns sorted, so its cause may be something other than hash order (an NLTK or WordNet-data version difference between the two builds?): not verified.

### 12.5 Fragility

- `eval()` (S307): 6. In `charts_Plotly_util.py`, `charts_util.py` and `hashfile.py`. Replace with `ast.literal_eval` or explicit parsing.
- `subprocess(..., shell=True)` (S602): 9. Breaks on paths with spaces. Use argument lists.

### 12.6 Tests

Coverage is 683 test functions in 67 files [3]. Gaps:
- No **empty-DataFrame** regression test for the chart/statistics pipeline (only the emotion-arc tests in `test_character_emotion_arcs_util.py` cover an empty frame).
- No **multi-column chart** regression test for `charts_util` (the v1.6.4 "by Document" grouped-bar fix has no test).
- **`test_hc_runs_on_real_scikit_learn` fails in a full local run** (27 Nov, on `roberto` too), and passes alone: real scipy's import meets a stub another test file left in `sys.modules` (`TypeError: issubclass() arg 2 must be a class` in `scipy.stats._new_distributions`). CI skips it (no scikit-learn there). Find the stub it meets, and hide it the way the test already hides scikit-learn/scipy stubs.

### 12.7 Hygiene

- Unused variables (F841): 496. Unused imports (F401): 1 [290]. Invalid escapes (W605): 0 [80].
- Tab-indented lines remain in 2 files.
- Large modules (lines): `DB_PCACE_data_analysis_util` 7,731 · `charts_util` 5,620 · `corpus_profiler_util` 4,191 · `Stanford_CoreNLP_util` 3,563 · `statistics_txt_util` 3,033. When you open one for a feature, pull testable helpers out instead of adding in place.
- About 900 `print()` calls. Move to `logging` over time.

**Order:** the F821 left in §12.1 → bare excepts on user paths → B023 → B006 → eval/shell.

## 13. Branches

Head branches of merged PRs are deleted automatically (repo setting since 18 Nov 2026; the coralynnkc fork has it too). Remote branches besides `roberto`, `current-stable`:

- `mac-font-pin` (22 Jul 2026): not in `roberto`, no open PR. Check whether it's still needed.
- `dictionary` (Sep 2024), `taeeun` (Dec 2024): heads of stale PRs #1528 and #1525. Delete after those PRs are closed.
- `remove_shortcut_prompt` (2021), `tony` (2023): no open PR. Delete candidates.
- Cora's, open work: the 1.6.48 candidate (`release/v1.6.48`, PLAN) and 1.6.49 (`chore/tcl9-trace-add`, `chore/1.6.49-python-3.11.18`). The 1.6.43 spike branches and the 1.6.44 backup were deleted on 23 Nov.

Deleting someone else's remote branch is Roberto's call.

## 14. Requirements, release checks and settled decisions

- **coreferee** is gone from `requirements.txt` (it pins `spacy<3.6` and broke the PyInstaller build). `fastcoref` replaces it. Don't re-add it. spaCy is unpinned.
- **pygit2** is no longer a requirement (1.6.41): the source-checkout updater uses the `git` program. Don't re-add it.
- **`lib/release_manifest.tsv`** is written by the build's last step before zipping (1.6.41). The self-updater relies on it to tell the user's files from the release's: any step that adds files to `dist/` must come before it.
- **A release may delete files.** The self-updater installs the new release as a whole folder and carries over only `config/`, `reminders/` and files the user added (not in the old manifest); a release file the new release drops is left in `<folder>_previous` and goes with it. A dropped file the user had edited stays in that backup, which is then kept (`user_files` in `NLP_setup_self_update_util.py`).
- **Pillow** is pinned to 13.0.0 (1.6.47). The old 10.4.0 pin was for a Tcl/Tk crash in `PIL.ImageTk`, which only the Google Earth icon preview still uses, inside a try/except. Don't add new `ImageTk` callers: use `GUI_util.tk_image_from_pil`.
- **transformers** is `>=5.10` (1.6.47). Don't add a package that holds it below 5; `bert-extractive-summarizer` did, and was removed for it.
- **CI Python:** 3.11 for tests and installers, and the bundled `python-env` is CPython 3.11.14 from python-build-standalone `20251217` (1.6.47), the last with Tcl/Tk 8.6. 1.6.49 moves it to `20261124` (3.11.18, Tcl/Tk 9.0.4) after the `trace_add` port, on the Mac (Windows: 3.11.18 with Tcl/Tk 8.6.15), and the build then fails if python-env's Tcl is not 9 on the Mac or not 8.6 on Windows. SRL stays on its own 3.8 env.
- **Mac runners:** `macos-15` since 2 Nov 2026 (`macos-14` retired). No Intel Mac build.
- **`src/` is Ruff-formatted** (v1.6.40). PRs opened before that need a rebase, not a hand merge.
- **Update order matters.** The in-app check reads `current-stable`'s `lib/release_version.txt`, which changes before the tag's zips finish building. The self-updater and the launch popup both wait until that version's zip is on the release page.
- **Before every tag:** build, unzip both artifacts, confirm `Launch NLP Suite (Mac).command` and the Windows entry point exist, run `tests/bundle_gate.py` (`snapshot` the last release and the candidate, then `compare`), then draft the CHANGELOG section.
- **When a release changes analysis code**, compare outputs zip against zip with `tests/tool_sweep.py`: `run` each unzipped zip (the last release and the candidate) into its own folder, pass `--external-config config/NLP_setup_external_software_config.csv` so the CoreNLP recipes find CoreNLP, then `compare` the two folders. Use `--only` for the changed tools when `pip list` of the two `python-env`s is the same; run everything when it is not. Differences that are noise, seen on 1.6.44 and 1.6.45: langdetect's confidence and vocd-D (random sampling); CoreNLP's speed assessment (timing); Character Emotion Arcs' character order within a sentence and "Lady Elliot"/"Elliot" (set order); floating-point noise around 1e-14. `tool_sweep_compare.NOISE` encodes these. Without `--external-config`, CoreNLP recipes are SKIPPED (a fresh unzip has no CoreNLP path).
- **The self-updater can be checked without clicking:** in an unzipped previous release, add a file under `lib/`, a folder, and a config line, then run that release's own `NLP_setup_self_update_util.update_zip_install(app, "<new version>")` on its `python-env` with `tkinter.messagebox` patched to answer Yes, and `NLP_SUITE_UPDATE_QUIET=1` so the swap script shows no dialog. Then diff the tree against a clean unzip of the new release, and call `remove_previous_version(app, background=False)`. It needs the new release published; the swap waits while any `NLP_Suite` process runs. A first launch of the frozen menu opens the welcome screen, which waits for a click before the menu (and its backup cleanup) runs.
- **The wiki is published from `docs/wiki/`** (one file per page, exact wiki names, plus `_Sidebar.md` and `_Footer.md`). `publish-wiki.yml` copies it over the wiki on every push to `roberto` that touches it, deleting pages that are not there, so edit `docs/wiki/`, never the wiki. On a PR to `roberto` it prints what would change without pushing. The wiki is not tied to releases: a page about a feature that has not shipped waits for the release before it is merged.
- **`bundle_gate.py` sets `DO_NOT_TRACK=1`** for every program it runs, and ignores CustomTkinter's `application has been destroyed` traceback when it closes the menu (both were false alarms on 17 Nov). `lib/release_version.txt` must equal the tag (CI enforces it).

## 15. The updater: known limits

- **The start race (fixed in 1.6.48).** On a GitHub Windows runner (28 Nov) PowerShell took 30 s to start the swap script; the app gave up at 30 s, said the installer did not start, and deleted the download while the script was starting, which then moved the NLP Suite aside, found nothing to install and moved it back. 1.6.48 waits 120 s and claims the start flag atomically (the app on a timeout, the script as its first act), so a late script changes nothing. Updates *from* 1.6.47 still run 1.6.47's 30 s code: a slow Windows machine may see "the program that installs the new version did not start" once; its NLP Suite keeps working, and the next close tries again.

- **Long paths:** staging is 17 characters deeper than the install; without Windows LongPathsEnabled the deep `node_modules` paths (#1653) fail to unpack. Fails safely with a message. Fix with #1653.
- No checksum (GitHub's asset `digest` is unused) and no resume of a broken download. Ctrl-C during the download leaves `_update` behind, which blocks updates for 24 h (the message says which folder to delete).
- GitHub allows 60 unauthenticated API calls an hour per IP; on a shared campus network the exit-time release lookup can get 403. The fallback is the download page with the reason.
- The Git update on `current-stable` still runs `git add -A` + `git stash`, so local edits go into a stash silently.
- A release file the NLP Suite itself rewrites at run time would keep the backup every time; none is known.
