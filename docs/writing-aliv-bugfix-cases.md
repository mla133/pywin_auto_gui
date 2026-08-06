# Writing an ALIV bugfix regression case

`regression.md` (the curated A-H suite covered by
[`regression-coverage.md`](regression-coverage.md) and
[`adding-a-test.md`](adding-a-test.md)) is for the *stable* feature surface of
AccuMate. Individual bug tickets are a different kind of artifact: a
`scenarios/ALIV-<ticket-number>.md` file, run through `test_case_runner.py`
rather than `pytest`. This page covers when and how to add one.

## When to write an ALIV case instead of a regression.md test

Use an `ALIV-<number>.md` bugfix case when:

- You're verifying the fix for a **specific Jira ticket** (`ALIV-1234`), not a
  general feature area already covered by `regression.md`.
- The verification steps come from a **real, human-written test-case
  document** (Confluence/Jira export) with prose instructions and an
  `Expected Result`/`[PASS/FAIL]` line — not something you're authoring from
  scratch in scenario-runner's plain-English grammar.
- The case is a **one-off snap-in check**: something worth being able to
  re-run standalone later (e.g. during a future regression pass, or if the
  same area regresses again), but not worth folding into the curated A-H
  files.

If instead you're automating a scenario that's already an ID in
`regression.md` (A1-H9), follow [`adding-a-test.md`](adding-a-test.md) and
write a real `pytest` test in `tests/test_regression_<letter>.py` — don't
create an ALIV file for it.

If you just want a quick, disposable smoke-check with no bug ticket behind
it, use `scenario_runner.py` and a Markdown file under `scenarios/` with a
non-`ALIV-*` name (e.g. `scenarios/example_connect_and_save.md`) instead —
see the "Ad-hoc scenarios" section of `adding-a-test.md`.

## Naming convention (required)

The file **must** be named `scenarios/ALIV-<number>.md` (e.g.
`scenarios/ALIV-4085.md`) — the Jira ticket ID for the bug it documents. This
is a pure filename convention: `test_case_runner.py` auto-discovers any file
matching `scenarios/ALIV-*.md` via `discover_bugfix_files()`. There is no
registration step, list, or import to update — just drop the file in
`scenarios/` and it's immediately runnable via `--bugfix ALIV-4085`,
`--all-bugfixes`, or `--list-bugfixes`.

Don't name a generated report file this way — `*-report.md` files living
alongside a bugfix case are excluded from discovery automatically.

## Document format (Confluence wiki markup)

Unlike `regression.md` or scenario-runner's plain Markdown, these files use
the wiki markup Jira/Confluence exports as-is. Keep that format when
authoring a new one — don't convert it to `#`/`##` Markdown headers:

```
h4.  <Section Title>

1.  <Step text, one or more sentences, may bundle several actions and a
    verification together>
    Expected Result: _<what should happen>_ *[PASS/FAIL]*

2.  <Next step...>
    Expected Result: _<...>_ *[PASS/FAIL]*
```

Real example (`scenarios/ALIV-4085.md`):

```
h4.  Testing Firmware Upgrade

1.  Connect to the AccuLoad via Ethernet connection.  Confirm that
    731-Comm Link Programming is set to "Level 5 Access".  Confirm that
    Ethernet Host Security Level is set to anything other than "No
    Security".  Push changes to the AccuLoad and confirm via Pull Selected
    of the appropriate directories that the changes were made if
    necessary.
    Expected Result: _AccuMate connects to the AccuLoad and the parameters
    are set as above._ *[PASS/FAIL]*
```

Key structural rules `parse_test_case_document()` relies on:

- Only content **under an `h4.` header** is parsed into `TestStep`s.
  Anything before the first `h4.` (an `h3.` title, notes, a settings-value
  list) is preamble and is intentionally skipped — put scope/context notes
  there freely, they won't confuse the parser.
