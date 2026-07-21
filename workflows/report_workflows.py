"""
Report Configuration document type workflows (scenarios/regression.md B1-B28).

B1-B3 and B15-B16 are LIVE-VERIFIED against the real running app (control
ids, dialog titles, and the "New" fly-out mechanism all confirmed live).
B4-B14 (device upload/download), B17-B28 (canvas drag/drop, format
validation, out-of-bounds, document size/pages) remain unimplemented - see
"Remaining gaps" below.

Live-verified findings:
  - The Application Button's "New" fly-out has 5 real items, not 4 as
    previously found while scoping D1/E1: "AccuMate Config File" (0),
    "Report Configuration" (1), "Translation" (2), "Equation Set" (3),
    "Driver Database" (4) - uniform ~52px row spacing. An earlier version
    of file_workflows._APP_MENU_NEW_FLYOUT_Y_OFFSETS omitted "Report
    Configuration" entirely (a 4-item list that happened to still work for
    Translation/Equation Set/Driver Database purely because their offsets
    were copied verbatim from a screenshot, just mislabeled with the wrong
    0-based indices) - this has been fixed in file_workflows.py.
  - Selecting "Report Configuration" creates a new document titled
    "Report<n> - AccuMate for AccuLoad".
  - The ribbon button is simply named "Insert" (same button already used
    for Equation Set's "Insert" - it's context-sensitive per active
    document type), opening the "Edit Report Item" dialog (title exact,
    class "#32770") with real automation_ids: Line Edit=1001, Column
    Edit=1008, Item Type ComboBox=1020 (options: "Run/Program Data Value",
    "Run/Program Data Description", "User-defined Text"), Data Register
    (read-only) Edit=1005, "Change..." Button=1021, Item Value Edit=1022,
    Format Edit=1014, "Advanced..." Button=1011, OK=1, Cancel=2, Help=9.
  - Clicking "Change..." (only relevant/enabled for the "Run/Program Data
    Value"/"Run/Program Data Description" Item Types) opens a SECOND
    top-level dialog titled "Select Data Item" (class "#32770") containing
    a SysTreeView32 (auto_id 1090) of data registers (e.g. "Load Arm
    Layout" -> "Number of Load Arms"), an "Offset 1/2/3" triple of Edit
    controls (1006/1007/1021 - NOTE: 1021 collides with the parent
    dialog's "Change..." button auto_id, harmless since different
    windows), OK=1, Cancel=2, and a "Search" button (id 57636). Selecting
    a leaf tree node and OK'ing populates the parent "Edit Report Item"
    dialog's Data Register AND Item Value fields with the leaf's display
    name (confirmed live: "Load Arm Layout"->"Number of Load Arms" sets
    both fields to "Number of Load Arms" and Format to "%s").
  - OK'ing "Edit Report Item" places a new item on the report canvas as a
    plain win32 Button control (NOT a SysListView32/tree like every other
    document type in this repo) whose window_text() is the item's
    displayed value and whose control_id is a large per-item id (e.g.
    20033, allocated sequentially) - confirmed live for both a plain
    "User-defined Text" item and a "Run/Program Data Description" item.
    Read all placed items via get_report_items() (filters the main
    window's Button descendants to control_id >= 10000, since ribbon
    buttons/dialog buttons are all either negative or well below 10000).
  - Typing a value containing a literal space via `send_keys()` silently
    dropped the space in live testing (e.g. "Hello Report" -> "HelloReport")
    - use the escaped `"{SPACE}"` keycode instead of a literal space
    character when building the string passed to send_keys (see
    _send_text's docstring).

Remaining gaps (NOT yet implemented/verified):
  - B4-B14: need a live, reachable AccuLoad device AND a not-yet-built
    "AccuMate File Transfer" upload/download dialog workflow (same shared
    gap as driver_db_workflows.py's D6-D8/equation_workflows.py's E4-E6/E8).
    B11/B12 additionally need provided AM3 (.RPX)/early-AM4 report files
    not present in this repo/environment.
  - B17 (item offsets): the "Select Data Item" dialog's Offset 1/2/3 Edit
    controls are visible/probed above but not yet exercised end-to-end.
  - B18/B19 (Advanced Report Item Options / format validation): the
    "Advanced..." button (auto_id 1011) opens a dialog that has not yet
    been probed.
  - B20-B25 (drag/drop item moving, copy/paste, out-of-bounds): canvas
    mouse-drag interactions on the Button-based item controls, not yet
    probed/implemented.
  - B26-B28 (document size/page count): Document Options dialog fields for
    Report Configuration documents specifically have not yet been probed
    (Document Options is already used elsewhere for AccuMate Config Files'
    IP address, but the Report-specific page-size/page-count fields are a
    different tab/layout, unconfirmed).
"""

import time

from pywinauto import Application
from pywinauto.keyboard import send_keys

