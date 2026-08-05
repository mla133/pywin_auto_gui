# pywin_auto_gui

A Python-based UI automation test framework for **AccuMate for AccuLoad**, a
Win32/MFC desktop application, built on **pywinauto** + **pytest**.

There is no mocking layer here — every test drives the real application
binary. This README documents the API as it stands today so a new
contributor can start writing tests (or ad-hoc automation scripts) quickly.

---

# 🚀 Features

- Automates a real Win32/MFC ribbon UI via `pywinauto` (dual win32 + UIA
  backends, since MFC ribbon buttons aren't exposed as native win32
  controls)
- Layered architecture: **App → Controls → Pages → Workflows → Tests**
- Robust window/dialog handling: polling waits (not hard sleeps), automatic
  win32 ↔ UIA re-attachment for modal dialogs
- Tree (`SysTreeView32`) and ListView (`SysListView32`) navigation helpers
- Ribbon button discovery/click/enabled-state helpers
- Device connectivity workflow (configure IP, connect, poll for a live
  AccuLoad IV connection)
- File open/save/"Save As" workflows, including the non-UIA-accessible
  ribbon "Application Button" backstage menu
- A shared "AccuMate File Transfer" dialog workflow (upload/download to a
  live device) reused across every document type (Report, Driver Database,
  Equation Set, Translation, Logs)
- Pytest-based test execution with custom markers for device-dependent /
  disruptive / not-yet-verified tests
- Two higher-level "just describe the steps" runners
  (`scenario_runner.py`, `test_case_runner.py`) for turning plain-English
  test scripts into automated runs without writing new pytest code
- Automatic teardown (screenshot + force-kill, no orphaned processes)
- Auto-screenshot after every `MainPage` interaction step, for
  headless/CI-friendly debugging

---

# 📁 Project Structure

```
pywin_auto_gui/
│
├── app/
│   └── application.py        # AccuMateApp: launch/attach, get_window()/get_uia_window(),
│                              # is_device_connected(), wait_for_device_connection()
│
├── controls/                 # Low-level, backend-agnostic UI helpers
│   ├── common_controls.py    # wait_for_control, get_list, get_tree, get_list_row_texts
│   ├── ribbon_controls.py    # find/click/is_enabled ribbon button, find_app_button
│   ├── debug_tools.py        # safe_dump_control (describe a control from an STA thread)
│   └── uia_sta.py            # run_in_sta (dedicated STA thread for UIA calls)
│
├── pages/
│   └── main_page.py           # MainPage: tree/list interactions, @auto_step screenshots
│
├── workflows/                 # Higher-level, multi-step flows (plain functions, take app_obj)
│   ├── file_workflows.py          # open/save/"Save As", New-document flyout, Close
│   ├── comm_workflows.py          # Communications Settings dialog, configure_ip_and_connect
│   ├── security_workflows.py      # passcode entry (incl. "incorrect passcode" retry)
│   ├── file_transfer_workflows.py # shared "AccuMate File Transfer" upload/download dialog
│   ├── driver_db_workflows.py     # Driver Database editor + upload/download
│   ├── equation_workflows.py      # Equation Set editor + upload/download
│   ├── report_workflows.py        # Report editor + upload/download
│   ├── translation_workflows.py   # Translation Editor
│   ├── print_workflows.py         # Print/PDF workflows
│   ├── general_options.py         # General Options dialog
│   ├── totalizers.py              # Totalizers document type
│   ├── terminal_emulator.py       # Terminal emulator window
│   ├── help_content.py / help_viewer.py  # Help navigation
│   ├── installer_workflows.py     # Inno Setup installer/uninstaller automation
│   └── accuload_web.py            # Selenium bridge to the AccuLoad device's own web HMI
│
├── tests/                     # Pytest tests (test_*.py auto-collected; unit_test_*.py is not)
│   ├── conftest.py             # `page` fixture, COM STA autouse fixture, logging setup
│   ├── test_e2e.py             # smoke test: load file, wait for device, walk a tree/list
│   ├── test_regression_*.py    # scenarios/regression.md sections A-H, one file per letter
│   ├── test_device_connectivity.py
│   ├── test_scenario_runner.py / test_test_case_runner.py
│   └── unit_test_*.py          # run by explicit path only (don't match test_*.py)
│
├── scenarios/                  # Markdown test documents (manual + automatable)
│   ├── regression.md           # the master manual regression test document
│   ├── example_*.md            # scenario_runner.py usage examples
│   └── ALIV-*.md               # snap-in bugfix regression cases (see "Bugfix regression cases" below)
│
├── scenario_runner.py          # Standalone: run a plain-English Markdown scenario
├── test_case_runner.py         # Standalone: hybrid auto/manual runner for formal test docs
├── configs/                    # Saved AccuMate config files referenced by scenarios/tests
├── screenshots/                # Auto-captured screenshots (gitignored content, dir tracked)
├── conftest.py                 # Root fixtures: `app`, `device_ip`, `config_file`, `accuload_web`
└── pytest.ini                  # testpaths, python_files, markers, default addopts
```