- Steps are **numbered** (`1.`, `2.`, ...). Each step's `Expected Result:
  ..._` line and trailing `*[PASS/FAIL]*` marker are optional but expected
  by convention — write them the same way the source ticket did.
- One step's text can bundle multiple actions and a verification into a
  single compound sentence. **Don't try to split it up** for finer-grained
  automation — see "Why compound steps aren't split" below.

## How a step gets executed: AUTO vs. MANUAL

For each step, `test_case_runner.py` checks the step's **entire text** (not
individual clauses) against two sources of automatic handlers, in order:

1. **`_TESTCASE_STEP_PATTERNS`** — a small curated set of patterns specific
   to this runner (in `test_case_runner.py`), e.g.:
   - `"Start the AccuMate Application"` → confirms the main window exists
     (the app is already launched by `run_test_case()` before any steps run).
   - `"Load test configuration file '<name>' file"` → resolves `<name>`
     against `configs/` first (falling back to the scenario file's own
     directory), then calls `workflows.file_workflows.load_config_file`.
   - `"Navigate to the X -> Y.  Click the 'Z' Ribbon button."` → a bounded
     pattern for **read-only** directory operations (Pull Selected/Pull
     All): calls `page.select_tree_path([X, Y])` then
     `page.click_ribbon(Z)`, after first checking `page.is_ribbon_enabled(Z)`
     and raising if it's disabled (so a disconnected device produces an
     honest failure, not a silent no-op false-pass).
2. **`_SAFE_STEP_HANDLERS`** — an explicit **allowlist** of a few
   `scenario_runner.py` handlers judged safe for whole-step matching against
   arbitrary prose (load test file, load config file, connect to IP, enter
   passcode, assert connected/disconnected, wait). Only handlers whose
   capture groups are tightly bounded (a literal phrase, an IPv4 address, a
   single token, a bare number) are on this list.

If neither matches, the step falls back to **`_prompt_manual_verdict`**: the
step text and Expected Result are printed, and a human is prompted to
perform/verify it and answer `[p]ass / [f]ail / [s]kip` at the console.

### Why compound steps aren't split for partial automation

This was deliberately evaluated and rejected. Most real test-case steps mix
UI actions with a state verification a human has to read off the screen
anyway (e.g. "confirm status is Offline", "confirm AccuMate prompts for a
passcode again") — clause-splitting a compound sentence to automate just the
action half would add real fragility for very little saved effort. If a step
is fully automatable, it should match a whole-step pattern above; otherwise
leave it manual.

### Why patterns are an allowlist, not a denylist

Two real false positives during `ALIV-3929.md` testing drove this design:

- `"Click on the 'Open' button in the top left corner of the application."`
  — `scenario_runner`'s open-ended `"click <name>"` catch-all captured the
  filler words as a literal (bogus) button name.
- `"Change Security Directory -> Ethernet Host Security Level to 'No
  Security'.  Confirm the AccuLoad updated the parameter.  Go offline..."`
  — the `"set/change X to Y"` pattern's non-greedy-but-end-anchored capture
  swallowed the entire trailing sentence as the "value".

Both silently attempted (and failed) the wrong auto-action instead of
correctly falling back to manual. Rather than denylisting each newly
discovered unsafe pattern, `_SAFE_STEP_HANDLERS` only allowlists handlers
whose capture groups structurally can't absorb an unrelated clause. If
you're tempted to add a new `scenario_runner` pattern to this allowlist,
convince yourself its capture group is similarly bounded first.

## Passcodes are always manual — never automate them

Steps involving entering a security passcode always pause for a human,
matched via `_step_enter_passcode` from `scenario_runner`'s grammar. Real
per-site security passcodes referenced abstractly in these documents (e.g.
"the passcode for security level 3") have no business living in a Markdown
file or this repository. **Don't** add a pattern or config value that
sources a passcode automatically, even for convenience.

## Automated post-execution verification (not just "didn't raise")

An `AUTO` step's recorded verdict isn't just "the handler ran without
raising" — where the Expected Result can be checked safely and
unambiguously with existing `app`/`page` primitives, a **verifier** function
is attached to the matched handler (`_STEP_VERIFIERS` for
`_TESTCASE_STEP_PATTERNS` handlers, `_SR_STEP_VERIFIERS` for the allowlisted
`scenario_runner` handlers) and re-checks real state afterward, turning
*that* into the recorded PASS/FAIL:

- `_tc_load_test_configuration_file` → `_verify_config_file_loaded`: polls
  the main window's title bar (up to 25s — AccuMate spends ~10-13s
  attempting a device connection using the newly-loaded config's comm
  settings before updating the title, so a short/immediate check reads the
  stale title and false-fails) for the loaded file's base name.
- `_tc_navigate_and_click_ribbon` → `_verify_no_passcode_prompt`: confirms
  no unexpected `#32770` dialog appeared after a read-only pull.
- `scenario_runner`'s `"connect to <ip>"` → `_verify_connected`: independently
  re-checks `AccuMateApp.is_device_connected()`.

Steps with **no verifier registered** keep the old "ran without raising ->
PASS" behavior — a deliberate, documented gap (e.g. "Start the AccuMate
Application" has no automated way to confirm "opens to a blank view" beyond
the window merely existing). Steps with **no matching handler at all** are
never auto-verified, even if their Expected Result happens to mention
checkable state — we only verify the aftermath of something we ourselves
executed.

