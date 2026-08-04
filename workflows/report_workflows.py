"""
Report Configuration document type workflows (scenarios/regression.md B1-B28).

B1-B3, B15-B16, and now B17-B26/B28 are LIVE-VERIFIED against the real
running app (control ids, dialog titles, and every interaction mechanism
below all confirmed live). B4-B14 (device upload/download) remain
unimplemented; B27 was only partially verified - see "Remaining gaps".

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
    controls (1021/1006/1007), OK=1, Cancel=2, and a "Search" button (id
    57636). Selecting a leaf tree node and OK'ing populates the parent
    "Edit Report Item" dialog's Data Register AND Item Value fields with
    the leaf's display name (confirmed live: "Load Arm Layout"->"Number of
    Load Arms" sets both fields to "Number of Load Arms" and Format to
    "%s").
  - B17: for a leaf that supports an offset (e.g. "Pulse Input Config"->
    "Pulse Input Tag", offsets 1-14), ONLY auto_id 1006 of the visible
    Offset 1/2/3 Edit triple actually drives the resulting Data Register
    text - confirmed live by rectangle-matching it to the dialog's own
    dynamic "Offset #: (1 - 14)" label (which replaces the static "Offset
    2:" label once such a leaf is selected), and by confirming setting
    1006 to 1 then 14 correctly produced "Pulse Input Tag (1)" then
    "Pulse Input Tag (14)" while setting the visually-adjacent auto_id
    1007 first had no effect at all.
  - OK'ing "Edit Report Item" places a new item on the report canvas as a
    plain win32 Button control (NOT a SysListView32/tree like every other
    document type in this repo) whose window_text() is the item's
    displayed value and whose control_id is a large, NOT-necessarily-
    unique per-item id (observed value 20033 repeated across multiple
    items in live testing - read items by iterating win.descendants(),
    never by assuming control_id uniquely identifies one) - confirmed live
    for both a plain "User-defined Text" item and a "Run/Program Data
    Description" item. Read all placed items via get_report_items()
    (filters the main window's Button descendants to control_id >=
    10000, since ribbon buttons/dialog buttons are all either negative or
    well below 10000).
  - Typing a value containing a literal space via `send_keys()` silently
    dropped the space in live testing (e.g. "Hello Report" -> "HelloReport")
    - use the escaped `"{SPACE}"` keycode instead of a literal space
    character when building the string passed to send_keys (see
    _send_text's docstring). Similarly, a literal '%' in send_keys() is the
    classic SendKeys ALT-modifier escape character and gets silently
    misrouted unless escaped as "{%}" (discovered live while setting the
    Advanced dialog's Format field to "%10.10s" - see set_report_item_format).
  - insert_report_item() sets Line/Column AFTER the Change/Select-Data-Item
    round trip, not before - live-confirmed that OK'ing "Select Data Item"
    resets "Edit Report Item"'s Line field back to its default (1), so
    setting it earlier gets silently overwritten.
  - B18/B19: the "Advanced..." button (auto_id 1011) opens a THIRD dialog
    titled "Advanced Report Item Options" (class "#32770") with a Format
    Edit (auto_id 1014, mirrors and propagates back to the parent dialog's
    own Format field on OK), a "Restrictions:" ComboBox (auto_id 1031,
    default "Always print this entry"), a read-only "Reference Register"
    Edit (auto_id 1005, default "<none>"), its own "Change" Button (auto_id
    1021), a checkbox Button (auto_id 1032, "Use reference register's
    value for the offset for this item"), OK=1, Cancel=2, Help=9. Setting
    an incompatible format (e.g. "%d" on a string-typed value) and OK'ing
    pops the generic "AccuMate" message-box dialog (class "#32770") with
    static text "Invalid Format String - Type specifier does not match
    item data type" and a single OK button (control_id 2) - confirmed live
    it does NOT close the Advanced dialog underneath.
  - B20/B21/B25: report canvas items support real OS-level mouse drag/drop
    via a plain press-move-release gesture (no special held-drag timing
    trick needed here, unlike the Application Button's "New" fly-out).
    Confirmed live: dragging an item to a new empty spot on the canvas
    moves it (rectangle changes); dragging one item directly onto another
    item is silently rejected (rectangle unchanged, no error dialog);
    dragging an item off the visible canvas area entirely is also silently
    rejected (rectangle unchanged).
  - B22/B23: right-clicking a placed item opens a real, UIA-readable win32
    popup menu (class "#32768" - NOT the Application Button's non-
    automatable backstage-menu pattern) with items "Properties...", "Cut",
    "Copy" (no "Paste" on an item's own menu). Right-clicking an EMPTY spot
    on the canvas opens a different real popup menu with "Insert New
    Here...", "Paste Here", and a disabled "{Line N, Col M}" coordinate
    readout. Confirmed live: Copy an item then "Paste Here" at a new empty
    spot duplicates it; putting plain text on the Windows clipboard (via
    win32clipboard.SetClipboardText) then "Paste Here" creates a brand new
    User-defined Text item containing that exact text.
  - B24: setting an Item Value to 100 '-' characters and OK'ing "Edit
    Report Item" pops the generic "AccuMate" message-box dialog with
    static text "Placing a report item at this position would exceed the
    column bounds. Please choose a different line and/or column." - the
    dialog is NOT closed by this warning.
  - B26/B28: Report Configuration's own "Document Options" dialog is
    titled "Report Options" (class "#32770" - a DIFFERENT dialog from the
    AccuMate Config File's IP-address Document Options used elsewhere in
    this repo), with: Report Title Edit=1005, "Default (80 columns x ~60
    lines per page)" RadioButton=1091, "Wide (132 columns x ~60 lines per
    page)" RadioButton=1092, "Custom:" RadioButton=1093, Columns Edit=1030,
    Lines Edit=1094, "Number of Pages in Report" Edit=1019, "End with Form
    Feed" checkbox Button=1032, Character Set ComboBox=1095/Edit=1001,
    OK=1, Cancel=2. Confirmed live: setting Custom 100x100 and re-opening
    the dialog correctly re-reads back "100"/"100"; setting Number of
    Pages to "2" and re-opening correctly re-reads back "2" (though the
    Columns/Lines fields themselves stay at their prior Default 80/60
    values on reopen - the claimed resulting "120 x 80" effective page
    size from regression.md was not independently re-derived live).
  - B26 KNOWN BUG (matches regression.md's own documented Ticket #3644
    note): once a Report Configuration's page size has been changed via
    Report Options (even just re-confirming/enlarging it), the "Edit
    Report Item" dialog's own placement validation becomes unreliable and
    reports a false "Placing a report item at this position would cause
    overlap with an existing item" error - reproduced live even on a
    genuinely blank, freshly-resized 100x100 canvas with a plainly
    in-bounds line 50/column 90 target. Per regression.md, use
    drag_report_item() on an already-placed item instead of the dialog to
    place items on a resized canvas.

Remaining gaps (NOT yet implemented/verified):
  - B4-B14: wired to workflows/file_transfer_workflows.py's shared upload/
    download dialog module (see upload_report_file/download_report_file
    below), EXCEPT for one report-specific piece that has NOT yet been
    live-probed: regression.md's B4/B13 describe an extra "Select Report"
    dialog appearing mid-upload/download (after clicking Start) to pick
    which report slot the file belongs to (e.g. "User Configured Report 1
    - Transaction Report"). No exact dialog title/control-ids for this
    have been confirmed live yet - _select_report_type() below is a
    best-effort, title/id-agnostic implementation (matches by visible
    control text) built from regression.md's step text alone. Treat
    upload_report_file/download_report_file as UNCONFIRMED
    (`needs_live_verification`) until a real run against a live device
    exercises this path. B11/B12 additionally need provided AM3 (.RPX)/
    early-AM4 report files not present in this repo/environment.
  - B27 (shrink page size with an existing item now out of range): the
    Ticket #3644 bug above blocks placing an item via the dialog after any
    resize, and reliably landing a dragged item beyond a shrunk page's new
    bounds requires the canvas to actually be scrolled/displayed at that
    size on screen, which was not achieved in this pass (drags landing
    outside the currently-visible canvas viewport are rejected the same
    way as a genuine out-of-bounds drop - see B25). Live-attempting this
    produced no warning dialog, but that result is inconclusive (the item
    likely never actually left the still-in-bounds visible viewport)
    rather than a confirmed negative - treat B27 as unconfirmed, not
    "no warning happens".
"""