---

# 🛠️ Requirements

## Python

- Python 3.10+ (this repo currently runs on 3.14; if automating a 32-bit
  build of AccuMate, using 32-bit Python avoids the `UserWarning: 32-bit
  application should be automated using 32-bit Python` noise, though 64-bit
  Python still works)

## Dependencies

```bash
pip install pywinauto pytest Pillow pythoncom pywin32
```

## Target application

Tests drive the real AccuMate binary — the path is hardcoded in
`app/application.py`'s `APP_EXE` constant. Update that constant (or pass
`AccuMateApp(exe_path=...)`) if your build lives elsewhere.

---

# ▶️ Running Tests

From the project root:

```bash
pytest -s -v
```

- `-s` is required in practice — it shows the extensive `[DEBUG]`/`[INFO]`/
  `[STEP]`/`[WARN]` print output used to diagnose UI automation failures
  when you can't watch the screen live.
- `pytest.ini`'s default `addopts` excludes three marker categories so a
  routine run never surprises you:
  - `disruptive` — mutates live device state (e.g. resets IP/netmask)
  - `needs_live_verification` — written from docs/inference, not yet
    confirmed against the real running app
  - `installs_software` — performs a real install/uninstall
- Run a single test:
  ```bash
  pytest -s -v tests/test_e2e.py::test_full_user_workflow
  ```
- Run a `requires_device`/`needs_live_verification`-marked test explicitly
  against a specific device (the marker override is needed because
  `needs_live_verification` is excluded by default `addopts`):
  ```bash
  pytest -s -v tests/test_regression_d.py::test_d6_uploading_driver_database_files \
      --accumate-device-ip=10.55.66.70 -m "requires_device" -o addopts=""
  ```
- Run everything, including disruptive/live-verification tests, for a full
  regression pass:
  ```bash
  pytest -s -v -m "" --accumate-config-file="C:\path\to\DefaultAL4.dat" --accumate-device-ip=10.55.66.70
  ```
- `unit_test_ribbon_controls.py` and `unit_test_uia_inspection.py` don't
  match `python_files = test_*.py`, so invoke them by explicit path:
  ```bash
  pytest -s -v tests/unit_test_ribbon_controls.py
  ```

---

# 🧩 Architecture: how a test is built up

```
AccuMateApp            (app/)         -- launches/attaches to the real .exe
   │
   ▼
controls/*.py                          -- low-level control lookup (list/tree/ribbon)
   │
   ▼
pages/MainPage                         -- page-object: tree/list interactions + auto-screenshot
   │
   ▼
workflows/*.py                         -- multi-step flows: open file, connect device,
   │                                       upload/download, edit a dialog, etc.
   ▼
tests/test_*.py                        -- pytest tests compose the above into scenarios
```

Every workflow function takes an `app_obj` (an `AccuMateApp` instance,
usually from the `app` pytest fixture) as its first argument and calls back
into `app_obj.get_window()` / `app_obj.get_uia_window()` as needed. This
keeps workflows composable and testable independent of pytest.

---

# 🔑 Core API you'll actually use

## `AccuMateApp` (`app/application.py`)

```python
from app.application import AccuMateApp

app = AccuMateApp()                 # launches AccuMate.exe
win = app.get_window()              # win32 wrapper of the main frame
uia_win = app.get_uia_window()      # UIA wrapper of the same window (for ribbon buttons)

app.is_device_connected()           # bool - checks ribbon button enablement, not the tree
app.wait_for_device_connection(timeout=10)  # polls is_device_connected(); never raises
```