from controls.ribbon_controls import click_ribbon_button
from workflows.file_workflows import (
    _click_new_document_flyout_item,
    _NEW_FLYOUT_REPORT_CONFIGURATION_INDEX,
)

_EDIT_REPORT_ITEM_DIALOG_TITLE = "Edit Report Item"
_EDIT_REPORT_ITEM_DIALOG_CLASS = "#32770"
_EDIT_REPORT_ITEM_LINE_AUTO_ID = "1001"
_EDIT_REPORT_ITEM_COLUMN_AUTO_ID = "1008"
_EDIT_REPORT_ITEM_TYPE_COMBO_AUTO_ID = "1020"
_EDIT_REPORT_ITEM_DATA_REGISTER_AUTO_ID = "1005"
_EDIT_REPORT_ITEM_CHANGE_BUTTON_AUTO_ID = "1021"
_EDIT_REPORT_ITEM_VALUE_AUTO_ID = "1022"
_EDIT_REPORT_ITEM_FORMAT_AUTO_ID = "1014"
_EDIT_REPORT_ITEM_ADVANCED_BUTTON_AUTO_ID = "1011"
_EDIT_REPORT_ITEM_OK_AUTO_ID = "1"
_EDIT_REPORT_ITEM_CANCEL_AUTO_ID = "2"

_SELECT_DATA_ITEM_DIALOG_TITLE = "Select Data Item"
_SELECT_DATA_ITEM_DIALOG_CLASS = "#32770"
_SELECT_DATA_ITEM_TREE_AUTO_ID = "1090"
_SELECT_DATA_ITEM_OK_AUTO_ID = "1"
_SELECT_DATA_ITEM_CANCEL_AUTO_ID = "2"

ITEM_TYPE_USER_TEXT = "User-defined Text"
ITEM_TYPE_RUN_PROGRAM_DATA_VALUE = "Run/Program Data Value"
ITEM_TYPE_RUN_PROGRAM_DATA_DESCRIPTION = "Run/Program Data Description"

_NEW_REPORT_TITLE_RE = r"Report\d+ - AccuMate for AccuLoad"
_NEW_REPORT_TIMEOUT = 20

# Report canvas items are allocated real, large win32 control ids (observed
# starting around 20033) - ribbon/dialog buttons are all either -1 or well
# below this, so this threshold reliably distinguishes "an item placed on
# the report canvas" from any other Button-class control in the main window.
_REPORT_ITEM_CONTROL_ID_THRESHOLD = 10000


def _send_text(text):
    """send_keys() silently drops literal space characters in this app's
    Edit controls (live-confirmed on the Item Value field) - escape spaces
    as the `{SPACE}` keycode instead."""
    send_keys(str(text).replace(" ", "{SPACE}"))


def create_new_report_file(app_obj, timeout=_NEW_REPORT_TIMEOUT):
    """
    B1: Creating New Report Files.

    regression.md: "Click the top left circle button then hover your mouse
    over 'New'... Click on 'Report Configuration'." -> a new Report
    Configuration view is displayed.
    """
    print("[STEP] Opening Application menu -> New -> Report Configuration")
    _click_new_document_flyout_item(app_obj, _NEW_FLYOUT_REPORT_CONFIGURATION_INDEX)

    start = time.time()
    while time.time() - start < timeout:
        try:
            title = app_obj.get_window().window_text()
            if "Report" in title:
                print(f"[INFO] New Report Configuration file created: {title!r}")
                return
        except Exception:
            pass
        time.sleep(0.5)

    raise RuntimeError(f"New Report Configuration view did not appear within {timeout}s")


def get_report_items(app_obj):
    """
    Read all items currently placed on the Report canvas. Live-confirmed:
    each placed item is a plain win32 Button control (not a
    SysListView32/tree like every other document type in this repo) with
    a large, per-item control_id and window_text() equal to its displayed
    value. Returns a list of dicts: {"control_id": int, "text": str}.
    """
    win = app_obj.get_window()
    items = []
    for d in win.descendants(class_name="Button"):
        try:
            cid = d.control_id()
        except Exception:
            continue
        if cid and cid >= _REPORT_ITEM_CONTROL_ID_THRESHOLD:
            items.append({"control_id": cid, "text": d.window_text()})
    return items


