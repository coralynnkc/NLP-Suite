# UX Modernization Proposals

**Scope:** what the CustomTkinter migration deliberately does *not* do. The migration
(`docs/CustomTkinter-Migration-Plan.md`) preserves every GUI's structure and wording exactly — its
whole safety argument rests on that. This document collects the changes that are out of scope there:
layout patterns, interaction patterns, and copy that are dated or confusing *by design*, plus a
handful of outright bugs found while auditing them.

Each item states the problem, the evidence in code, and a proposed fix. §7 sorts everything by
effort/risk into three tiers — the first tier is plain bugfixes that could ship this week; the later
tiers change behavior users may have habituated to and **need Roberto's sign-off**, same as the
theme-color question (§0 of the migration plan).

**Sequencing:** none of this should ride along inside Phase 3/4 migration tranches — a migration PR
that also changes wording or behavior can no longer be reviewed as "mechanical". Land Tier 1 as its
own small PRs anytime; Tiers 2–3 after the migration stabilizes (call it Phase 6 if useful).

---

## 1. The main-menu dropdowns: tool discovery is the suite's worst UX

The front door (`NLP_menu_main.py`) presents **seven dropdowns across two tabs**, and the user must
guess which dropdown hides the tool they want. Measured entry counts:

| Dropdown | Real entries |
|---|---|
| CORPUS/DOCUMENT Analysis Tools | 45 |
| Pre-Processing Tools | 29 |
| Visualization Tools | 15 |
| Data & Files Handling Tools | 11 |
| CORPUS Analysis Tools | 6 |
| Statistical Tools | 4 |
| SENTENCE Analysis Tools | 1 |

(lists in `constants_util.py:547-649`, wired up in `NLP_menu_main.py:559-601`)

### 1.1 Problems, in descending severity

1. **Five entries are dead on arrival — label/key drift (BUG).** A menu selection is looked up in
   the `pydict` dispatch table (`NLP_menu_main.py:219-328`) by its *exact label*. Five labels in
   `constants_util.py` no longer match any key, so selecting them shows *"was not found in the
   Python dictionary… Please, inform the NLP Suite developers"* (`IO_files_util.py:1047-1058`):
   - `File classifier (file name) (dumb classifier via embedded date)` — pydict has the two
     parentheticals in the *other order* (`NLP_menu_main.py:254`)
   - `Spelling checker cleaner (file content) (Find & Replace string)` — pydict key lacks
     `(file content)` (`NLP_menu_main.py:303`)
   - `Hedge/uncertainty annotator` — pydict key is `Annotator - hedge/uncertainty` (`:231`)
   - `Semantic analysis (via TensorFlow)` — no such key at all
   - `WordNet` — no such key at all (closest: `Semantic aggregation (WordNet, VerbNet, FrameNet)`)

   *Fix:* reconcile labels and keys, then add a startup assertion (or a unit test — the lists and
   dict are both importable without Tk) that every menu entry resolves in `pydict`. This class of
   bug will otherwise recur every time someone rewords a label.

2. **Separator and blank rows are selectable.** The lists embed `''` and
   `'-----------------…'` rows as entries; picking one earns a warning popup telling you it "is
   only an explanatory label" (`IO_files_util.py:1050-1053`). A menu should not offer choices that
   exist to be refused. *Fix (short-term):* swallow these selections silently in the trace and
   reset the variable. *Fix (real):* see §1.2 — a widget that supports non-selectable headers.

3. **"Not available" tools are still listed.** Entries mapped to `["", 0]` (e.g. `SRL Semantic
   Role Labeling`, `Similarities between documents (via Python difflib)`, `Sentence visualization:
   Dynamic sentence network viewer`) produce *"not available yet. Sorry!"*
   (`IO_files_util.py:1060-1062`). Same principle as the greyed video buttons (§2): if it can't
   go, don't offer it — or suffix the label `(coming soon)` and grey it, but never let selecting
   it be the way the user finds out.

4. **Heavy overlap between menus with inconsistent labels.** The same script appears under
   several dropdowns with different names (`file_checker_converter_cleaner_main.py` appears ~8
   times; `NGrams_CoOccurrences_main.py` under at least 6 labels including both
   `N-grams & Co-occurrences` and `N-grams & Co-Occurrences`). Users can't tell whether two
   entries are two tools or one.

5. **The select-then-RUN two-step is undiscoverable.** Picking an entry does nothing visible — it
   silently sets `script_to_run` and *clears the other six dropdowns*
   (`clear_selected_options`, `NLP_menu_main.py:603-652`); the user must then know to press RUN.
   Nothing on screen says so; the only hint is a warning popup if they press RUN with nothing
   selected. (Esc-to-clear is likewise invisible — documented only inside `?HELP` popups.)

### 1.2 Proposed direction

The honest fix is to stop using dropdowns as a tool catalog. Two options, in ascending ambition:

