"""
Manual diagnostic script for probing the compiled AccuMate Inno Setup
installer's wizard pages (scenarios/regression.md G1-G5). NOT collected by
default pytest runs (see pytest.ini's python_files = test_*.py - this file
intentionally doesn't match) - run explicitly by path:

    pytest -s -v tests/unit_test_installer_probe.py

Navigates Welcome -> License (accepts) -> Select Components -> Select
Destination -> Ready to Install, printing each page's full control tree, then
stops and cancels out WITHOUT actually installing anything - this is a
read-only probe for discovering/re-confirming real control ids/class names
whenever the installer script or Inno Setup version changes, following the
same pattern as unit_test_ribbon_controls.py/unit_test_uia_inspection.py for
the main AccuMate app.

Does not use the `app` fixture (that launches AccuMate.exe itself) - this is
a genuinely separate process, launched directly via
workflows.installer_workflows.launch_installer().
"""
from workflows.installer_workflows import (
    accept_license,
    click_cancel,
    click_next,
    get_ready_to_install_summary,
    is_license_page,
    is_ready_to_install_page,
    launch_installer,
)


def _dump(win_spec, label):
    print(f"\n===== {label} =====")
    try:
        win_spec.print_control_identifiers()
    except Exception as e:
        print(f"[ERROR] print_control_identifiers failed: {e}")


def test_probe_installer_wizard_pages():
    win_spec = launch_installer()
    _dump(win_spec, "Page 1 (Welcome)")

    assert click_next(win_spec), "Next should be enabled on the Welcome page"
    _dump(win_spec, "Page 2 (License)")
    assert is_license_page(win_spec), "expected the License Agreement page next"
    accept_license(win_spec)

    assert click_next(win_spec), "Next should be enabled after accepting the license"
    _dump(win_spec, "Page 3 (Select Components)")

    assert click_next(win_spec), "Next should be enabled on Select Components"
    _dump(win_spec, "Page 4 (Select Destination)")

    assert click_next(win_spec), "Next should be enabled on Select Destination"
    _dump(win_spec, "Page 5 (expected Ready to Install)")
    assert is_ready_to_install_page(win_spec), "expected the Ready to Install page next"
    print(f"\n[INFO] Ready to Install summary:\n{get_ready_to_install_summary(win_spec)}")

    print("\n[INFO] Stopping before the real install step. Cancelling wizard...")
    click_cancel(win_spec)