`get_window()` and `get_uia_window()` both return **resolved wrappers**, not
`WindowSpecification` objects — so `.child_window(...)` is **not**
available on their result. Scan `.descendants()` and match manually
(`window_text()`, `control_id()`, `automation_id`, etc.) instead. This one
gotcha has caused most of this repo's early bugs — see `controls/*.py` for
the established pattern.

## Controls (`controls/common_controls.py`, `controls/ribbon_controls.py`)

```python
from controls.common_controls import get_list, get_tree, get_list_row_texts
from controls.ribbon_controls import click_ribbon_button, is_ribbon_button_enabled

lst = get_list(app)                       # polls for a SysListView32, raises TimeoutError if absent
tree = get_tree(app)                      # polls for a SysTreeView32
row = get_list_row_texts(lst, row_index)  # list of column strings for one row

uia_win = app.get_uia_window()
is_ribbon_button_enabled(uia_win, "Pull All From AccuLoad")
click_ribbon_button(uia_win, "Retry Comm")
```

## `MainPage` (`pages/main_page.py`)

The page-object wrapping tree/list interactions. Every public method is
decorated with `@auto_step`, which captures a numbered screenshot into
`screenshots/<test_name>/NN_<method>_<timestamp>.png` after each call — the
primary debugging aid when you can't watch a headless/CI run live.

```python
from pages.main_page import MainPage

page = MainPage(app)

page.select_tree_path(["System Directory", "Security Directory"])
row_index = page.select_list_item("Ethernet Host Security Level")
page.edit_value("Ethernet Host Security Level", "3")
current = page.get_value("Ethernet Host Security Level")
page.edit_dropdown_value("Security Level", "Security Level 2")

page.is_ribbon_enabled("Retry Comm")   # -> bool
page.click_ribbon("Retry Comm")
```

## File workflows (`workflows/file_workflows.py`)

```python
from workflows.file_workflows import (
    load_test_file, load_config_file, save_as, open_file_dialog,
    new_config_file, close_current_file,
)

load_test_file(app)                       # opens the repo's default test config (TEST_FILE)
load_config_file(app, r"C:\path\to.al4")  # opens an arbitrary saved config; closes any open doc first
save_as(app, str(tmp_path / "out.al4"))   # Application Button -> Save As... -> handles overwrite confirm
open_file_dialog(app, str(tmp_path / "out.al4"))  # Ctrl-O -> Open dialog -> set path -> Open
new_config_file(app)                      # Application Button -> New -> AccuMate Config File
close_current_file(app)                   # Application Button -> Close (handles "save changes?" -> No)
```

## Device connectivity (`workflows/comm_workflows.py`)

```python
from workflows.comm_workflows import configure_ip_and_connect

connected = configure_ip_and_connect(app, "10.55.66.70", timeout=15)
# opens Communications Settings, sets IP (+ optional arm_addresses), OKs the
# dialog, clicks ribbon "Retry Comm", then polls app.wait_for_device_connection().
# Returns True/False; never raises for a connection failure.
```

## Security / passcodes (`workflows/security_workflows.py`)

```python
from workflows.security_workflows import enter_passcode

enter_passcode(app, "1234")   # handles the passcode modal, including the
                               # "incorrect passcode" retry path
```

## File transfer to/from a live device (`workflows/file_transfer_workflows.py`)

The shared module behind every "Upload File to AccuLoad"/"Download File
From AccuLoad" ribbon action, reused by Report/Driver Database/Equation
Set/Translation/Log document types:

```python
from workflows.file_transfer_workflows import upload_file, download_file, DOWNLOAD_CATEGORY_IDS

result = upload_file(app, r"C:\path\to.al4ddb")
# {"message": str or None, "timed_out": bool} - `message` is whatever the
# generic "AccuMate" popup said (success, "no information to pull", or a
# real device-side "The operation timed out" - all surface through the
# same dialog, so callers must interpret `message` against what the
# specific test expects).

result = download_file(app, "Driver Database File", str(tmp_path / "out.al4ddb"))
# category must be a key of DOWNLOAD_CATEGORY_IDS:
#   Transaction Log, Event Log, Audit Trail Log, Equations File,
#   Report Files, Driver Database File, Translation File, License Status File
```

Document-type-specific wrappers exist in each editor's own workflow module,
e.g. `driver_db_workflows.upload_driver_database_file`/
`download_driver_database_file`, `equation_workflows.upload_equation_file`/
`download_equation_file`, `report_workflows.upload_report_file`/
`download_report_file` (the latter also resolves an extra "Select Report"
dialog via `_select_report_type`).

