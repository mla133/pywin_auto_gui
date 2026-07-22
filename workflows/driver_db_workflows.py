"""
Driver Database document type workflows (scenarios/regression.md D1-D9).

D1-D4 are LIVE-VERIFIED against the real running app (control ids, dialog
titles, and the "New" fly-out mechanism all confirmed live - see
workflows/file_workflows.py's _click_new_document_flyout_item for the
fly-out mechanism itself). D6-D9 remain unimplemented - see the "Remaining
gaps" section below.

Live-verified findings:
  - The Application Button's "New" item DOES have a real fly-out submenu
    ("AccuMate Config File", "Translation", "Equation Set", "Driver
    Database") - resolving the conflict noted in an earlier draft of this
    module. It only renders under a genuine held-mouse-button drag gesture;
    see file_workflows._click_new_document_flyout_item's docstring for why.
  - Selecting "Driver Database" creates a new document titled
    "DDB<n> - AccuMate for AccuLoad" with a single-column-header
    SysListView32 grid (columns: ID Number, HID #, PIN, Field #1, Field #2,
    Field #3) - the same get_list/get_list_row_texts primitives used
    elsewhere in this repo for Config Directory listviews work unchanged
    here.
  - Double-clicking a grid row opens the "Edit Database Record" dialog
    (title confirmed exact, class "#32770") with these real automation_ids:
    Raw Card Data edit=1005, PIN #=1161, Field 1=1144, Field 2=1019,
    Field 3=1160, "< Enter in HID Format..." button=1011, OK=1, Cancel=2.
  - The HID Format button opens a second dialog titled
    "HID Card Data Encoding" with three Edit fields left-to-right:
    Extended Code (0-4095)=1158, Facility Code (0-255)=1159,
    Card # (0-65535)=1144 (a different dialog, so this ID overlaps
    harmlessly with the parent dialog's Field 1 automation_id), OK=1,
    Cancel=2, Help=9. OK'ing it converts the three values into a single
    packed number back in the parent dialog's Raw Card Data field (e.g.
    Extended=3, Facility=7, Card#=12345 -> Raw Card Data "0030730") -
    confirmed live, matching regression.md D2 step 5 exactly.
  - Reading Edit control values reliably requires the win32 backend's
    descendants(class_name="Edit") + .window_text() (matched by
    .control_id()) - the UIA backend's own .window_text()/legacy_properties
    Value were both unreliable/empty for these specific Edit controls in
    live testing (a different flavor of the "UIA text automation doesn't
    work reliably in this app" pattern already documented elsewhere in this
    repo), so this module intentionally uses win32-backend reads throughout
    even though UIA is still used to reach controls by automation_id for
    writes/clicks (a form of the dual-backend approach documented in
    the repo-level custom instructions' "Key conventions" section).

Remaining gaps (NOT yet implemented/verified):
  - D5 (Save As / Open comparison): needs workflows.file_workflows.save_as/
    open_file_dialog confirmed compatible with non-Config document types -
    not yet tried live.
  - D6-D8: need a live, reachable AccuLoad device AND a not-yet-built
    "AccuMate File Transfer" upload/download dialog workflow (genuinely new
    ground, no existing code anywhere in this repo touches that dialog).
  - D9: needs a provided AM3-format Database Driver File (.3DB) that does
    not currently exist in this repo/environment - same class of blocker as
    H3-H8's provided files.
"""

import time

from pywinauto.keyboard import send_keys
from pywinauto import Application

from controls.common_controls import get_list, get_list_row_texts
from workflows.file_workflows import (
    _click_new_document_flyout_item,
    _NEW_FLYOUT_DRIVER_DATABASE_INDEX,
    open_new_document_verified,
)

_EDIT_RECORD_DIALOG_TITLE = "Edit Database Record"
_EDIT_RECORD_DIALOG_CLASS = "#32770"
_EDIT_RECORD_RAW_CARD_DATA_AUTO_ID = "1005"
_EDIT_RECORD_HID_FORMAT_BUTTON_AUTO_ID = "1011"  # "< Enter in HID Format..."
_EDIT_RECORD_PIN_FIELD_AUTO_ID = "1161"
_EDIT_RECORD_FIELD1_AUTO_ID = "1144"
_EDIT_RECORD_FIELD2_AUTO_ID = "1019"
_EDIT_RECORD_FIELD3_AUTO_ID = "1160"
_EDIT_RECORD_OK_AUTO_ID = "1"
_EDIT_RECORD_CANCEL_AUTO_ID = "2"