import time

from pywinauto import Application
from pywinauto.keyboard import send_keys
from pywinauto.mouse import click, press, release, move

from controls.ribbon_controls import click_ribbon_button
from workflows.file_workflows import (
    _click_new_document_flyout_item,
    _NEW_FLYOUT_REPORT_CONFIGURATION_INDEX,
    open_new_document_verified,
)
from workflows.file_transfer_workflows import upload_file, download_file

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
# B17: of the "Offset 1:"/"Offset 2:"/"Offset 3:" Edit triple (auto_ids
# 1021/1006/1007), only 1006 actually drives the resulting "<Name> (N)"
# Data Register text - live-confirmed by rectangle-matching it to the
# dialog's own dynamic "Offset #: (1 - N)" label that appears once an
# offset-having leaf (e.g. "Pulse Input Tag") is selected.
_SELECT_DATA_ITEM_OFFSET_AUTO_ID = "1006"

_ADVANCED_REPORT_ITEM_OPTIONS_TITLE = "Advanced Report Item Options"
_ADVANCED_REPORT_ITEM_OPTIONS_CLASS = "#32770"
_ADVANCED_REPORT_ITEM_FORMAT_AUTO_ID = "1014"
_ADVANCED_REPORT_ITEM_OK_AUTO_ID = "1"
_ADVANCED_REPORT_ITEM_CANCEL_AUTO_ID = "2"

