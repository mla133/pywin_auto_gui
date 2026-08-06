# Adding a New Workflow

A "workflow" (`workflows/*.py`) is a plain function that takes an
`app_obj` (usually the `app` pytest fixture) and drives one multi-step UI
flow: opening a dialog, filling it in, clicking through a confirmation,
etc. This page walks through adding one from scratch, using patterns
already proven out in this repo.

## 1. Decide where it belongs

- **New document type / editor** (like Report, Driver Database, Equation
  Set, Translation) → new file `workflows/<thing>_workflows.py`, following
  the shape of an existing one (e.g. `workflows/equation_workflows.py` is
  the simplest complete example: `create_new_*`, `get_*_rows`,
  `insert_*`, plus upload/download thin wrappers).
- **A new step in an existing flow** (e.g. another field in the
  Communications Settings dialog) → add a function to the existing file
  (`workflows/comm_workflows.py`).
- **A shared, reusable dialog mechanic** (e.g. another "AccuMate File
  Transfer"-style dialog) → check `workflows/file_transfer_workflows.py`
  first; it's deliberately generic (`upload_file`/`download_file` take a
  `category` key) so new document types should plug into it rather than
  re-deriving the same dialog mechanics.

## 2. Follow the dual-backend dialog pattern

If your workflow opens any modal dialog (`class_name="#32770"`):

```python
from pywinauto import Desktop

def open_my_dialog(app_obj):
    win = app_obj.get_window()
    # ...trigger the dialog (ribbon click, Ctrl+shortcut, menu item)...

    # 1. Wait for it via win32 (fast, reliable existence/enabled/visible checks)
    dlg = Desktop(backend="win32").window(class_name="#32770", title="My Dialog")
    dlg.wait("exists enabled visible ready", timeout=10)

    # 2. Re-attach the SAME HWND via UIA for UIA-only features
    from pywinauto import Application
    uia_app = Application(backend="uia").connect(handle=dlg.handle)
    uia_dlg = uia_app.window(handle=dlg.handle)
    return uia_dlg
```

See `workflows/file_workflows.open_file_dialog` for the fully-worked
version of this, including the filename-edit-box + OK/Cancel button
lookup by `automation_id`.

## 3. Use ribbon helpers for ribbon buttons

Never try to find a ribbon button via the win32 backend — it isn't there.

```python
from controls.ribbon_controls import click_ribbon_button, is_ribbon_button_enabled

uia_win = app_obj.get_uia_window()
if not is_ribbon_button_enabled(uia_win, "My Button"):
    raise RuntimeError("'My Button' is disabled - check preconditions")
click_ribbon_button(uia_win, "My Button")
```

## 4. Read back state with `get_list`/`get_tree`, not a fresh dialog probe

Almost every document view (Config Directory, Report canvas [an
exception — see `report_workflows.get_report_items`'s docstring], Driver
Database, Equation Set, Translation) is a plain `SysListView32`. Reuse:

```python
from controls.common_controls import get_list, get_list_row_texts

def get_my_thing_rows(app_obj):
    lst = get_list(app_obj)
    return [get_list_row_texts(lst, i) for i in range(lst.item_count())]
```

## 5. Write a docstring that documents *why*, not just *what*

This repo's workflows/tests lean heavily on docstrings to record
hard-won findings (a control's real automation_id, a dialog's actual
button order, a device-timing quirk) so the next person doesn't have to
rediscover them live. When you find something surprising while building a
workflow (e.g. "clicking OK doesn't close the dialog, you have to click
Cancel" — see `report_workflows.py`'s B27 finding), write it down in the
function's docstring immediately.

## 6. Live-verify before considering it done

Nothing in this repo should be trusted until it's actually been run
against the real application at least once. A workflow written purely
from `scenarios/regression.md`'s prose or by pattern-matching an existing
workflow is a reasonable first draft, but:

- Mark any *test* that calls it `@pytest.mark.needs_live_verification`
  until you've run it live and confirmed control ids/dialog titles/actual
  behavior (see [`running-tests.md`](running-tests.md) for how to run
  `needs_live_verification`-marked tests explicitly).
- Watch for stray `AccuMate.exe` processes left over from earlier failed
  iterations while you debug live — they cause confusing "timed out"
  failures because a *different* stale process's window gets matched
  instead of the fresh one. `Get-Process AccuMate` + `Stop-Process -Id
  <pid> -Force` between iterations.
- Once confirmed, remove the marker and update the docstring from
  "NOT YET LIVE-VERIFIED"/TODO language to a statement of the confirmed
  behavior.

## Worked example: F14-F17 (loading an AM3 file and asserting a converted value)

A good template for "load a legacy file, then assert something about the
converted state" is `tests/test_regression_f.py`'s F14/F15/F16/F17 (added
after AM3 test files were supplied into `configs/`):

```python
def test_f15_parameter_conversions_from_a3x_configuration_file(app):
    a3x_path = os.path.join(os.path.dirname(__file__), "..", "configs", "F15.A3X")
    if not os.path.isfile(a3x_path):
        pytest.skip(f"F15: provided AM3 .a3x test file not found: {a3x_path}")

    open_file_dialog(app, a3x_path)

    title = _wait_for_title_contains(app, "F15")   # poll, don't assume it's instant
    assert "F15" in title

    page = MainPage(app, request=None)
    page.select_tree_path(["System Directory", "General Purpose"])
    assert page.get_value("System Status Display") == "Yes"
```

Notice the pattern: defensive file-existence skip (protects against a
future removal of the supporting file), a *polled* title-substring check
(not an immediate one — title bar updates can lag), then a real
domain-specific assertion (not just "it didn't crash").

See also: [`architecture.md`](architecture.md), [`adding-a-test.md`](adding-a-test.md).