> **Known live-confirmed limitation:** every real transfer attempt against
> the test AccuLoad IV device (10.55.66.70) has ended in a device-side "The
> operation timed out" message after ~60-90s, despite a live control-channel
> connection (TCP 7734) throughout. The dialog automation itself is fully
> verified correct — this looks like a separate data-channel/firewall issue
> external to this repo. Tests that exercise real transfers check for this
> exact message and skip (not fail) when they see it.

> **RESOLVED (2026-08-05):** the "operation timed out" message above traced
> back to a corporate firewall/network policy that blocks real FTP file
> transfers specifically when AccuMate.exe is launched from this repo's raw
> `Release/` build output folder — not a device, network, or automation bug.
> Launching the *exact same binary* from its installed location
> (`app.application.APP_EXE_INSTALLED`, e.g.
> `C:\Users\<user>\AppData\Local\Guidant\AccuMate\1.12\AccuMate.exe`) instead
> completes real transfers successfully (confirmed live for D6/D7/B5), once
> the one-time Windows Firewall prompt for that path is accepted. Any test
> that performs a real upload/download should request the `app_ftp` fixture
> (see `conftest.py`) instead of the plain `app` fixture — everything else
> (document editing, non-transfer ribbon actions) should keep using `app`
> against the Release build as before.


---

# 🧪 Example: a full pytest test

```python
def test_full_user_workflow(app):
    from workflows.file_workflows import load_test_file
    from pages.main_page import MainPage

    load_test_file(app)
    page = MainPage(app)

    page.select_tree_path(["System Directory", "Security Directory"])
    row_index = page.select_list_item("Ethernet Host Security Level")

    assert row_index is not None
```

## Example: device connectivity + editing a value

```python
import pytest
from workflows.file_workflows import load_config_file
from workflows.comm_workflows import configure_ip_and_connect
from pages.main_page import MainPage


@pytest.mark.requires_device
def test_set_security_level(app, config_file, device_ip):
    if not config_file:
        pytest.skip("No saved AccuMate config file available")

    load_config_file(app, config_file)

    if not configure_ip_and_connect(app, device_ip, timeout=15):
        pytest.skip("AccuLoad device not reachable/connected")

    page = MainPage(app)
    page.select_tree_path(["System Directory", "Security Directory"])
    page.edit_value("Ethernet Host Security Level", "2")
    assert page.get_value("Ethernet Host Security Level") == "2"
```

## Example: uploading a file to a live device and handling the outcome

```python
import os
import pytest
from workflows.file_workflows import load_test_file, save_as
from workflows.comm_workflows import configure_ip_and_connect
from workflows.driver_db_workflows import (
    create_new_driver_database_file, upload_driver_database_file,
)

_DEVICE_TIMEOUT_MESSAGE = "The operation timed out"


@pytest.mark.requires_device
def test_upload_driver_database(app, device_ip, tmp_path):
    create_new_driver_database_file(app)

    upload_path = str(tmp_path / "upload.al4ddb")
    save_as(app, upload_path)
    assert os.path.isfile(upload_path)

    # "Document Options" only enables once a real AL4 config document is
    # loaded - a bare Driver Database document alone isn't enough.
    load_test_file(app)

    if not configure_ip_and_connect(app, device_ip, timeout=15):
        pytest.skip("AccuLoad device not reachable/connected")

    result = upload_driver_database_file(app, upload_path)
    if result["timed_out"] or _DEVICE_TIMEOUT_MESSAGE in (result["message"] or ""):
        pytest.skip(f"Device-side transfer timeout: {result!r}")

    assert result["message"] is not None
```

## Example: a ribbon-driven smoke check (no device needed)

```python
def test_ribbon_button_enabled_state(page):
    # `page` fixture (tests/conftest.py) wraps a fresh `app` in MainPage
    assert page.is_ribbon_enabled("Document Options") is False  # before a config loads
```

## Example: driving a plain-English scenario without writing a pytest test

For quick manual exploration/reproduction, skip pytest entirely and describe
the steps in Markdown:

```markdown
<!-- scenarios/my_scenario.md -->
# My scenario

- Connect to 10.55.66.70
- Verify that the device is connected
- Save as C:\temp\test2.al4
```