# B19: the generic AccuMate message-box dialog (title "AccuMate", class
# "#32770") reused for many different warnings across this app - here
# specifically for "Invalid Format String - Type specifier does not match
# item data type".
_INVALID_FORMAT_WARNING_TITLE = "AccuMate"
_INVALID_FORMAT_WARNING_CLASS = "#32770"

# B26-B28: Report Configuration's own "Document Options" dialog - titled
# "Report Options", NOT the same dialog as the AccuMate Config File's
# IP-address Document Options used elsewhere in this repo.
_REPORT_OPTIONS_DIALOG_TITLE = "Report Options"
_REPORT_OPTIONS_DIALOG_CLASS = "#32770"
_REPORT_OPTIONS_CUSTOM_RADIO_AUTO_ID = "1093"
_REPORT_OPTIONS_COLUMNS_AUTO_ID = "1030"
_REPORT_OPTIONS_LINES_AUTO_ID = "1094"
_REPORT_OPTIONS_PAGES_AUTO_ID = "1019"
_REPORT_OPTIONS_OK_AUTO_ID = "1"
_REPORT_OPTIONS_CANCEL_AUTO_ID = "2"

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

    def _verify(app_obj):
        return "Report" in app_obj.get_window().window_text()

    open_new_document_verified(app_obj, _NEW_FLYOUT_REPORT_CONFIGURATION_INDEX, _verify, timeout=timeout)
    print(f"[INFO] New Report Configuration file created: {app_obj.get_window().window_text()!r}")


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


