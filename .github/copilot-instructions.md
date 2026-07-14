# pywin_auto_gui — Copilot Instructions

UI automation test framework for a specific Win32/MFC desktop app ("AccuMate for AccuLoad")
using `pywinauto` + `pytest`. Tests drive the real application binary — there is no mocking
layer, so tests require the target app to be installed at the path in `app/application.py`.

## Running tests

```bash
pytest -s -v
```

- `pytest.ini` sets `testpaths = tests` and `python_files = test_*.py` — only files matching
  `test_*.py` under `tests/` are collected by default. `tests/unit_test_ribbon_controls.py` and
  `tests/unit_test_uia_inspection.py` do **not** match this pattern (see dedicated section below)
  and must be run by explicit path.
- Run a single test: `pytest -s -v tests/test_e2e.py::test_full_user_workflow`
- `-s` is required in practice to see the extensive `[DEBUG]`/`[INFO]`/`[STEP]` print output used
  for diagnosing UI automation failures.
- `tests/test_e2e.py::test_full_user_workflow` launches the app and loads the test file, then calls
  `AccuMateApp.wait_for_device_connection()` to check for a real live connection (see
  `is_device_connected()` below — **not** tree/list presence). If not connected within
  `DEVICE_CONNECT_TIMEOUT` (10s), the test calls `pytest.skip()` automatically instead of failing.
  No manual configuration/env var is needed by default. Pass `--accumate-config-file` explicitly to
  additionally have it load a saved config and configure+connect to `--accumate-device-ip` first
  (see below) before running the workflow steps.