def _select_data_item(app_obj, tree_path):
    """
    Click "Change..." (must already be showing the "Select Data Item"
    dialog's trigger context, i.e. a "Run/Program Data Value/Description"
    Item Type already chosen in the currently-open "Edit Report Item"
    dialog) and select `tree_path` (e.g. ["Load Arm Layout", "Number of
    Load Arms"]) in the resulting tree, then OK it.
    """
    dlg_spec = app_obj.app.window(
        title=_SELECT_DATA_ITEM_DIALOG_TITLE, class_name=_SELECT_DATA_ITEM_DIALOG_CLASS
    )
    dlg_spec.wait("exists visible ready", timeout=10)
    win32_dlg = dlg_spec.wrapper_object()
    hwnd = win32_dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

    tree = win32_dlg.descendants(class_name="SysTreeView32")[0]
    current = None
    for level, name in enumerate(tree_path):
        search_space = tree.roots() if level == 0 else current.children()
        found = next((n for n in search_space if name in n.text()), None)
        if found is None:
            raise RuntimeError(f"Select Data Item tree node '{name}' not found")
        if level < len(tree_path) - 1:
            found.expand()
        else:
            found.click_input()
        current = found
        time.sleep(0.2)

    uia_dlg.child_window(auto_id=_SELECT_DATA_ITEM_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.5)


def insert_report_item(
    app_obj,
    item_type=ITEM_TYPE_USER_TEXT,
    item_value=None,
    line=None,
    column=None,
    tree_path=None,
):
    """
    B2/B15/B16 steps: click ribbon "Insert" to open the "Edit Report Item"
    dialog, optionally set Line/Column, choose `item_type`, and either:
      - set `item_value` directly (for ITEM_TYPE_USER_TEXT), or
      - click "Change..." and select `tree_path` in the "Select Data Item"
        dialog (for ITEM_TYPE_RUN_PROGRAM_DATA_VALUE/_DESCRIPTION), which
        populates both Data Register and Item Value from the chosen leaf.
    Then OK the "Edit Report Item" dialog.
    """
    uia_win = app_obj.get_uia_window()
    print("[STEP] Clicking ribbon 'Insert'")
    click_ribbon_button(uia_win, "Insert")
    time.sleep(1.0)

    dlg_spec = app_obj.app.window(
        title=_EDIT_REPORT_ITEM_DIALOG_TITLE, class_name=_EDIT_REPORT_ITEM_DIALOG_CLASS
    )
    dlg_spec.wait("exists visible ready", timeout=10)
    win32_dlg = dlg_spec.wrapper_object()
    hwnd = win32_dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

    if line is not None:
        line_edit = uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_LINE_AUTO_ID, control_type="Edit")
        line_edit.click_input()
        send_keys("^a")
        _send_text(line)
        time.sleep(0.2)

    if column is not None:
        col_edit = uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_COLUMN_AUTO_ID, control_type="Edit")
        col_edit.click_input()
        send_keys("^a")
        _send_text(column)
        time.sleep(0.2)

    if item_type != ITEM_TYPE_USER_TEXT:
        combo = next(
            d for d in win32_dlg.descendants(class_name="ComboBox")
            if str(d.control_id()) == _EDIT_REPORT_ITEM_TYPE_COMBO_AUTO_ID
        )
        combo.select(item_type)
        time.sleep(0.3)

        print(f"[STEP] Clicking 'Change...' -> selecting tree path {tree_path}")
        uia_dlg.child_window(
            auto_id=_EDIT_REPORT_ITEM_CHANGE_BUTTON_AUTO_ID, control_type="Button"
        ).click_input()
        time.sleep(1.0)
        _select_data_item(app_obj, tree_path)
    elif item_value is not None:
        value_edit = uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_VALUE_AUTO_ID, control_type="Edit")
        value_edit.click_input()
        send_keys("^a")
        _send_text(item_value)
        time.sleep(0.2)

    print("[STEP] Clicking OK on Edit Report Item dialog")
    uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.8)


def upload_report_file(app_obj, file_path, report_type):
    """
    B5/B7/B9: Upload a Report File (.al4rep) to a connected AccuLoad via
    the ribbon "Upload File to AccuLoad" button's "AccuMate File Transfer"
    window, then select `report_type` (e.g. "User Configured Report 1 -
    Transaction Report") in the resulting "Select Report" dialog.

    NOT YET IMPLEMENTED - needs live device access plus a live probe of
    the "AccuMate File Transfer" dialog's controls (shared gap with
    driver_db_workflows.upload_driver_database_file /
    equation_workflows.upload_equation_file). See module docstring
    "Remaining gaps".
    """
    raise NotImplementedError(
        "B5/B7/B9: 'AccuMate File Transfer' upload dialog has no existing "
        "workflow in this repo and needs live device access plus a live "
        "probe of its controls before this can be implemented."
    )


def download_report_file(app_obj, save_path, report_type):
    """
    B6/B8/B10: Download a Report File from a connected AccuLoad via the
    ribbon "Download File From AccuLoad" button, selecting `report_type`.

    NOT YET IMPLEMENTED - see upload_report_file's docstring; same gap.
    """
    raise NotImplementedError(
        "B6/B8/B10: 'AccuMate File Transfer' download dialog has no "
        "existing workflow in this repo and needs live device access plus "
        "a live probe of its controls before this can be implemented."
    )