def _select_data_item(app_obj, tree_path, offset=None):
    """
    Click "Change..." (must already be showing the "Select Data Item"
    dialog's trigger context, i.e. a "Run/Program Data Value/Description"
    Item Type already chosen in the currently-open "Edit Report Item"
    dialog) and select `tree_path` (e.g. ["Load Arm Layout", "Number of
    Load Arms"]) in the resulting tree, then OK it.

    B17: if the selected leaf has an associated offset (e.g. "Pulse Input
    Config" -> "Pulse Input Tag", which supports offsets 1-14), pass
    `offset` to set it. Live-confirmed the dialog shows THREE Edit
    controls near "Offset 1:"/"Offset 2:"/"Offset 3:" static labels
    (auto_ids 1021/1006/1007 respectively, by screen position) but only
    ONE is ever active/relevant per data item - confirmed by rectangle
    matching that auto_id 1006 is the one vertically aligned with the
    dynamic label that changes to "Offset #: (1 - N)" once a
    offset-having leaf is selected (the other two stay statically labeled
    "Offset 1:"/"Offset 3:" and are NOT the ones that affect the
    resulting "<Name> (N)" Data Register text - confirmed live: setting
    auto_id 1006 to 1 then 14 correctly produced "Pulse Input Tag (1)"
    then "Pulse Input Tag (14)"; setting the visually-adjacent-looking
    auto_id 1007 first had NO effect on the Data Register text at all).
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

    if offset is not None:
        offset_edit = next(
            e for e in win32_dlg.descendants(class_name="Edit")
            if str(e.control_id()) == _SELECT_DATA_ITEM_OFFSET_AUTO_ID
        )
        offset_edit.click_input()
        send_keys("^a")
        _send_text(offset)
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
    offset=None,
):
    """
    B2/B15/B16/B17 steps: click ribbon "Insert" to open the "Edit Report
    Item" dialog, choose `item_type`, and either:
      - set `item_value` directly (for ITEM_TYPE_USER_TEXT), or
      - click "Change..." and select `tree_path` (and optionally `offset`,
        for data items that support one, e.g. "Pulse Input Tag") in the
        "Select Data Item" dialog (for ITEM_TYPE_RUN_PROGRAM_DATA_VALUE/
        _DESCRIPTION), which populates Data Register and Item Value from
        the chosen leaf.
    Then set `line`/`column` if given, and OK the "Edit Report Item"
    dialog.

    NOTE: `line`/`column` are set AFTER the Change/Select-Data-Item round
    trip, not before - live-confirmed that OK'ing the "Select Data Item"
    dialog resets the "Edit Report Item" dialog's Line field back to its
    default (1), so setting it first would be silently overwritten.
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

    if item_type != ITEM_TYPE_USER_TEXT:
        combo = next(
            d for d in win32_dlg.descendants(class_name="ComboBox")
            if str(d.control_id()) == _EDIT_REPORT_ITEM_TYPE_COMBO_AUTO_ID
        )
        combo.select(item_type)
        time.sleep(0.3)

        print(f"[STEP] Clicking 'Change...' -> selecting tree path {tree_path} (offset={offset})")
        uia_dlg.child_window(
            auto_id=_EDIT_REPORT_ITEM_CHANGE_BUTTON_AUTO_ID, control_type="Button"
        ).click_input()
        time.sleep(1.0)
        _select_data_item(app_obj, tree_path, offset=offset)
    elif item_value is not None:
        value_edit = uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_VALUE_AUTO_ID, control_type="Edit")
        value_edit.click_input()
        send_keys("^a")
        _send_text(item_value)
        time.sleep(0.2)

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

    print("[STEP] Clicking OK on Edit Report Item dialog")
    uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.8)


def open_advanced_report_item_options(app_obj):
    """
    B18/B19: click the currently-open "Edit Report Item" dialog's
    "Advanced..." button (auto_id 1011) and return a helper wrapper for
    the resulting "Advanced Report Item Options" dialog (title exact,
    class "#32770"). Real confirmed controls: Format Edit=1014 (mirrors
    the parent dialog's own Format field and propagates back to it on
    OK), Restrictions ComboBox=1031, Reference Register (read-only)
    Edit=1005, "Change" Button=1021 (Reference Register), a checkbox
    Button=1032 ("Use reference register's value for the offset for this
    item"), OK=1, Cancel=2, Help=9.
    """
    dlg_spec = app_obj.app.window(
        title=_EDIT_REPORT_ITEM_DIALOG_TITLE, class_name=_EDIT_REPORT_ITEM_DIALOG_CLASS
    )
    dlg_spec.wait("exists visible ready", timeout=10)
    win32_dlg = dlg_spec.wrapper_object()
    hwnd = win32_dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

    uia_dlg.child_window(
        auto_id=_EDIT_REPORT_ITEM_ADVANCED_BUTTON_AUTO_ID, control_type="Button"
    ).click_input()
    time.sleep(1.0)

    adv_spec = app_obj.app.window(
        title=_ADVANCED_REPORT_ITEM_OPTIONS_TITLE, class_name=_ADVANCED_REPORT_ITEM_OPTIONS_CLASS
    )
    adv_spec.wait("exists visible ready", timeout=10)
    return adv_spec.wrapper_object()