- **A. Searchable flat list (recommended).** One type-to-filter search box over *all* tools, plus
  the categorized list below it as a browse fallback. The suite already contains an unfinished
  `combobox_with_search_widget` (migration plan, Phase 4 deferred) pointing the same direction.
  With ~110 labels, filtering beats categorizing: a user who wants "sentiment" should type it,
  not learn the taxonomy. CTk has no Listbox, but the migration plan (§3) already sanctions a
  styled `tk.Listbox` in a `CTkFrame`, or a `CTkScrollableFrame` of buttons.
- **B. Keep the two-tab layout, upgrade each category to a proper picker** — a popup list with
  bold non-selectable section headers, one click to choose, double-click (or an explicit button)
  to launch. Less new design, keeps the current mental model.

Either way: dedupe labels, one canonical name per tool, launch on an explicit affordance rather
than a variable trace, and show the current selection prominently (see §3 — put it *on* the RUN
button).

---

## 2. Disabled chrome that should be absent — or should just go

### 2.1 Greyed "No videos/TIPS/reminders available" dropdowns

When a GUI has no videos, the bottom bar still shows a full-size greyed dropdown reading "No
videos available" (`GUI_util.py:1703-1718`; same pattern for TIPS `:1728-1743` and reminders
`:1766-1785`). It occupies the same space as a working one and its only behavior is a popup saying
there are none. Under the cut-3 color rule this is now *correctly* grey — but a control whose only
message is "I don't exist" shouldn't be a control.

*Proposal:* when the lookup is empty, don't build the widget (the grid reflows; absolute layout
never allowed this, the grid does). If Roberto wants the bar visually stable across GUIs, the
fallback is a small dimmed *label* ("no videos for this tool"), which at least isn't clickable.

Also: when exactly **one** video/TIPS exists, a dropdown is the wrong widget — make it a button
that just opens the thing ("▶ Watch: Setup the NLP Suite"). Dropdown-as-launcher is a recurring
pattern worth retiring generally: the bottom bar's chart-type and data-tools dropdowns *launch
entire GUIs* as a side effect of selection (`GUI_util.py:1649-1678`), and their `'_______ Open
GUI'` separator entries reset themselves when clicked (`:1654-1655`). Selection should select;
buttons should launch.

### 2.2 Disabled checkboxes as status lights

The three SETUP rows on the main menu each start with a **permanently disabled checkbox** whose
tick means "this setup is complete" (`NLP_menu_main.py:376-435`; the tooltip even has to explain
"The checkbox, always disabled, is ticked ON when…"). A disabled checkbox reads as a broken
control, not a status. One of them (`setup_external_software_checkbox`, `:434`) even has a
`command=` that can never fire.

*Proposal:* replace with a status glyph + short label (`✓ configured` in green / `✗ not set up`
in the theme red) rendered as a plain `CTkLabel`. Cheap, and it removes three tooltips whose only
job is apologizing for the widget choice.

---

## 3. RUN semantics on the main menu