_HID_FORMAT_DIALOG_TITLE = "HID Card Data Encoding"
_HID_FORMAT_DIALOG_CLASS = "#32770"
_HID_FORMAT_EXTENDED_CODE_AUTO_ID = "1158"
_HID_FORMAT_FACILITY_CODE_AUTO_ID = "1159"
_HID_FORMAT_CARD_NUMBER_AUTO_ID = "1144"
_HID_FORMAT_OK_AUTO_ID = "1"

_NEW_DDB_TITLE_RE = r"DDB\d+ - AccuMate for AccuLoad"
_NEW_DDB_TIMEOUT = 20


def create_new_driver_database_file(app_obj, timeout=_NEW_DDB_TIMEOUT):
    """
    D1: Create New Driver Database Files.

    regression.md: "Click the top left circle button then hover your mouse
    over 'New'. Click on 'Driver Database'." -> "The application will
    display a new Driver Database view."

    Uses open_new_document_verified() (see file_workflows.py) rather than
    a single fly-out click: live testing showed the fly-out's per-item
    hit-testing is flaky (sporadically lands on a neighboring document
    type or misses entirely) even with a stepped drag and generous dwell
    times - retrying with a fresh verification check is more robust than
    any single fixed offset/timing combination found.
    """
    print("[STEP] Opening Application menu -> New -> Driver Database")

    def _verify(app_obj):
        title = app_obj.get_window().window_text()
        return "DDB" in title and get_list(app_obj).item_count() >= 1

    open_new_document_verified(app_obj, _NEW_FLYOUT_DRIVER_DATABASE_INDEX, _verify, timeout=timeout)
    print(f"[INFO] New Driver Database file created: {app_obj.get_window().window_text()!r}")


def get_driver_database_rows(app_obj):
    """
    Read all rows currently shown in the Driver Database grid view.
    Live-confirmed: this is a plain SysListView32, same as Config Directory
    views, so the existing get_list/get_list_row_texts primitives apply
    unchanged.
    """
    lst = get_list(app_obj)
    return [get_list_row_texts(lst, i) for i in range(lst.item_count())]


def _get_dialog_by_app(win32_app, title, class_name, timeout=10):
    dlg_spec = win32_app.window(title=title, class_name=class_name)
    dlg_spec.wait("exists visible ready", timeout=timeout)
    win32_dlg = dlg_spec.wrapper_object()
    hwnd = win32_dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)
    return win32_dlg, uia_dlg


def _get_dialog(app_obj, title, class_name, timeout=10):
    return _get_dialog_by_app(app_obj.app, title, class_name, timeout)


def open_edit_database_record_dialog(app_obj, row_index=0):
    """
    D2/D3/D4 step 1: Double-click a Driver Database grid row to open the
    "Edit Database Record" dialog. Returns (win32_dlg, uia_dlg) - the win32
    wrapper is used for reliable text reads, the uia wrapper for
    automation_id-based control lookups (see module docstring).
    """
    lst = get_list(app_obj)

    if row_index >= lst.item_count():
        raise RuntimeError(
            f"Driver Database grid only has {lst.item_count()} row(s), "
            f"cannot open row {row_index}"
        )

    item = lst.get_item(row_index)
    item.select()

    rect = item.rectangle()
    x = rect.left + 60
    y = rect.top + rect.height() // 2

    print(f"[INFO] Opening 'Edit Database Record' dialog for row {row_index}")
    lst.click_input(coords=(x, y))
    lst.click_input(coords=(x, y), double=True)

    return _get_dialog(app_obj, _EDIT_RECORD_DIALOG_TITLE, _EDIT_RECORD_DIALOG_CLASS)


def _set_edit_field(uia_dlg, auto_id, value):
    """Reliable field-set pattern for this app's Edit controls: click to
    focus, select-all, type - UIA's set_edit_text() was seen to intermittently
    raise a COMError on freshly-opened dialogs in this app (live-confirmed on
    the HID Format dialog specifically)."""
    edit = uia_dlg.child_window(auto_id=auto_id, control_type="Edit")
    edit.click_input()
    time.sleep(0.15)
    send_keys("^a")
    send_keys(str(value))
    time.sleep(0.15)


def _read_edit_field(win32_dlg, auto_id):
    """Reliable field-read pattern: win32 backend descendants matched by
    control_id() - the UIA backend's window_text()/legacy Value were both
    unreliable/empty for these Edit controls in live testing."""
    for d in win32_dlg.descendants(class_name="Edit"):
        if str(d.control_id()) == str(auto_id):
            return d.window_text()
    raise RuntimeError(f"Edit control with auto_id={auto_id!r} not found")


