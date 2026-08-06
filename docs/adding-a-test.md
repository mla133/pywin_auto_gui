# Adding a New Test

This page is a practical checklist for wiring a new `scenarios/regression.md`
scenario into `tests/`, or for capturing a one-off bugfix regression case.
For workflow-level (`workflows/*.py`) additions, see
[`adding-a-workflow.md`](adding-a-workflow.md) first — a new test usually
needs supporting workflow functions to already exist (or be added
alongside it).

## Which kind of test are you adding?

| Situation                                                | Where it goes                                                                                                          |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| A scenario from `scenarios/regression.md`'s A-H sections | `tests/test_regression_<letter>.py`, one function per scenario ID                                                      |
| A one-off bugfix verification (e.g. ALIV-1234)           | `scenarios/ALIV-1234.md` (wiki-markup test-case doc), run via `test_case_runner.py` — **not** a pytest test, see below |
| Ad-hoc manual exploration/reproduction                   | A throwaway `scenarios/*.md` file run via `scenario_runner.py` — no pytest file needed at all                          |

## Wiring a `regression.md` scenario (the common case)

1. **Find the scenario's exact text** in `scenarios/regression.md` (search
   for its `h4. <ID>: <title>` heading) — the literal step text and
   "Expected Result" are your source of truth for what to assert.
2. **Check for an existing stub.** Most scenario IDs already have a
   `pytest.skip(...)` placeholder in the matching
   `tests/test_regression_<letter>.py` file — rewrite it in place rather
   than adding a new function.
3. **Reuse an existing workflow** if the document type/dialog is already
   covered (see [`adding-a-workflow.md`](adding-a-workflow.md) step 1) —
   don't re-derive dialog mechanics that already exist.
4. **Decide what markers apply**:
   - `@pytest.mark.requires_device` — needs a live, reachable AccuLoad.
   - `@pytest.mark.disruptive` — mutates persistent live-device state
     (e.g. resets IP/netmask) in a way that could break a *later* test in
     the same run. Excluded from default runs.
   - `@pytest.mark.needs_live_verification` — written from
     docs/inference, not yet confirmed against the real app. **Always**
     start here for a brand-new test; remove it only after a live pass.
   - `@pytest.mark.installs_software` — performs a real install/uninstall.
   - `@pytest.mark.manual` — genuinely cannot be automated from this repo
     at all (missing hardware/file/access, or needs human judgment) — see
     [`regression-coverage.md`](regression-coverage.md) for real examples
     (F6, F8, G1, G4, G5) and their docstrings for the reasoning to
     model a new one on.
   - `@pytest.mark.special_case` — *can* be automated, but only applies
     when the physical device is deliberately put into an atypical state
     (e.g. "no file present after Factory Init") that this repo has no
     safe way to arrange or verify (see B14/C6/D8/E6). Don't invent a
     device-state assumption to force a pass — mark it `special_case` and
     document exactly what precondition a human would need to arrange.
5. **Write the test body**, then **run it live** (`pytest -s -v
   tests/test_regression_<letter>.py::test_<id>_<slug> -m ""` — the `-m
   ""` override is needed if it's still marked
   `needs_live_verification`/`manual`/etc., since those are excluded from
   default `addopts`).
6. **Watch for stray `AccuMate.exe` processes** between debug iterations
   (`Get-Process AccuMate`) — a leftover process from a prior failed run
   is the single most common cause of a confusing "this should work but
   times out" failure.
7. Once it passes reliably, **remove `needs_live_verification`**, update
   the docstring from speculative/TODO language to a statement of
   confirmed behavior (cite the exact dialog text, control id, or
   surprising finding you hit), and run the whole letter's suite once
   more to check for regressions:
   
   ```bash
   pytest -s -v tests/test_regression_<letter>.py
   ```
8. Update the module's docstring "Scope summary" section if one exists —
   these files intentionally keep a running summary of what's automated,
   what's blocked, and why, at the top of the file.

## Wiring a bugfix regression case (ALIV-*.md)

Don't write a pytest test for a one-off bugfix verification. Instead, drop
a new `scenarios/ALIV-<ticket-number>.md` file (same wiki-markup format as
the existing `ALIV-3929.md`/`ALIV-4085.md` — `h3.`/`h4.` headers,
numbered steps, an `Expected Result: ..._` line) into `scenarios/`. It's
auto-discovered by filename — no registration step needed:

```bash
python test_case_runner.py --list-bugfixes
python test_case_runner.py --bugfix ALIV-1234
python test_case_runner.py --all-bugfixes --report-dir scenarios/reports
```

`test_case_runner.py` runs each step through a small curated
pattern-matcher (`_TESTCASE_STEP_PATTERNS`/`_SAFE_STEP_HANDLERS`) for
fully-automatable phrasings, and pauses for a human PASS/FAIL/SKIP verdict
on everything else (most real test-case steps mix several UI actions with
a judgment call, so this is deliberate, not a gap). Only extend the
pattern set with genuinely bounded phrasings (fixed literal text, or a
capture group constrained to something that can't swallow an unrelated
clause) — see `test_case_runner.py`'s module docstring for two real false
positives this caused and how they were fixed.

## Ad-hoc scenario exploration (no test file at all)

For quick manual reproduction while debugging (no assertions needed,
just "drive the app through these steps"):

```markdown
<!-- scenarios/my_repro.md -->
- Connect to 10.55.66.70
- Verify that the device is connected
- Save as C:\temp\test2.al4
```

```bash
python scenario_runner.py scenarios/my_repro.md
```

Recognized phrasings live in `scenario_runner.py`'s `_STEP_PATTERNS`
registry — unrecognized steps are reported and skipped rather than
guessed at. Extend the registry with `@step(pattern)` if you find
yourself repeating the same manual step across scenarios.

See also: [`architecture.md`](architecture.md),
[`adding-a-workflow.md`](adding-a-workflow.md),
[`regression-coverage.md`](regression-coverage.md),
[`running-tests.md`](running-tests.md).
