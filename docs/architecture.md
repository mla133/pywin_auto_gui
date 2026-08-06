# Architecture Deep-Dive

This page expands on the README's "Architecture" section for contributors
who need to *extend* the framework, not just use it. If you just want to
run existing tests, the [README](../README.md) is enough.

## The five layers

```
AccuMateApp            (app/application.py)
   │  launches/attaches to the real .exe, exposes get_window()/get_uia_window()
   ▼
controls/*.py
   │  low-level, backend-agnostic control lookup (list/tree/ribbon/dialog)
   ▼
pages/MainPage          (pages/main_page.py)
   │  page-object: tree/list interactions + @auto_step screenshot capture
   ▼
workflows/*.py
   │  multi-step flows composed from app/controls: open a file, connect to
   │  a device, upload/download, drive a specific editor's dialogs, etc.
   ▼
tests/test_*.py
      pytest tests compose workflows + MainPage into full scenarios
```

Every `workflows/*.py` function takes an `app_obj` (an `AccuMateApp`
instance, normally the `app` pytest fixture) as its **first** argument and
calls back into `app_obj.get_window()` / `app_obj.get_uia_window()` as
needed. This is what keeps workflows composable, testable outside of
pytest (see `scenario_runner.py`), and reusable across multiple document
types.

**Rule of thumb for where new code belongs:**

- Talks to `pywinauto`/Win32 primitives directly, with no knowledge of
  *why* → `controls/`.
- Wraps the main Config/Tree/List document view specifically → `pages/`.
- Drives a specific dialog/document type/multi-step flow → `workflows/`.
- Composes the above into an assertion against `scenarios/regression.md`
  → `tests/`.

## Why two backends (win32 + UIA)?

AccuMate is an MFC ribbon application. Its **tree/list/dialog controls**
are classic Win32 (`SysTreeView32`, `SysListView32`, `#32770`), but its
**ribbon buttons** are drawn by the ribbon framework and have no Win32
handle of their own — they only exist via the UIA (UI Automation)
accessibility tree.

- `app.get_window()` → win32 backend. Use for tree/list interactions,
  waiting for dialogs to appear, reading `window_text()`/`control_id()`.
- `app.get_uia_window()` → UIA backend, **attached to the same HWND**
  (cached on `app._uia_app`). Use for ribbon buttons
  (`controls/ribbon_controls.py`) and for UIA-only dialog features (e.g.
  `set_edit_text` on a common-dialog Edit control).

**Modal dialogs use both, in sequence**: attach via win32 to *wait for*
the dialog to exist (`Desktop(backend="win32").window(...).wait(...)`),
then re-attach the *same HWND* via UIA when you need a UIA-only
capability. See `workflows/file_workflows.open_file_dialog` for the
canonical example of this pattern.

## The `WindowSpecification` vs. resolved-wrapper gotcha

`AccuMateApp.get_window()`/`get_uia_window()` both return **resolved
wrappers** (the result of `.wrapper_object()`), not a lazy
`WindowSpecification`. This means:

```python
win = app.get_window()
win.child_window(title="OK", control_type="Button")   # AttributeError!
```

`.child_window()` only exists on `WindowSpecification`. On a resolved
wrapper, scan `.descendants()` (optionally `class_name=...`) and match
manually instead:

```python
for d in win.descendants(class_name="Button"):
    if d.window_text() == "OK":
        d.click_input()
        break
```

This was the root cause of several real bugs early in this project
(`ribbon_controls.find_ribbon_button`, `common_controls.wait_for_control`,
`comm_workflows._find_by_control_id`) — if you hit an `AttributeError`
mentioning `child_window`, this is almost certainly why.

## Dialogs need stable identifiers, not `title`/`control_type` alone

Modern Explorer-style common dialogs (Open/Save As) expose *many*
same-titled/same-typed controls (e.g. 14 `Edit`-type elements in the Open
dialog for search boxes, column headers, etc., and 3 `Button`s all titled
"Open"). `child_window(title=..., control_type=...)` raises
`ElementAmbiguousError` in these cases.

**Prefer `automation_id`** discovered by probing the real dialog once
(e.g. `"1148"` for the Open dialog's filename Edit box, `"1"`/`"2"` for
the standard `IDOK`/`IDCANCEL` buttons). For a custom AccuMate dialog with
no documented automation_id, use `control_id()` (Win32's `IDOK`=1,
`IDCANCEL`=2, `IDYES`=6, `IDNO`=7 are stable Windows conventions worth
matching on directly rather than a translatable button title).

## Polling, not sleeping

Every wait in this repo is a **poll-with-timeout** loop
(`wait_for_control`, `wait_until`, or a manual `while time.time() - start
< timeout: ... time.sleep(...)`), never a hard `time.sleep(N)` used as the
*only* synchronization mechanism. AccuMate's own state transitions
(device connection attempts, title bar updates after a file loads) can
take anywhere from under a second to 10+ seconds depending on what else
is happening (e.g. a baked-in comm-settings connection attempt kicking
off before a newly-loaded file's title updates) — a fixed sleep is either
too slow (wastes time on every run) or too fast (flaky failures).

## COM STA requirement

`tests/conftest.py` has an autouse fixture wrapping every test in
`pythoncom.CoInitialize()`/`CoUninitialize()`. pywinauto's UIA backend
needs an STA-threaded COM apartment; removing this fixture reintroduces
`0x80040155`/`0x8001010D` COM errors. If you write a new standalone script
(like `scenario_runner.py`) that uses the UIA backend outside of pytest,
you need the same `CoInitialize()` call yourself.

## Teardown discipline

The root `conftest.py`'s `app` fixture and `MainPage._auto_screenshot`
both swallow screenshot/teardown exceptions (`try/except` + `[WARN]`
print) so a failure capturing a screenshot never masks the real test
failure. The app process is always force-killed
(`taskkill /PID <pid> /F /T`) afterward to avoid orphaned `AccuMate.exe`
processes accumulating between runs — a real, recurring failure mode
during development is a stray process from an earlier failed run holding
a stale dialog open and confusing a *later* test's window-matching logic.
If a test behaves inexplicably, check `Get-Process AccuMate` first.

## Two ways to describe a test

1. **pytest** (`tests/test_*.py`) — the primary, CI-friendly path. Full
   assertions, fixtures, markers.
2. **Plain-English runners** (`scenario_runner.py`, `test_case_runner.py`)
   — for fast manual exploration/reproduction or for real Jira/Confluence
   test-case documents that mix automatable and genuinely-manual steps.
   These reuse the exact same `workflows/`/`pages.MainPage` functions as
   the pytest suite; they're a different *front door* onto the same
   underlying API, not a separate implementation. See
   [`adding-a-test.md`](adding-a-test.md) for when to use which.

See also: [`adding-a-workflow.md`](adding-a-workflow.md),
[`adding-a-test.md`](adding-a-test.md),
[`regression-coverage.md`](regression-coverage.md),
[`running-tests.md`](running-tests.md).