def set_report_item_format(app_obj, fmt):
    """
    B18/B19: open the "Advanced Report Item Options" dialog (the "Edit
    Report Item" dialog must already be open with "Change..." already
    used to pick a data item), set its Format field to `fmt`, and OK it.

    NOTE: pywinauto's send_keys() treats a literal '%' as the classic
    SendKeys-style ALT-modifier escape character - it must be escaped as
    the literal string "{%}" or the keystrokes silently get misrouted
    (live-confirmed: an un-escaped "%10.10s" produced no change at all to
    the Format field). `fmt` may be passed with a normal '%' - this
    function does the escaping.

    Returns True if OK succeeded (format accepted), or False if AccuMate
    popped up an "Invalid Format String" warning dialog instead (B19) -
    in that case this function dismisses the warning (clicks its OK) and
    leaves the Advanced dialog open (matching regression.md's B19
    expectation that the warning appears without closing the dialog).
    """
    adv_dlg = open_advanced_report_item_options(app_obj)
    adv_hwnd = adv_dlg.handle
    adv_uia = Application(backend="uia").connect(handle=adv_hwnd).window(handle=adv_hwnd)

    fmt_edit = next(
        e for e in adv_dlg.descendants(class_name="Edit")
        if str(e.control_id()) == _ADVANCED_REPORT_ITEM_FORMAT_AUTO_ID
    )
    fmt_edit.click_input()
    send_keys("^a")
    send_keys(str(fmt).replace("%", "{%}"))
    time.sleep(0.3)

    adv_uia.child_window(auto_id=_ADVANCED_REPORT_ITEM_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.8)

    warn_spec = app_obj.app.window(
        title=_INVALID_FORMAT_WARNING_TITLE, class_name=_INVALID_FORMAT_WARNING_CLASS
    )
    if warn_spec.exists(timeout=1):
        warn_win32 = warn_spec.wrapper_object()
        ok_btn = next(b for b in warn_win32.descendants(class_name="Button") if b.window_text() == "OK")
        ok_btn.click_input()
        time.sleep(0.3)
        return False
    return True


def get_report_item_format(app_obj):
    """Read the Format field's current value from the open "Edit Report Item" dialog."""
    dlg_spec = app_obj.app.window(
        title=_EDIT_REPORT_ITEM_DIALOG_TITLE, class_name=_EDIT_REPORT_ITEM_DIALOG_CLASS
    )
    dlg_spec.wait("exists visible ready", timeout=10)
    win32_dlg = dlg_spec.wrapper_object()
    fmt_edit = next(
        e for e in win32_dlg.descendants(class_name="Edit")
        if str(e.control_id()) == _EDIT_REPORT_ITEM_FORMAT_AUTO_ID
    )
    return fmt_edit.window_text()