- `tests/test_device_connectivity.py::test_device_connectivity` is a dedicated, marked
  (`@pytest.mark.requires_device`) connectivity check: it loads a saved AccuMate config file,
  configures the device IP via `workflows/comm_workflows.configure_ip_and_connect` (opens the
  Communications Settings dialog, sets the IP, clicks "Retry Comm"), and asserts a live connection
  is established:
  ```bash
  pytest -s -v tests/test_device_connectivity.py --accumate-config-file="C:\path\to\DefaultAL4.dat" --accumate-device-ip=10.55.66.70
  ```
  Both options have working defaults (`conftest.py`'s `config_file`/`device_ip` fixtures fall back
  to the app's own `DefaultAL4.dat` and a known test device `10.55.66.70`, respectively), so running
  it with no flags still attempts a real connection whenever that default config file exists on
  disk. Skips (rather than fails) if no config file is available at all, or if the device doesn't
  come online within the timeout.
  - Filter these out of a run with `pytest -m "not requires_device"` if no device is available.

### Ribbon controls, UIA inspection, and debug_tools

- Ribbon smoke test: `pytest -s -v tests/unit_test_ribbon_controls.py`
  - Run a single parametrized case: `pytest -s -v "tests/unit_test_ribbon_controls.py::test_click_ribbon_button[Retry Comm]"`
  - Uses the `page` fixture defined in `tests/conftest.py` (a `MainPage` instance), which exposes
    `is_ribbon_enabled(name)`/`click_ribbon(name)` — these dispatch to `AccuMateApp.get_uia_window()`
    + `controls/ribbon_controls.py` helpers, since ribbon buttons aren't real win32 controls and
    require the UIA backend.
- UIA inspection test (exercises `controls/debug_tools.safe_dump_control`, which wraps
  `controls/uia_sta.run_in_sta` to describe a control from a dedicated STA thread):
  `pytest -s -v tests/unit_test_uia_inspection.py`
- Both of these are excluded from the default `pytest -s -v` run because they don't match
  `python_files = test_*.py` in `pytest.ini` — invoke them by explicit path as shown above.

No linter or build step is configured for this project.

## Architecture (App → Controls → Pages → Workflows → Tests)

- **`app/application.py`** — `AccuMateApp` launches/attaches to the real `.exe` (path is the
  hardcoded `APP_EXE` constant) and exposes `get_window()` (win32 backend; matches via
  `title_re=".*AccuMate for AccuLoad\s*$"` **and** `class_name_re="^Afx:"` — a plain exact
  `title=APP_TITLE` match breaks once any file loads, since the title becomes
  `"<filename> - AccuMate for AccuLoad"`, and a naive `title_re`-only match is ambiguous because the
  ribbon's `AFX_SUPERBAR_TAB:...` owned window shares the same title text; the main frame's class
  always starts with `"Afx:"`, which disambiguates it), `get_uia_window()` (attaches to the same
  HWND via the UIA backend, cached on `self._uia_app`, needed for ribbon/dialog controls not
  exposed natively), `is_device_connected()` (checks whether the ribbon's "Pull All From AccuLoad"
  button is enabled — see device connectivity below) and `wait_for_device_connection(timeout)`
  (polls `is_device_connected()`; never raises, returns `True`/`False`). Almost everything else
  takes an `app_obj`/`app` argument and calls back into this.
- **`controls/common_controls.py`** — low-level, backend-agnostic helpers for polling for a
  control by class name (`wait_for_control`), and fetching `SysListView32`/`SysTreeView32`
  wrappers and row text. Poll-with-timeout (not hard sleeps) is the pattern for control lookup.
  Uses `.descendants(class_name=...)` rather than `.child_window()` (see the wrapper vs.
  `WindowSpecification` note below).
- **`pages/main_page.py`** — `MainPage` is a page-object wrapping tree/list interactions
  (`select_tree_path`, `select_list_item`, `edit_value`, `edit_dropdown_value`, `get_value`,
  `is_ribbon_enabled`, `click_ribbon`). Every public interaction method is decorated with
  `@auto_step`, which auto-captures a numbered screenshot into
  `screenshots/<test_name>/NN_<method>_<timestamp>.png` after each step — this is the primary
  debugging aid when a headless/CI run fails, since you can't watch the UI live.
- **`workflows/`** — higher-level, multi-step flows composed from `app`/`controls` (e.g.
  `file_workflows.load_test_file`/`load_config_file` drive the native Open-file dialog to load
  either the default `TEST_FILE` or an arbitrary saved config path; `security_workflows.
  enter_passcode` handles the passcode modal including an "incorrect passcode" retry path;
  `comm_workflows.configure_ip_and_connect` drives the device-connectivity flow — see below).
  Workflows are plain functions taking `app_obj`, not classes.
- **`tests/`** — pytest tests compose `app` fixture + `workflows` + `MainPage` into end-to-end
  scenarios. Tests print a `[STEP]` line before each logical action for traceability. The root
  `conftest.py` also registers the `--accumate-config-file`/`--accumate-device-ip` CLI options and
  `config_file`/`device_ip` fixtures used to point tests at a real, previously-saved AccuMate config
  and device IP for device-connectivity testing, plus the `requires_device` marker.

## Device connectivity (real AccuLoad hardware)

- **Tree/list presence is NOT a valid "connected" signal.** `SysTreeView32`/`SysListView32` populate
  as soon as a config *file* loads/parses — completely independent of whether AccuMate has a live
  device connection. An earlier version of `wait_for_device_connection()` used tree presence and
  was a false heuristic (confirmed by a populated tree next to a status bar reading
  "Offline"/"Comm Not Enabled").
- **The status bar's "ONLINE"/"Offline" text is not exposed to automation at all** — it's rendered
  in a custom, owner-drawn region with no matching control/text found via either the win32 or UIA
  backend descendant scans.
- **The reliable, UIA-readable proxy is ribbon button enablement**: "Pull All From AccuLoad" /
  "Push All to AccuLoad" / "Go Offline" are enabled only while genuinely online, and disabled while
  offline (confirmed by toggling "Go Offline"/"Retry Comm" against the visible status bar).
  `AccuMateApp.is_device_connected()` checks this via `controls/ribbon_controls.
  is_ribbon_button_enabled(uia_win, "Pull All From AccuLoad")`.
- **Configuring and connecting to a device**: `workflows/comm_workflows.configure_ip_and_connect
  (app_obj, ip_address, timeout)` opens the "AccuMate Communications Settings" dialog (ribbon
  "Document Options" button, `class_name="#32770"`), sets the `SysIPAddress32` control (`control_id
  1028`) via `click_input()` + `type_keys()` (setting it via `ctypes.SendMessage(IPM_SETADDRESS)`
  is unreliable — readback via `IPM_GETADDRESS` returns `0.0.0.0` across the 32-bit/64-bit process
  boundary even when the set actually succeeded; verify via `.window_text()` instead), clicks OK
  (`control_id 1`), clicks ribbon "Retry Comm", then polls `wait_for_device_connection()`.
  `open_communications_settings()` retries the ribbon click a couple of times since the app can
  still be settling (e.g. finishing its own initial connection attempt) right after a config file
  loads, and the first click can be missed.

## Save As workflow (ribbon Application Button)

- **There is no dedicated "Save As" ribbon button or accelerator** — `F12`, `Ctrl+Shift+S`, and the
  classic `Alt+F` menu key all do nothing (this ribbon skin has no menu bar). The only path to
  "Save As..." is the round **Application Button** in the ribbon's top-left corner.
- **The Application Button is a UIA `Button` with empty `window_text()`**, distinguishable only by
  size (~56×56px, larger than any other control in that region). `controls/ribbon_controls.
  find_app_button(uia_win)` locates it by scanning descendants for an empty-text `Button` >40×40px.
- **Its backstage popup menu is entirely non-UIA-accessible** — clicking it spawns two `Afx:...:800:...`
  popup HWNDs that both return **zero descendants** when scanned via UIA (stronger version of the
  status-bar's "custom-drawn, non-automatable" pattern). Keyboard navigation (`{DOWN}`) doesn't work
  either — it silently closes the menu. The only way to select a menu item is a **coordinate click**,
  computed window-relative to the Application Button's own rectangle so it survives window moves (but
  not window resizes/DPI changes):
  ```
  x = (app_button_rect.left - window_rect.left) + 85
  y = (app_button_rect.bottom - window_rect.top) + 27 + item_index * 52
  ```
  Item order (0-based): New=0, Open...=1, Save=2, **Save As...=3**, Firmware Update...=4, Print=5,
  Close=6, About=7.
- **`workflows/file_workflows._click_app_menu_item`/`_open_save_as_dialog` retry (default 3
  attempts)**: the popup's render/animation timing is flaky enough that the very first click after
  opening the menu frequently misses in practice — every observed failure recovered on retry 2. Each
  retry presses `{ESC}` first to dismiss any stuck/mis-clicked menu before reopening.
- **Overwrite confirmation is a gotcha**: saving to an existing path can pop up to two sequential
  confirmation dialogs. The OS-level common-dialog "Confirm Save As" prompt's Yes button is titled
  `&Yes` (with an ampersand accelerator) — match it by **`control_id() == 6`** (`IDYES`), not by exact
  title text. An earlier version matched by `title="Yes"` inside a broad `except Exception: pass`,
  which failed **silently** (the file already existed from a prior save, so `os.path.isfile()` still
  passed) and left a stuck modal dialog blocking teardown. Don't swallow exceptions broadly around
  confirmation-dialog handling; `save_as()` raises `RuntimeError` loudly instead if no Yes button is
  found. `tests/unit_test_save_as.py` also independently asserts no stray Save/Confirm dialog remains
  open after a save, since the file-exists check alone doesn't catch this bug class.
- `workflows/file_workflows.save_as(app_obj, save_path)` ties this together: validates the target
  directory exists, opens Save As via the Application Button menu, sets the filename field
  (`automation_id="1001"`) and clicks Save (`automation_id="1"`) using the same dual-backend
  win32+UIA dialog pattern as `open_file_dialog`, then handles the overwrite-confirmation loop.

### Config reload fix (Close current document before re-opening)

- **Bug**: AccuMate always has *some* document open (`DefaultAL4.dat` auto-loads on startup). Doing
  a plain Ctrl-O to open a *different* config file while one is already open can silently pop an
  extra "save changes?" confirmation first — which `open_file_dialog`'s wait for the `#32770` Open
  dialog doesn't expect, so it just times out. This showed up live running `scenarios/ALIV-3929.md`:
  the first "Load test configuration file" step (right after app start) succeeded, but the second
  occurrence of the identical step later in the same document (re-loading the same file into an
  already-open document) timed out.
- **Fix**: `workflows/file_workflows.load_config_file(app_obj, config_path, close_existing=True)` now
  closes the current document first via `close_current_file(app_obj)` — Application Button ->
  **Close** (`item_index=6`, NOT the same as closing the whole app) — before opening the requested
  file, so the reload always happens against a clean "nothing open" state in the same app instance.
  `close_current_file` also handles the optional "save changes?" confirmation dialog that Close can
  trigger, answering **No** (`control_id() == 7`, `IDNO`) — an automated test run should never
  silently persist in-app edits back over a saved config file. Pass `close_existing=False` to skip
  this (e.g. a caller that already knows nothing is open).
- Verified live: both "Load test configuration file 'ALIV-3929.AL4'" steps in `ALIV-3929.md` now
  `AUTO/PASS` (previously the second one timed out); 0 failures across all 41 steps.

## Hybrid test-case runner (formal wiki-markup test documents)

- **`test_case_runner.py`** handles a *different, messier* input format than `scenario_runner.py`:
  real Jira/Confluence-exported manual test case documents (see `scenarios/ALIV-3929.md`) written in
  Confluence wiki markup (`h3.`/`h4.` headers, `_italic_`/`*bold*`), with compound multi-action numbered
  steps, an `Expected Result: ..._` line, and a trailing `*[PASS/FAIL]*` marker meant for a *human*
  tester to fill in — nothing like the purpose-built scenario Markdown format above.
  ```bash
  python test_case_runner.py scenarios/ALIV-3929.md --report scenarios/ALIV-3929-report.md
  ```
- **`parse_test_case_document(path)`** extracts `TestSection`/`TestStep` objects only from content under
  `"h4."` headers — everything before the first `h4.` (the `h3.` title, notes, a settings-value list)
  is preamble/context, not steps, and is intentionally skipped.
- **Deliberately a *hybrid*, not a full auto-executor**: most real test-case steps bundle several UI
  actions with a state verification that fundamentally requires a human to read the screen anyway, so
  clause-splitting a compound sentence for partial automation was evaluated and rejected as adding
  fragility without saving real effort. Instead, **each whole step's text** is checked against a small
  curated set of fully-automatable phrasings (`_TESTCASE_STEP_PATTERNS`, e.g. `"Start the Accumate
  Application"`, `"Load test configuration file '<name>' file"`) plus `scenario_runner`'s general step
  grammar; anything else pauses and prompts the human to perform/verify it and record a `pass`/`fail`/
  `skip` verdict (`_prompt_manual_verdict`).
- **Only an explicit allowlist of `scenario_runner` patterns is reused for whole-step matching**
  (`_SAFE_STEP_HANDLERS`) — several of its patterns use an open-ended, non-greedy-but-end-anchored
  capture (e.g. `"click <name>"`, `"set/change X to Y"`) that's fine for a clean, purpose-written
  scenario line but unsafe against messy compound prose. Real testing against `ALIV-3929.md` caught
  **two** separate false positives this way: `"Click on the 'Open' button in the top left corner of the
  application."` got its filler words captured as a literal (bogus) button name, and `"Change Security
  Directory -> Ethernet Host Security Level to 'No Security'.  Confirm the AccuLoad updated the
  parameter.  Go offline..."` had its entire trailing sentence swallowed as the "value" by the
  `set/change ... to ...` pattern — both attempted (and failed) a wrong auto-action instead of correctly
  falling back to a manual step. Rather than denylist each newly-discovered unsafe pattern, the fix
  flipped to an allowlist of only genuinely bounded patterns (fixed literal phrases, or capture groups
  constrained to an IPv4 address / single token / bare number that can't absorb an unrelated clause).
- **Passcodes are always manual, on purpose** — real per-site security passcodes referenced abstractly
  in these documents ("the passcode for security level 3") have no business living in a Markdown file
  or this repo, so passcode-entry steps always pause rather than sourcing a value automatically.
- **Bare config filenames resolve against the repo's `configs/` directory first** (`_resolve_config_path`)
  — e.g. `"Load test configuration file 'ALIV-3929.AL4' file"` resolves to `configs/ALIV-3929.AL4`, which
  is where saved AccuMate config files referenced by formal test-case documents are expected to live,
  falling back to the scenario Markdown file's own directory for backward compatibility. A filename that
  already includes a directory is used as-is.
- Results are collected per step (`AUTO`/`MANUAL`, verdict, notes) and written to a Markdown report
  (default `<input-name>-report.md` next to the input file, or `--report <path>`).
- **Automated post-execution verification (no human input) for the steps we ourselves execute**: an
  `AUTO` step's verdict used to just mean "the handler didn't raise an exception" - which confirms the
  *action* ran, but not that AccuMate actually reached the state the step's Expected Result claims.
  Where a matched handler's outcome can be checked safely and unambiguously via existing `app`/`page`
  primitives, a **verifier** function (`_STEP_VERIFIERS`/`_SR_STEP_VERIFIERS`, keyed by handler) is
  attached to it and re-checks real app state after the handler returns, turning *that* into the
  recorded `PASS`/`FAIL` instead of assuming success:
  - "Load test configuration file ..." -> polls the main window's title bar (up to 25s) for the
    loaded file's base name (`_verify_window_title_contains`/`_verify_config_file_loaded`). Live
    testing showed this needs a real poll, not an immediate check: AccuMate spends ~10-13s attempting
    a device connection using the newly-loaded config's comm settings *before* it finishes loading the
    document and updates the title - checking too early or with too short a timeout reads the
    *previous* title and reports a false failure (caught and fixed during this work).
  - `scenario_runner`'s `"connect to <ip>"` (in the safe-handler allowlist) -> re-checks
    `AccuMateApp.is_device_connected()` independently of `configure_ip_and_connect`'s own internal
    check.
  - Steps with **no verifier registered** (e.g. `"Start the Accumate Application"` - "opens to a blank
    view" has no automated way to confirm beyond the window merely existing) keep the previous
    "ran without raising -> PASS" behavior; this is a deliberate, documented gap, not a silent one.
  - Steps with **no matching action handler at all** are never auto-verified — we only verify the
    aftermath of something we ourselves executed, never a claim about a step nobody automated (e.g. a
    step describing a manual UI click isn't auto-verified just because its Expected Result happens to
    mention checkable state - the action that would produce that state never actually ran).
- `tests/test_test_case_runner.py` parses the real `scenarios/ALIV-3929.md` fixture directly (no live
  app) to validate section/step/expected-result extraction and whole-step pattern matching, including a
  regression test for the click-catch-all false positive above, plus tests asserting which handlers do
  and don't carry a verifier.

## Markdown scenario runner (plain-English test scripts)

- **`scenario_runner.py`** (repo root) is a standalone script — *not* a pytest test — that reads a
  plain-English Markdown file and executes it step-by-step against a real running AccuMate instance,
  reusing the same `workflows/`/`pages.MainPage` functions the pytest suite is built on:
  ```bash
  python scenario_runner.py scenarios/example_connect_and_save.md
  ```
- **Markdown format**: only bullet (`- `/`* `) or numbered (`1. `) list items are treated as steps, in
  file order; headers, blank lines, fenced code blocks, and plain paragraph text are narration and are
  ignored (see `parse_scenario_markdown`) — this was corrected after a real test run showed prose
  narration lines being misread as unrecognized steps and failing the scenario.
- **Step recognition is a small, literal regex-to-handler registry** (`_STEP_PATTERNS` in
  `scenario_runner.py`, registered via the `@step(pattern)` decorator), not a general NLP parser —
  e.g. `"Connect to 10.55.66.70"` → `configure_ip_and_connect`, `"Save as <path>"` → `save_as`,
  `"Verify that the device is connected"` → asserts `wait_for_device_connection()`. Unrecognized
  steps are reported and skipped (not guessed at), so a typo fails loudly rather than silently doing
  the wrong thing. A broad `"click ... [button]"` pattern is registered last as a catch-all for any
  named ribbon button not covered by a more specific pattern.
- **Runner does its own app lifecycle**: launches `AccuMateApp()`, runs steps in order (stopping at
  the first real failure — later steps likely depend on it), then always takes a teardown screenshot
  and force-kills the process, mirroring the pattern in the root `conftest.py`'s `app` fixture.
- **Example scenarios** live in `scenarios/` (e.g. `example_connect_and_save.md`,
  `example_load_test_file.md`) as both usage samples and manual smoke-test scripts.
- **`tests/test_scenario_runner.py`** covers the parsing/regex-matching logic in isolation (no real
  app launched, so it's collected by default) — covers Markdown extraction edge cases (headers, code
  fences, bullet styles) and verifies each recognized step phrasing maps to the correct handler.

## Key conventions

- **Dual-backend dialog handling**: modal dialogs (`class_name="#32770"`) are attached via the
  `win32` backend for waiting/finding, then re-attached via the `uia` backend (using the same
  HWND) when UIA-only features are needed (e.g. `set_edit_text` on an Edit control in the Open
  file dialog). See `workflows/file_workflows.open_file_dialog` for the pattern.
- **UIA element lookups must use `automation_id`, not `title`/`control_type` alone**: modern
  Explorer-style common dialogs expose many controls with the same generic title/type (e.g. the
  Open dialog has 14 `Edit`-type elements — list view columns, search box, etc. — and 3
  `Button`-type elements titled "Open"). `child_window(title=..., control_type=...)` alone raises
  `ElementAmbiguousError` in these cases. Prefer stable `automation_id`s discovered by probing the
  real dialog (e.g. `"1148"` for the filename edit box, `"1"`/`"2"` for the standard
  `IDOK`/`IDCANCEL` Open/Cancel buttons) — see `workflows/file_workflows.open_file_dialog`.
- **`child_window()` only exists on `WindowSpecification`, not on a resolved wrapper**
  (`.wrapper_object()`'s return value). `AccuMateApp.get_window()`/`get_uia_window()` both return
  resolved wrappers, so any code calling `.child_window()` on their result raises
  `AttributeError`. This was the root cause of multiple real bugs this session
  (`ribbon_controls.find_ribbon_button`, `common_controls.wait_for_control`,
  `comm_workflows._find_by_control_id`) — the fix is to scan `.descendants()` (optionally filtered
  by `class_name=...`) and match manually (by `window_text()`/`control_id()`/etc.) instead.
- **COM STA requirement**: `tests/conftest.py` has an autouse fixture that calls
  `pythoncom.CoInitialize()`/`CoUninitialize()` around every test — required because pywinauto's
  UIA backend needs an STA-threaded apartment. Don't remove this without understanding the
  `0x80040155`/`0x8001010D` COM errors it prevents.
- **List/tree interaction is coordinate + keyboard driven**: editing a `SysListView32` cell (e.g.
  `MainPage.edit_value`/`edit_dropdown_value`) works by selecting the row, clicking an
  approximate pixel offset for the target column (`VALUE_COLUMN_X_OFFSET`), then driving edit
  mode via `send_keys` (`{F2}`, `^a`, `{ENTER}`, `{DOWN}`/`{UP}`). There's no reliable
  accessibility API for these controls, so changes to column layout will require adjusting the
  hardcoded offsets.
- **Teardown always screenshots then force-kills**: both the root `conftest.py` fixture and
  `MainPage._auto_screenshot` swallow screenshot/teardown exceptions (`try/except` + `[WARN]`
  print) so a failure capturing a screenshot never masks the real test failure; the app process
  is killed via `taskkill /PID <pid> /F /T` to avoid orphaned processes between runs.
- Debug/status output uses consistent bracketed tags (`[DEBUG]`, `[INFO]`, `[STEP]`, `[WARN]`,
  `[ERROR]`) via `print()` rather than a logging framework (except pywinauto's own logger, which
  `tests/conftest.py` silences to `ERROR` level).
