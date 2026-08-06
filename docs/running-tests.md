# Running Tests: Markers, Fixtures, and CLI Cheat Sheet

Quick reference for the pytest setup. For the underlying architecture,
see [`architecture.md`](architecture.md). For coverage status by scenario
ID, see [`regression-coverage.md`](regression-coverage.md).

## Basic invocation

```bash
pytest -s -v
```

`-s` is required in practice — it surfaces the `[DEBUG]`/`[INFO]`/`[STEP]`/
`[WARN]` print output this repo relies on for diagnosing UI automation
failures you can't watch live.

## Markers (defined in `pytest.ini`)

| Marker | Meaning | In default `addopts`? |
|---|---|---|
| `requires_device` | Needs a live, reachable AccuLoad device connection | included (not excluded — informational) |
| `requires_device_web` | Drives the AccuLoad's own embedded web HMI via Selenium (`workflows/accuload_web.py`) | included |
| `disruptive` | Mutates persistent live-device state in a way that can break a later test in the same run (e.g. A19's PUSH resets IP/netmask/gateway) | **excluded** |
| `needs_live_verification` | Written from docs/inference, not yet confirmed against the real running app | **excluded** |
| `installs_software` | Performs a real install/uninstall via the Inno Setup installer | **excluded** |
| `manual` | Cannot be automated from this repo at all; must be performed by a human tester | **excluded** |
| `special_case` | Automatable in principle, but only applies to a hand-arranged device state this repo can't safely arrange/verify | **excluded** |

Default `addopts`:
```ini
addopts = -v -m "not disruptive and not needs_live_verification and not installs_software and not manual and not special_case"
```

So a routine `pytest -s -v` run **never**: mutates persistent device
state, runs a half-verified flow, installs/uninstalls software, or wastes
time on a test that's guaranteed to just print "MANUAL TEST" / "SPECIAL
CASE" and skip.

## Running excluded categories explicitly

Override the marker filter with `-m` (and `-o addopts=""` if you need to
fully clear the file's default, e.g. to combine with device flags):

```bash
# Run one requires_device test, overriding the file's default marker filter
pytest -s -v tests/test_regression_d.py::test_d6_uploading_driver_database_files \
    --accumate-device-ip=10.55.66.70 -m "requires_device" -o addopts=""

# Full regression pass, including disruptive/live-verification/etc.
pytest -s -v -m "" --accumate-config-file="C:\path\to\DefaultAL4.dat" --accumate-device-ip=10.55.66.70

# List what's currently manual/special_case without running anything
pytest --collect-only -q -m "manual"
pytest --collect-only -q -m "special_case"

# Run only installer tests
pytest -s -v -m "installs_software"
```

## Key CLI options (registered in root `conftest.py`)

| Option | Used by | Fallback if omitted |
|---|---|---|
| `--accumate-config-file` | Tests needing a real saved AccuMate config (`config_file` fixture) | AccuMate's own `DefaultAL4.dat`, if present |
| `--accumate-device-ip` | Tests needing a live device (`device_ip` fixture) | A known test device IP baked into `conftest.py` |

## Key fixtures

| Fixture | Provides |
|---|---|
| `app` | A fresh `AccuMateApp` instance; launches the real `.exe`, force-kills + screenshots on teardown |
| `app_ftp` | Same as `app`, but launched from the **installed** AccuMate path (see "Two AccuMate.exe builds" below) — required for any FTP/file-transfer test |
| `page` | `MainPage(app)` — the tree/list page-object wrapping the `app` fixture |
| `config_file` | Resolves `--accumate-config-file` or a sensible default; tests should `pytest.skip()` if unavailable |
| `device_ip` | Resolves `--accumate-device-ip` or a sensible default |
| `device_arm_addresses` | Arm address list paired with `device_ip`, used by device-connectivity tests |

## Two `AccuMate.exe` builds — which to use when

This project has hit a real corporate-firewall difference between two
valid AccuMate builds:

- **`...\Release\AccuMate.exe`** (built from source) — FTP file transfers
  to/from a live device **time out** here (blocked by policy).
- **The installed build** (`...\AppData\Local\Guidant\AccuMate\<version>`)
  — FTP transfers **work**, after allowing it through Windows Firewall
  once.

**Rule:** use the installed build (`app_ftp` fixture) for anything
uploading/downloading a file to/from a live device (Reports, Driver
Database, Equation Sets, Translations, Logs, License Status). Use the
`Release/` build (`app` fixture) for everything else. If you add a new
FTP-touching test, make sure it takes `app_ftp`, not `app`.

## Running the non-`test_*.py` files

`unit_test_ribbon_controls.py` and `unit_test_uia_inspection.py`
deliberately don't match `pytest.ini`'s `python_files = test_*.py`, so
they're excluded from a bare `pytest -s -v` and must be invoked by
explicit path:

```bash
pytest -s -v tests/unit_test_ribbon_controls.py
pytest -s -v "tests/unit_test_ribbon_controls.py::test_click_ribbon_button[Retry Comm]"
pytest -s -v tests/unit_test_uia_inspection.py
```

## Non-pytest runners

```bash
# Plain-English scenario, no pytest test needed
python scenario_runner.py scenarios/example_connect_and_save.md

# Hybrid auto/manual runner for formal Assembla-style test docs
python test_case_runner.py scenarios/ALIV-3929.md --report scenarios/ALIV-3929-report.md
python test_case_runner.py --list-bugfixes
python test_case_runner.py --bugfix ALIV-4085
python test_case_runner.py --all-bugfixes --report-dir scenarios/reports
```

See also: [`architecture.md`](architecture.md),
[`adding-a-workflow.md`](adding-a-workflow.md),
[`adding-a-test.md`](adding-a-test.md),
[`regression-coverage.md`](regression-coverage.md).