`run_button_state` is forced to `'normal'` for `NLP_menu_main` (`GUI_util.py:680-683`), so RUN
glows brand-red from the moment the menu opens — but with nothing selected, pressing it just pops
*"No option has been selected."* (`NLP_menu_main.py:49-51`). Under the §0 design premise ("color
is a signal"), this is the signal lying: red is supposed to mean *this will do something*.

*Proposal:*

1. Start RUN **disabled** on the menu; enable it inside `getScript` when `script_to_run` becomes
   non-empty; disable again when Esc/`clear` empties it. The trace plumbing already exists — this
   is a ~10-line change and deletes the warning popup path.
2. Better still, make RUN show its target: `RUN: Sentiment analysis` (a `configure(text=…)` in the
   same trace). This simultaneously fixes §1.1's "selection does nothing visible" — the selection
   now visibly lands somewhere, and the two-step becomes self-explanatory.

The same "red = will actually run" audit is worth doing per-GUI during migration QA: any GUI where
RUN is enabled but a required option is missing has the identical problem in miniature.

---

## 4. Copy editing: tooltips, popups, and labels

The in-app text is the suite's primary documentation and it reads as unedited first drafts.
Distinct problems:

1. **Typos, in user-facing strings** (grep-verified, non-exhaustive):
   - `currrently` — `NLP_menu_main.py:166,170,178,185,192` (five warning dialogs)
   - `laguage` — `NLP_menu_main.py:425` (tooltip)
   - `Setup NPUT/OUTPUT configuration` — `GUI_util.py:916` (tooltip)
   - `Square rooot` — `GUI_util.py:1633` (a **dropdown entry** every GUI's bottom bar shows)
   - `subdirecory`, `followining` — `NLP_menu_main.py:714-718` (help popups)
2. **Stale mechanics described in tooltips.** The videos/TIPS/reminders tooltips still say the
   widget turns "red, otherwise black" (`GUI_util.py:1718,1743,1785`) — under the CTk theme the
   unavailable state is grey, and if Roberto flips the cut-3 encoding the text drifts again.
   Tooltips shouldn't narrate color codes at all; the color should be legible on its own (§2.1).
3. **Wall-of-text popups.** Help/warning dialogs routinely run 10+ sentences with full file-path
   walkthroughs (e.g. the external-software help, `NLP_menu_main.py:717-723`). A dialog is for
   one decision; reference material belongs in TIPS PDFs, which already exist for exactly this.
4. **No shared voice.** Mixed "Please, using the dropdown menu, select…" / ALL-CAPS emphasis /
   "Sorry!" endings; `Fatal error` titles on recoverable validation misses
   (`NLP_menu_main.py:165-193` — nothing fatal happens; the user just picks a file and retries).

*Proposal:* one dedicated copy-editing PR over `text_info` strings, dialog bodies, and labels, with
a five-line style guide committed alongside (imperative first sentence; tooltips ≤ 3 lines, details
go to TIPS; `Warning` vs `Error` used honestly; no trailing apologies). Note the migration plan's
§5.3 "preserve tooltips verbatim" rule constrains *migration* PRs only — a deliberate, reviewed
copy pass is the sanctioned way to change them. The strings are all literals in `.py` files, so the
pass is greppable and mechanically reviewable.

---

## 5. The INPUT/OUTPUT path display

The selected I/O paths are shown as bare labels bound to the path variables
(`GUI_util.py:1048,1079` in `IO_config_setup_full`; the two-line summary label in
`IO_config_setup_brief`, `:951`). Long paths render as long flat strings floating in the window;
the "open" affordance is a separate 📂 button cluster elsewhere on the row; nothing distinguishes
the part you care about (the corpus folder name) from the noise (`/Users/…/Documents/…`).

*Proposal:* a small `path_display` widget in `GUI_theme_util`, used by both call sites:

- a framed, read-only chip (a `CTkEntry` in disabled/readonly styling or a bordered `CTkLabel`) so
  it reads as *data*, not stray text;
- middle-ellipsis for long paths (`/Users/…/newspaperArticles`), full path in the tooltip;
- basename emphasized (bold), parent dimmed;
- click = open in Finder/Explorer, absorbing the adjacent 📂 buttons, with a leading
  `INPUT DIR:` / `OUTPUT:` caption.

One widget, two call sites, and every GUI inherits it — same leverage pattern the migration relies
on. (Keep `IO_path_labels` publishing whatever widget results, since GUIs attach tooltips to it.)

---

## 6. Broader modernization (needs discussion, bigger lifts)

- **Startup dialog storm.** A fresh launch can chain: default-config-created info box
  (`NLP_menu_main.py:804`), the three-setups-incomplete `askyesno` (`:825`), an Apple-Silicon
  TensorFlow warning (`:851`), plus reminder popups (`:742-753`). Each is modal; the user clicks
  through blind. *Proposal:* fold all launch-time status into one in-window setup checklist/banner
  (the §2.2 status row is halfway there) and reserve modals for questions that block.
- **CLOSE silently self-updates.** The CLOSE button's command pulls the latest release from GitHub
  (`GUI_util.py:1816-1836`); the only disclosure is its tooltip. Auto-update on *exit* is
  surprising and failure-prone on bad connections. *Proposal:* decouple — CLOSE closes; update is
  an explicit "Check for updates" action (or an on-launch notification), with its own consent.
- **A persistent Home.** The welcome screen already exists but self-retires after 3 launches
  (`NLP_menu_main.py:57-81`). If §1 becomes a searchable catalog, the welcome content (what is
  this, sample corpus, first-run checklist) could live as a third tab instead of disappearing.
- **Appearance-mode toggle** — already planned (migration Phase 5); listed here only because users
  will read "dark mode" as the headline modernization feature.

---

## 7. Priority / effort summary

**Tier 1 — bugfixes & trivial polish (ship now, no design debate):**

| Item | Where | Effort |
|---|---|---|
| 5 dead menu labels reconciled with `pydict` + test | §1.1(1) | hours |
| Separator/blank rows swallowed silently | §1.1(2) | hours |
| Typo sweep (`currrently`, `laguage`, `NPUT`, `Square rooot`, …) | §4(1) | hours |
| Stale "red, otherwise black" tooltip text | §4(2) | minutes |
| Dead `command=` on disabled checkbox | §2.2 | minutes |

**Tier 2 — low-risk UX wins (small PRs, Roberto sign-off on each):**

RUN disabled-until-selected + `RUN: <tool>` label (§3) · hide/replace empty videos/TIPS/reminders
dropdowns, single-item dropdowns → buttons (§2.1) · status glyphs replacing disabled checkboxes
(§2.2) · `path_display` widget (§5) · "not available" entries removed or badged (§1.1(3)) ·
copy-editing PR + style guide (§4).

**Tier 3 — real design projects (spec first, then build):**

Searchable tool catalog replacing the seven dropdowns (§1.2) · startup checklist replacing the
dialog chain (§6) · decoupling CLOSE from auto-update (§6) · persistent Home tab (§6).

Tier 3 items each deserve the same treatment the migration got: a short design note in `docs/`,
Roberto's agreement on the premise, then implementation — they change workflows long-time users
have memorized, and this project's history (§0.1 of the migration plan, twice-reverted color cuts)
shows that shipping UX opinions without that agreement doesn't stick.
