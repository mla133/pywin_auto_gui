"""
Automated coverage for scenarios/regression.md sections A24 (General Options
- Display Security Level) and A27 (Document Options - Default IP) - both
fully automatable using only the AccuMate app itself, no live AccuLoad
device connection and no other application required.
"""

from controls.common_controls import get_list
from workflows.comm_workflows import open_communications_settings, get_configured_ip, close_communications_settings
from workflows.file_workflows import new_config_file
from workflows.general_options import (
    open_general_options,
    close_general_options,
    set_checkbox,
    CHECKBOX_DISPLAY_SECURITY_LEVEL,
)

EXPECTED_DEFAULT_IP = "192.168.0.1"
# SysListView32 columns aren't individually exposed via UIA/win32 child
# controls (no HeaderItem descendants), so column presence is verified by
# column_count() instead of reading header text. By default the list has 5
# columns (ID, Description, Value, Comments, Security Level) - toggling
# "Display security level in parameter list view" off/on adds/removes the
# last one.
EXPECTED_COLUMN_COUNT_WITH_SECURITY_LEVEL = 5
EXPECTED_COLUMN_COUNT_WITHOUT_SECURITY_LEVEL = 4


def test_a27_document_options_default_ip(app):
    """
    regression.md A27: Document Options - Default IP.
      1. Navigate to "Document Options".
      2. Verify the "IP Address" value defaults to "192.168.0.1".
    """
    print("[STEP] Creating a new AccuMate Config File")
    new_config_file(app)

    print("[STEP] Opening Communications Settings (Document Options)")
    dlg = open_communications_settings(app)

    actual_ip = get_configured_ip(dlg)
    close_communications_settings(dlg, accept=False)

    assert actual_ip == EXPECTED_DEFAULT_IP, f"Expected default IP {EXPECTED_DEFAULT_IP}, got {actual_ip}"


def test_a24_general_options_display_security_level(app, page):
    """
    regression.md A24: General Options - Display Security Level.
      1. Note the Security Level column in the Config File. Open General
         Options.
      2. Disable "Display security level in parameter list view". OK the
         dialog.
      3. Verify the "Security Level" column is no longer displayed in the
         list view.
    """
    print("[STEP] Creating a new AccuMate Config File")
    new_config_file(app)

    print("[STEP] Navigating to Config Directory -> System Layout")
    page.select_tree_path(["Config Directory", "System Layout"])

    lst = get_list(app)
    columns_before = lst.column_count()
    assert columns_before == EXPECTED_COLUMN_COUNT_WITH_SECURITY_LEVEL, (
        f"Expected {EXPECTED_COLUMN_COUNT_WITH_SECURITY_LEVEL} columns (incl. Security Level) by default: {columns_before}"
    )

    print("[STEP] Disabling 'Display security level in parameter list view'")
    dlg = open_general_options(app)
    set_checkbox(dlg, CHECKBOX_DISPLAY_SECURITY_LEVEL, False)
    close_general_options(dlg, accept=True)

    lst_after = get_list(app)
    columns_after = lst_after.column_count()
    assert columns_after == EXPECTED_COLUMN_COUNT_WITHOUT_SECURITY_LEVEL, (
        f"Expected Security Level column to be hidden ({EXPECTED_COLUMN_COUNT_WITHOUT_SECURITY_LEVEL} columns): {columns_after}"
    )

    print("[STEP] Re-enabling 'Display security level in parameter list view'")
    dlg2 = open_general_options(app)
    set_checkbox(dlg2, CHECKBOX_DISPLAY_SECURITY_LEVEL, True)
    close_general_options(dlg2, accept=True)

    lst_restored = get_list(app)
    columns_restored = lst_restored.column_count()
    assert columns_restored == EXPECTED_COLUMN_COUNT_WITH_SECURITY_LEVEL, (
        f"Expected Security Level column to reappear ({EXPECTED_COLUMN_COUNT_WITH_SECURITY_LEVEL} columns): {columns_restored}"
    )
