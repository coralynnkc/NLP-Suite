# PLAN — NLP Suite

What to do before tagging the next release, and what comes after it. The findings behind each item (evidence, line numbers, proposed fixes) are in [docs/future-work.md](docs/future-work.md); section numbers below refer to it. How to fix an issue is in [CLAUDE.md](CLAUDE.md#fixing-an-issue); how a release is checked is in §14. What has shipped is in [CHANGELOG.md](CHANGELOG.md).

**Last updated:** 28 Nov 2026: candidates `release/v1.6.48` and `release/v1.6.49`, checked on CI (below). v1.6.47 (Python 3.11, Pillow 13, transformers 5: the security release) released 23 Nov; v1.6.46 (fixes from the tool sweep) 23 Nov; v1.6.45 (HW 5 speedups) 22 Nov; v1.6.44 (bundle size) 21 Nov. Releases are Cora's (handed over by Roberto). HW 5 is due Sun 6 Dec.

## Next: 1.6.48, cleanup and what the sweep left

No dependency changes: `requirements*.txt` and the bundled Python (python-build-standalone `20251217`) stay as in 1.6.47, so the sweep against 1.6.47 shows only what the code changed.

**The candidate is `release/v1.6.48`** (28 Nov): #1803 (tests one file per module), #1779 and the categorical charts, the source-checkout sweep config, the dialog-free tests (`fix/tests-no-real-dialogs`), the tie-order fix (`fix/tie-order`, §12.4), the self-updater start race (`fix/updater-swap-start-race-148`, §15), #1706 (`chore/remove-dead-files`), and the version bump. `pytest tests/` 972 passed; `gui_smoke.py` crash list the same as `roberto`'s (Linux).

1. **Checks before the tag** (§14), on CI: the test branch `claude/tcl9-gui-upgrades-0fr6u2` builds the candidate and runs, on Windows and the Mac against the published 1.6.47 zips, the tool sweep and its compare, `bundle_gate.py`, the self-updater 1.6.47 → 1.6.48 (1.6.47's own updater, `.github/tk9-check/self_update_check.py`), the layout gate and the screenshot gallery (run 46165327627, started 28 Nov 16:28). Windows may show 1.6.47's 30 s start race once (§15); the fix is in 1.6.48's own updater. After promotion, merge the release branch back into `roberto` with a merge commit (#1804 did it for 1.6.47).

## 1.6.49: the newest CPython 3.11, with Tcl/Tk 9 on the Mac (§3.3)

**The candidate is `release/v1.6.49`** (28 Nov): `release/v1.6.48` plus `chore/tcl9-trace-add` and `chore/1.6.49-python-3.11.18`, and the version bump. `pytest tests/` 979 passed. Checked on CI against the published 1.6.47 (run 46120257866 and the GUI checks of 28 Nov, §3.3): sweep 0 regressions on Windows and the Mac, `bundle_gate` 0 failures on both, layout the same as 1.6.47 on both (Windows at 1920x1080: 50/50 pass; Mac: Tk 9 matches Tk 8.6 but for 5 px in Semantic aggregation), Windows process DPI-unaware on both. Still to do: rerun those checks against the published 1.6.48, the self-updater 1.6.48 → 1.6.49, and a person looking at the Mac GUIs on Tk 9 (the runner cannot take Mac screenshots) and at the `tkcolorpicker` dialog.

1.6.47 bundles CPython 3.11.14 from python-build-standalone `20251217`, the last release with Tcl/Tk 8.6. The newest 3.11 (3.11.18, `20261124`) comes with Tcl/Tk 9 on the Mac (the Windows build keeps Tcl/Tk 8.6.15, found 28 Nov), which crashed 54 GUIs at open in the first 1.6.47 candidate. Porting `src/` to Tcl 9 lets the bundled Python take four more CPython patch releases. Its own release, because it touches every GUI. Where it stands (27 Nov, §3.3):
1. `chore/tcl9-trace-add`: the 286 traces ported, and `tk9_fonts_util` for Tk 9's larger fonts on the Mac. On a Tcl 9 env every GUI builds (54 crashed before), records the same popups as on 8.6, and the layout gate matches 8.6 (49 of 50; 11 without the font fix). On `release/v1.6.49`; it changes nothing on 8.6.
2. `chore/1.6.49-python-3.11.18` (on top of 1): `PBS_TAG` `20261124`, CPython 3.11.18, Tcl/Tk 9.0.4 on the Mac and 8.6.15 on Windows; the build's Tcl check expects 9 on the Mac and 8.6 on Windows (it expected 9 on both, which failed every Windows build).
3. **Done against 1.6.47 (28 Nov, CI):** sweep 0 regressions on both platforms (only tie order and ~1e-6 float noise); `bundle_gate.py` 0 failures on both; layout gate with dialogs answered: Windows at 1920x1080 50/50 pass on both Tk 8.6.12 and 8.6.15, Mac 6/50 on both Tk 8.6.14 and Tk 9.0.4 with the same numbers but for 5 px in Semantic aggregation (the Mac runner's ~1024 px screen fails the rest, alike on both); Windows process DPI-unaware before and after Tk on both, so 150 % scaling behaves as today; Tk 9 features present on the Mac candidate (SVG photos, `tk print`/`systray`/`sysnotify`, `<TouchpadScroll>`) and absent on Windows; self-updater 1.6.47 → candidate passed on the Mac.
4. **Before the tag:** after 1.6.48 is published, rerun the release-candidate checks with `baseline` 1.6.48 (Actions tab, "Release candidate checks", Run workflow), which also covers the self-updater 1.6.48 → 1.6.49 (the second python-env swap). On a Mac, by hand: open the 1.6.49 zip's menu and about ten GUIs beside 1.6.47 (text size, clipping, checkboxes), the welcome screen and logo, and Data visualization's two colour buttons (`tkcolorpicker` on Tk 9); `.github/tk9-check/gui_gallery.py` makes a screenshot page of every GUI (the Mac runner cannot take screenshots). Do not tag 1.6.49 before these.

## Still to check on the published releases

On 28 Nov CI ran the **published 1.6.47 Windows and Mac zips** as baselines: the full tool sweep (129 recipes, CoreNLP and MALLET included), `bundle_gate.py`, the layout gate and the gallery, and the self-updater from 1.6.47 on both. That covers most of item 1 below on a runner; what still needs a Windows machine by hand:
1. The menu from the zip, and one tool per family on `python-env` (§2.5): BERT NER, BERTopic, fastcoref coreference, Stanza coreference, WSI with BERT, a CoreNLP parse with the bundled JRE, a GIS map, wordclouds, an Excel chart.
2. Shape of Stories with Hierarchical Clustering ticked (the default); NRC and SentiWordNet; #1705's start-up popups (menu with an empty `config/`, each Setup GUI); the first Stanza download (#1704); the welcome screen and logo (Pillow 13).
3. The self-updater from a 1.6.46 install to 1.6.47: the first update that replaces the bundled Python, through the Windows (PowerShell) swap script, which the Mac check on 23 Nov did not exercise. Read `%TEMP%\NLP_Suite_update.log`.

Ask students who report update problems to send the update log to coralynn.yang@emory.edu.

## After 1.6.49

- **Release checks into the repo** (from the test branch `claude/tcl9-gui-upgrades-0fr6u2`): `tk9-windows-check.yml` ("Release candidate checks", baseline chosen at start), `gui-checks.yml`, `.github/tk9-check/` (probes, `self_update_check.py`, `unzip_bundle.sh`), and `workflow_call` in `build-installers.yml`. Fold `no_popups.py` and `run_bounded` into `tests/gui_layout_gate.py` itself (on a runner, GUIs that pop up a dialog or launch another program at open hung it for hours) and add `gui_gallery.py` to `tests/` (§7.4 asks for it). Its own PR.
- **Mac screenshots on CI:** Pillow's `ImageGrab` on the macOS runner returns no image (likely no Screen Recording permission); try granting it, or keep the Mac look a manual check.
- **WordNet zoom-in list order** (§12.4): still changes between builds on one fixed keyword; find out whether NLTK or its WordNet data differ between the two zips.
- **Python 3.14** (future-work §3.4): the only way to Tcl/Tk 9 on Windows, and due before 3.11's end of life (October 2027). Requirements resolve on 3.14 for both platforms; gensim has no 3.14 wheels and must build from source. Its own release, like 1.6.47.
- **pandas 3, folium 1, ipython 9** (§3.2): 1.6.47 caps them below those versions; moving to each is its own change, tested with the sweep.
- **Trim the spec further** (§2.1): it keeps spaCy, pandas and the rest for the language advisor, which since #1732 runs on `python-env`. Probe build first.
- **Performance**, in §6.10's order: next, pandas out of `GUI_util` (§6.3).
- PR #1682 (spaCy CoNLL IDs, a shared structure) and PR #1683, which needs changes (§9). Close the four stale 2024 PRs with a thank-you comment.
- Smaller copy left from #1705 (§5.2); the repeated config warning on a first run from source (§5.3).
- Roberto's decisions on outdated flows: SRL in the zip, Java row, coreference default, N-grams VIEWER, MALLET coherence, reminders (§5.1).
- Retest and close recent issues that releases may have fixed; fix the open recent bugs (§10). Triage the 2021–2024 backlog (§11).
- The updater's known limits: long paths, no checksum or resume, the GitHub API rate limit, the silent `git stash` (§15).
- UI overhaul (§7), as its own releases.
- Tech debt in §12's order, and the missing chart regression tests (§12.6).
- Stale remote branches (§13): delete Cora's merged ones; the others are Roberto's call.
