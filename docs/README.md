# Developer Documentation

Deep-dive pages for contributors extending this framework. Start with the
[README](../README.md) for a quick overview/API reference; come here for
more depth on *why* things are built the way they are and *how* to extend
them.

- [`architecture.md`](architecture.md) — the App → Controls → Pages →
  Workflows → Tests layering, dual-backend (win32/UIA) rationale, and the
  gotchas (resolved-wrapper `.child_window()`, dialog `automation_id`
  ambiguity, polling vs. sleeping, COM STA, teardown discipline) that have
  caused the most real bugs in this repo.
- [`adding-a-workflow.md`](adding-a-workflow.md) — step-by-step guide to
  adding a new `workflows/*.py` function, with a worked example.
- [`adding-a-test.md`](adding-a-test.md) — step-by-step guide to wiring a
  `scenarios/regression.md` scenario into `tests/`, choosing the right
  pytest marker, and when to use the plain-English runners instead.
- [`regression-coverage.md`](regression-coverage.md) — a status matrix of
  every scenario ID in `scenarios/regression.md`: automated, automated-but-
  marked, manual, special-case, or out of scope, and why.
- [`running-tests.md`](running-tests.md) — marker/fixture/CLI cheat sheet
  for actually running the suite.
- [`writing-aliv-bugfix-cases.md`](writing-aliv-bugfix-cases.md) — how to
  author a one-off `scenarios/ALIV-<ticket>.md` bugfix regression case and
  run it via `test_case_runner.py`, separate from the curated A-H suite.

`mn06136.pdf` in this folder is the AccuLoad device manual (reference
material, not authored documentation for this repo).