def enter_hid_format_id(app_obj, win32_dlg, uia_dlg, extended_code, facility_code, card_number):
    """
    D2 step 4-5: Click "< Enter in HID Format..." to open the "HID Card
    Data Encoding" dialog, enter Extended/Facility/Card # values (bounds
    per the dialog itself: Extended Code 0-4095, Facility Code 0-255,
    Card # 0-65535), OK it - the "Edit Database Record" dialog's Raw Card
    Data field is then populated with the values packed into a single
    number (confirmed live: 3/7/12345 -> "0030730").

    `win32_dlg`/`uia_dlg` are the "Edit Database Record" dialog wrappers
    returned by open_edit_database_record_dialog(). Returns the resulting
    Raw Card Data string.
    """
    hid_btn = uia_dlg.child_window(auto_id=_EDIT_RECORD_HID_FORMAT_BUTTON_AUTO_ID, control_type="Button")
    print("[STEP] Clicking '< Enter in HID Format...'")
    hid_btn.click_input()
    time.sleep(0.8)

    # The HID Format dialog is a separate top-level window (not a child of
    # Edit Database Record), so it's looked up the same way as any other
    # top-level dialog via the app's own win32 Application object.
    hid_win32_dlg, hid_uia_dlg = _get_dialog_by_app(app_obj.app, _HID_FORMAT_DIALOG_TITLE, _HID_FORMAT_DIALOG_CLASS)

    print(f"[INFO] Setting Extended={extended_code}, Facility={facility_code}, Card#={card_number}")
    _set_edit_field(hid_uia_dlg, _HID_FORMAT_EXTENDED_CODE_AUTO_ID, extended_code)
    _set_edit_field(hid_uia_dlg, _HID_FORMAT_FACILITY_CODE_AUTO_ID, facility_code)
    _set_edit_field(hid_uia_dlg, _HID_FORMAT_CARD_NUMBER_AUTO_ID, card_number)

    hid_uia_dlg.child_window(auto_id=_HID_FORMAT_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.5)

    raw_card_data = _read_edit_field(win32_dlg, _EDIT_RECORD_RAW_CARD_DATA_AUTO_ID)
    print(f"[INFO] Raw Card Data after HID Format conversion: {raw_card_data!r}")
    return raw_card_data


def set_driver_record_fields(win32_dlg, uia_dlg, pin=None, field1=None, field2=None, field3=None):
    """
    D3 step 3 / D4 step 3: set PIN # and Field 1-3 values in an open "Edit
    Database Record" dialog, then OK it.
    """
    if pin is not None:
        _set_edit_field(uia_dlg, _EDIT_RECORD_PIN_FIELD_AUTO_ID, pin)
    if field1 is not None:
        _set_edit_field(uia_dlg, _EDIT_RECORD_FIELD1_AUTO_ID, field1)
    if field2 is not None:
        _set_edit_field(uia_dlg, _EDIT_RECORD_FIELD2_AUTO_ID, field2)
    if field3 is not None:
        _set_edit_field(uia_dlg, _EDIT_RECORD_FIELD3_AUTO_ID, field3)

    print("[STEP] Clicking OK on Edit Database Record dialog")
    uia_dlg.child_window(auto_id=_EDIT_RECORD_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.5)


def upload_driver_database_file(app_obj, file_path):
    """
    D6: Upload a Driver Database File (.al4ddb) to a connected AccuLoad via
    the ribbon "Upload File to AccuLoad" button's "AccuMate File Transfer"
    window.

    NOT YET IMPLEMENTED - needs live device access plus a live probe of the
    "AccuMate File Transfer" dialog's controls (no existing workflow for it
    anywhere in this repo). See module docstring "Remaining gaps".
    """
    raise NotImplementedError(
        "D6: 'AccuMate File Transfer' upload dialog has no existing "
        "workflow in this repo and needs live device access plus a live "
        "probe of its controls before this can be implemented."
    )


def download_driver_database_file(app_obj, save_path):
    """
    D7/D8: Download a Driver Database File from a connected AccuLoad via
    the ribbon "Download File From AccuLoad" button.

    NOT YET IMPLEMENTED - see upload_driver_database_file's docstring; same
    gap.
    """
    raise NotImplementedError(
        "D7/D8: 'AccuMate File Transfer' download dialog has no existing "
        "workflow in this repo and needs live device access plus a live "
        "probe of its controls before this can be implemented."
    )