```bash
python scenario_runner.py scenarios/my_scenario.md
```

Recognized step phrasings live in `scenario_runner.py`'s `_STEP_PATTERNS`
registry (`@step(pattern)` decorator) — unrecognized steps are reported and
skipped rather than guessed at.

---

# 🗺️ Where to look when writing a new test

1. **Is there already a workflow for this document type/dialog?** Check
   `workflows/` first — most editors (Report, Driver Database, Equation
   Set, Translation, Totalizers, General Options) already have a
   `create_new_*`/`get_*_rows`/`insert_*`/`save_as` pattern you can copy.
2. **Does it involve a modal dialog (`class_name="#32770"`)?** Follow the
   dual-backend pattern: attach via win32 to wait for/find it, then
   re-attach via UIA on the same HWND for `child_window(auto_id=..., ...)`
   lookups (see `workflows/file_workflows.open_file_dialog` for the
   canonical example).
3. **Does it involve a ribbon button?** Use
   `controls.ribbon_controls.click_ribbon_button`/`is_ribbon_button_enabled`
   — ribbon buttons only exist via the UIA backend
   (`app.get_uia_window()`), never win32.
4. **Does it involve uploading/downloading a file to a live device?** Reuse
   `workflows/file_transfer_workflows.py`'s `upload_file`/`download_file`
   rather than re-deriving the dialog mechanics — see the "File transfer"
   section above.
5. **Add the test to `tests/test_regression_<letter>.py`** matching
   `scenarios/regression.md`'s section lettering, with a docstring citing
   the regression.md step numbers it covers. Mark it `@pytest.mark.requires_device`
   if it needs a live AccuLoad, and `@pytest.mark.needs_live_verification`
   until you've actually run it against the real app and confirmed the
   control ids/dialog titles/behavior.
6. **Run it** with `-s -v` and read the `[DEBUG]`/`[STEP]` output plus the
   auto-captured screenshots in `screenshots/<test_name>/` if anything looks
   wrong.

---

# 📸 Screenshots

Screenshots are captured automatically:
- After every `MainPage` interaction (`@auto_step`), into
  `screenshots/<test_name>/NN_<method>_<timestamp>.png`.
- Once more just before teardown (root `conftest.py`'s `app` fixture), into
  `screenshots/<test_name>_<timestamp>.png`.

Screenshot/teardown failures are swallowed (logged as `[WARN]`) so they
never mask the real test failure, and the app process is always
force-killed (`taskkill /PID <pid> /F /T`) to avoid orphaned processes
between runs.

---

# 🐛 Bugfix regression cases (ALIV-*.md)

Any `scenarios/ALIV-<ticket-number>.md` file (same wiki-markup format as
`ALIV-3929.md`, run via `test_case_runner.py`) is a **one-off bugfix
regression case** - written once, when a specific bug is fixed and
verified, then available to snap back in and re-run at any time without
being folded into the curated `regression.md` A-H sections. No
registration step is needed: drop a new `ALIV-<number>.md` file into
`scenarios/` and it's auto-discovered by filename.

```bash
# List every bugfix scenario currently checked into scenarios/
python test_case_runner.py --list-bugfixes

# Run a single bugfix case by ticket ID (resolves to scenarios/ALIV-4085.md)
python test_case_runner.py --bugfix ALIV-4085

# Run every ALIV-*.md bugfix scenario back-to-back
python test_case_runner.py --all-bugfixes

# ...writing each one's report to a dedicated directory instead of next to the input file
python test_case_runner.py --all-bugfixes --report-dir scenarios/reports
```

Each file still runs through the same hybrid auto/manual step engine as
any other `test_case_runner.py` document (see below) - fully-automatable
steps run unattended, everything else pauses for a human verdict - and a
Markdown report is written out per file.

---

# 👍 Summary

✅ Clean, layered architecture (App → Controls → Pages → Workflows → Tests)
✅ Stable dual-backend (win32 + UIA) Win32/MFC automation
✅ Reusable workflows for every major document type and the device
   connectivity / file-transfer flows they all share
✅ Scalable pytest setup with markers for device/disruptive/unverified tests
✅ Two plain-English runners (`scenario_runner.py`, `test_case_runner.py`)
   for fast manual-test-to-automation conversion
✅ Debug-friendly: verbose step logging + auto-screenshots everywhere

---

Happy automating 🚀