def drag_report_item(app_obj, item_text, dx, dy):
    """
    B20/B21/B25: drag the report canvas item whose current text is
    `item_text` by (dx, dy) screen pixels via a plain press-move-release
    mouse gesture (live-confirmed this is a real, working OS-level drag
    on this app's canvas Button controls - no special held-drag timing
    trick is needed here, unlike the Application Button's "New" fly-out).

    Returns the item's rectangle after the drag attempt (compare against
    its rectangle before calling this to detect whether the drop was
    accepted or rejected - AccuMate silently rejects drops that would
    overlap another item (B21) or land outside the canvas (B25), leaving
    the item at its original position).
    """
    win = app_obj.get_window()
    item_ctrl = next(d for d in win.descendants(class_name="Button") if d.window_text() == item_text)
    rect = item_ctrl.rectangle()
    src_x, src_y = rect.mid_point().x, rect.mid_point().y
    dst_x, dst_y = src_x + dx, src_y + dy

    move(coords=(src_x, src_y))
    time.sleep(0.15)
    press(button="left", coords=(src_x, src_y))
    time.sleep(0.15)
    move(coords=((src_x + dst_x) // 2, (src_y + dst_y) // 2))
    time.sleep(0.15)
    move(coords=(dst_x, dst_y))
    time.sleep(0.2)
    release(button="left", coords=(dst_x, dst_y))
    time.sleep(0.4)

    win2 = app_obj.get_window()
    item_ctrl2 = next((d for d in win2.descendants(class_name="Button") if d.window_text() == item_text), None)
    return item_ctrl2.rectangle() if item_ctrl2 is not None else None


def _open_canvas_context_menu(app_obj, x, y):
    """Right-click the report canvas at screen coords (x, y) and return a
    UIA window wrapper for the resulting real win32 popup menu (class
    "#32768" - confirmed live to be a genuine, UIA-readable Win32 context
    menu, unlike the Application Button's non-automatable backstage
    popups)."""
    click(button="right", coords=(x, y))
    time.sleep(0.6)

    menu_hwnd = None
    for hwnd in win32gui_windows():
        if hwnd[1] == "#32768":
            menu_hwnd = hwnd[0]
    if menu_hwnd is None:
        raise RuntimeError(f"No context menu (#32768) appeared after right-clicking at ({x}, {y})")

    menu_app = Application(backend="uia").connect(handle=menu_hwnd)
    return menu_app.window(handle=menu_hwnd)


def win32gui_windows():
    """Return (hwnd, class_name) pairs for all currently visible top-level windows."""
    import win32gui

    results = []

    def _cb(hwnd, _results):
        if win32gui.IsWindowVisible(hwnd):
            _results.append((hwnd, win32gui.GetClassName(hwnd)))

    win32gui.EnumWindows(_cb, results)
    return results


def _click_context_menu_item(menu_win, item_text):
    item = next(
        (i for i in menu_win.descendants(control_type="MenuItem") if i.window_text() == item_text), None
    )
    if item is None:
        available = [i.window_text() for i in menu_win.descendants(control_type="MenuItem")]
        raise RuntimeError(f"Context menu item {item_text!r} not found (available: {available})")
    item.click_input()
    time.sleep(0.5)


def copy_report_item(app_obj, item_text):
    """
    B22: right-click the report canvas item whose text is `item_text` and
    click "Copy" from its real win32 context menu (confirmed live items:
    "Properties...", "Cut", "Copy" - no "Paste" on an item's own menu).
    """
    win = app_obj.get_window()
    item_ctrl = next(d for d in win.descendants(class_name="Button") if d.window_text() == item_text)
    mid = item_ctrl.rectangle().mid_point()
    menu_win = _open_canvas_context_menu(app_obj, mid.x, mid.y)
    _click_context_menu_item(menu_win, "Copy")


def paste_here(app_obj, x, y):
    """
    B22/B23: right-click an empty spot on the report canvas at screen
    coords (x, y) and click "Paste Here" from its real win32 context menu
    (confirmed live items on an empty canvas spot: "Insert New Here...",
    "Paste Here", and a disabled "{Line N, Col M}" coordinate readout).
    Works both for a previously-Copy'd report item (B22, duplicates it at
    the new location) and for plain text placed on the Windows clipboard
    via win32clipboard (B23, creates a new User-defined Text item with
    that text).
    """
    menu_win = _open_canvas_context_menu(app_obj, x, y)
    _click_context_menu_item(menu_win, "Paste Here")


def set_clipboard_text(text):
    """B23: put plain text on the Windows clipboard (CF_UNICODETEXT) so it
    can be pasted onto the report canvas via paste_here()."""
    import win32clipboard

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(str(text), win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()


def open_report_document_options(app_obj):
    """
    B26-B28: click the ribbon "Document Options" button and return a
    wrapper for the resulting "Report Options" dialog (title exact, class
    "#32770" - a DIFFERENT dialog from the AccuMate Config File's
    IP-address "Document Options" used elsewhere in this repo). Real
    confirmed controls: Report Title Edit=1005, "Default (80 columns x
    ~60 lines per page)" RadioButton=1091, "Wide (132 columns x ~60 lines
    per page)" RadioButton=1092, "Custom:" RadioButton=1093, Columns
    Edit=1030, Lines Edit=1094, Number of Pages in Report Edit=1019, "End
    with Form Feed" checkbox Button=1032, Character Set ComboBox=1095/
    Edit=1001, OK=1, Cancel=2.
    """
    uia_win = app_obj.get_uia_window()
    click_ribbon_button(uia_win, "Document Options")
    time.sleep(1.0)
    dlg_spec = app_obj.app.window(
        title=_REPORT_OPTIONS_DIALOG_TITLE, class_name=_REPORT_OPTIONS_DIALOG_CLASS
    )
    dlg_spec.wait("exists visible ready", timeout=10)
    return dlg_spec.wrapper_object()


def set_report_custom_page_size(app_obj, columns, lines):
    """
    B26/B27: open Report Options, select the "Custom:" radio, set Columns
    and Lines, and OK the dialog.

    KNOWN LIVE-CONFIRMED BUG (matches regression.md's own documented note
    for B26, referencing Ticket #3644): once a Report Configuration's page
    size has been changed via this dialog (even just re-confirming the
    same or a larger size), the "Edit Report Item" dialog's own placement
    validation becomes unreliable and can report a false "Placing a report
    item at this position would cause overlap with an existing item"
    error even for a genuinely blank canvas and in-bounds line/column
    values (live-confirmed: reproduced with a fresh blank canvas resized
    to 100x100, then attempting to place a single item at line 50, column
    90 - well inside bounds and with zero other items present). Per
    regression.md: "it can be manually dragged and placed to that
    location using the cursor" instead - use drag_report_item() on an item
    inserted BEFORE calling this function if you need to place an item on
    a resized canvas.
    """
    dlg = open_report_document_options(app_obj)
    hwnd = dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

    uia_dlg.child_window(
        auto_id=_REPORT_OPTIONS_CUSTOM_RADIO_AUTO_ID, control_type="RadioButton"
    ).click_input()
    time.sleep(0.2)

    cols_edit = uia_dlg.child_window(auto_id=_REPORT_OPTIONS_COLUMNS_AUTO_ID, control_type="Edit")
    cols_edit.click_input()
    send_keys("^a")
    _send_text(columns)

    lines_edit = uia_dlg.child_window(auto_id=_REPORT_OPTIONS_LINES_AUTO_ID, control_type="Edit")
    lines_edit.click_input()
    send_keys("^a")
    _send_text(lines)
    time.sleep(0.3)

    uia_dlg.child_window(auto_id=_REPORT_OPTIONS_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(1.0)


def set_report_number_of_pages(app_obj, num_pages):
    """
    B28: open Report Options, set "Number of Pages in Report" (auto_id
    1019), and OK the dialog. Live-confirmed the field accepts and
    persists the value (e.g. re-reads as "2" on reopen after setting it
    to 2) - the resulting effective page dimensions regression.md claims
    ("resize to 120 x 80") were NOT independently re-derived live in this
    pass (the Columns/Lines fields shown in this same dialog stay at
    their prior Default 80/60 values and don't visibly reflect a computed
    multi-page total - the effective enlarged canvas appears to be
    tracked separately/internally). Treat the exact resulting canvas
    bounds as unconfirmed until specifically re-probed.
    """
    dlg = open_report_document_options(app_obj)
    hwnd = dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

    pages_edit = uia_dlg.child_window(auto_id=_REPORT_OPTIONS_PAGES_AUTO_ID, control_type="Edit")
    pages_edit.click_input()
    send_keys("^a")
    _send_text(num_pages)
    time.sleep(0.3)

    uia_dlg.child_window(auto_id=_REPORT_OPTIONS_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(1.0)


def _select_report_type(dlg_wrapper, report_type, timeout=10):
    """
    Resolve regression.md B4/B13's "Select Report" dialog, which appears
    mid-upload/download to ask which report slot the file belongs to
    (e.g. "User Configured Report 1 - Transaction Report", "Batch Detail",
    "Prove Report"). UNCONFIRMED/best-effort: no live probe of this
    dialog's exact title/control-ids has been done yet (see module
    docstring "Remaining gaps"), so this matches purely by visible control
    text rather than a known automation_id/control_id, and clicks the
    first Button-class control (by visual position, topmost first) whose
    remaining text looks like an "OK"/affirmative commit button. Intended
    to be passed as `on_intermediate_dialog` to
    workflows.file_transfer_workflows.start_transfer()/upload_file()/
    download_file().
    """
    print(f"[STEP] Selecting report type {report_type!r} in intermediate dialog")
    deadline = time.time() + timeout
    option_ctrl = None
    while time.time() < deadline and option_ctrl is None:
        for ctrl in dlg_wrapper.children(recurse=True):
            try:
                if report_type in ctrl.window_text():
                    option_ctrl = ctrl
                    break
            except Exception:
                continue
        if option_ctrl is None:
            time.sleep(0.5)

    if option_ctrl is None:
        raise RuntimeError(
            f"Could not find a control matching report type {report_type!r} "
            f"in dialog {dlg_wrapper.window_text()!r} - this dialog has not "
            "been live-probed yet, see report_workflows.py module docstring."
        )

    option_ctrl.click_input()
    time.sleep(0.3)

    ok_ctrl = None
    for ctrl in dlg_wrapper.children(recurse=True):
        try:
            if ctrl.class_name() == "Button" and ctrl.window_text().strip().lstrip("&") == "OK":
                ok_ctrl = ctrl
                break
        except Exception:
            continue
    if ok_ctrl is None:
        raise RuntimeError(
            f"Could not find an 'OK' button on dialog {dlg_wrapper.window_text()!r} "
            "to confirm the selected report type."
        )
    ok_ctrl.click_input()
    time.sleep(0.5)


def upload_report_file(app_obj, file_path, report_type):
    """
    B5/B7/B9: Upload a Report File (.al4rep) to a connected AccuLoad via
    the ribbon "Upload File to AccuLoad" button's "AccuMate File Transfer"
    window, then select `report_type` (e.g. "User Configured Report 1 -
    Transaction Report") in the resulting "Select Report" dialog.

    Returns the result dict from workflows.file_transfer_workflows.
    start_transfer(): {"message": str or None, "timed_out": bool}.

    UNCONFIRMED (needs_live_verification): the "Select Report" dialog
    handling (_select_report_type) has not yet been live-verified against
    a real device - see module docstring "Remaining gaps".
    """
    return upload_file(
        app_obj, file_path,
        on_intermediate_dialog=lambda w: _select_report_type(w, report_type),
    )


def download_report_file(app_obj, save_path, report_type):
    """
    B6/B8/B10: Download a Report File from a connected AccuLoad via the
    ribbon "Download File From AccuLoad" button, selecting "Report Files"
    in the "File Download Selection" dialog, then `report_type` (e.g.
    "User Configured Report 1 - Transaction Report") in the resulting
    "Select Report" dialog.

    Returns the result dict from workflows.file_transfer_workflows.
    start_transfer() - see upload_report_file's docstring, including the
    UNCONFIRMED "Select Report" dialog caveat.
    """
    return download_file(
        app_obj, "Report Files", save_path,
        on_intermediate_dialog=lambda w: _select_report_type(w, report_type),
    )