When adding a new whole-step handler, ask whether its Expected Result can be
checked this way via an existing `app`/`page`/`workflows` primitive; if so,
add a verifier function and register it in the appropriate dict. If not,
it's fine to leave it unverified — don't invent a shaky check just to fill
the slot.

## Clause-level auto-check assist for MANUAL steps

Most steps stay `MANUAL` because they're compound. To still give the human
tester a head start, `auto_check_value_clauses()` scans a manual step's text
and Expected Result for the bounded shape `"Confirm/Verify that <param> is
set to '<value>'"`, reads the *actual* current value via `page.get_value()`
(a pure listview read — no side effects, no passcode), and prints an
`[AUTO-CHECK]` hint line before prompting for a verdict. The hint is folded
into the recorded note in the report, but it **never** changes the
AUTO/MANUAL classification or overrides the human's typed verdict.

Clauses it deliberately skips rather than guesses at:

- Compound clauses joining two parameters with `"&"` or the word "both"
  (e.g. `"both *1903* & *1904* is set to ..."`) — skipped whole rather than
  guessing which side the expected value applies to.
- Negated claims (`"is set to anything other than ..."`) — don't match the
  positive `is/are set to '<value>'` shape at all, so they're never
  mis-parsed as an assertion of a specific value.
- If `page.get_value()` raises (e.g. the parameter isn't in the currently
  displayed list view — common right after a fresh config load before the
  tree's been navigated), the hint reports "could not read current value"
  rather than a false mismatch.

## Bare config filenames resolve against `configs/` first

`"Load test configuration file 'ALIV-3929.AL4' file"` resolves to
`configs/ALIV-3929.AL4` via `_resolve_config_path()` — that's where saved
AccuMate config files referenced by these documents are expected to live,
matching the convention used for regression.md's file-driven tests. It
falls back to the scenario file's own directory for backward compatibility.
A filename that already includes a directory is used as-is. If your case
needs a config file, add it to `configs/` named to match what the ticket's
document references (see `configs/ALIV-3929.AL4` as a precedent).

## Running a bugfix case

```bash
# List all discovered bugfix cases:
python test_case_runner.py --list-bugfixes

# Run one case interactively (prompts for MANUAL steps at the console):
python test_case_runner.py --bugfix ALIV-4085

# Run every ALIV-*.md case found in scenarios/, writing a report per file:
python test_case_runner.py --all-bugfixes --report-dir scenarios/reports

# Equivalent to --bugfix, but by explicit path (works for non-ALIV files too):
python test_case_runner.py scenarios/ALIV-3929.md --report scenarios/ALIV-3929-report.md
```

Each run collects per-step results (`AUTO`/`MANUAL`, verdict, notes) and
writes them to a Markdown report (default `<input-name>-report.md` next to
the input file, or wherever `--report`/`--report-dir` points).

## Step-by-step: adding a new ALIV case

1. Export or transcribe the ticket's test-case document, keeping the
   `h4.`/numbered-step/`Expected Result`/`*[PASS/FAIL]*` wiki-markup format
   intact, and save it as `scenarios/ALIV-<number>.md`.
2. If any step references a saved config file, add it to `configs/` (named
   to match what the step references) so `_resolve_config_path` can find it.
3. Run it once interactively (`python test_case_runner.py --bugfix
   ALIV-<number>`) to see which steps auto-match vs. fall back to manual —
   don't assume; the console output tells you.
4. If a step you expected to auto-run instead prompts manually (or a step
   you expected to be manual worries you by auto-matching something wrong),
   check it against `_TESTCASE_STEP_PATTERNS`/`_SAFE_STEP_HANDLERS` in
   `test_case_runner.py` rather than rewording the step to fit — the safe
   default is manual, and only add a new pattern if it's genuinely bounded
   (see "Why patterns are an allowlist" above).
5. Walk through the manual prompts for real against the live app at least
   once, recording genuine PASS/FAIL verdicts, and confirm the generated
   report reads sensibly.
6. No test-runner registration, `pytest` marker, or `regression-coverage.md`
   entry is needed — ALIV cases are intentionally outside the curated A-H
   matrix. Just commit the new `scenarios/ALIV-<number>.md` (and any new
   `configs/` file it needs).

## Related docs

- [`adding-a-test.md`](adding-a-test.md) — for automating a `regression.md`
  A-H scenario ID as a real `pytest` test instead.
- [`running-tests.md`](running-tests.md) — marker/fixture cheat sheet for
  the `pytest` suite (not used by `test_case_runner.py`, which is a
  standalone script).
- [`architecture.md`](architecture.md) — the underlying `app`/`controls`/
  `pages`/`workflows` layers that both `pytest` tests and
  `test_case_runner.py` build on.
