"""
Equation Set document type workflows (scenarios/regression.md E1-E8).

E1-E3 are LIVE-VERIFIED against the real running app (control ids, dialog
titles, and the "New" fly-out mechanism all confirmed live - see
workflows/file_workflows.py's _click_new_document_flyout_item for the
fly-out mechanism itself, shared with Driver Database). E4-E8 remain
unimplemented - see "Remaining gaps" below.

Live-verified findings:
  - Selecting "Equation Set" from the New fly-out creates a new document
    titled "Equation<n> - AccuMate for AccuLoad" with a single-column
    SysListView32 grid (0 rows initially) - the same get_list/
    get_list_row_texts primitives used elsewhere in this repo work
    unchanged.
  - The ribbon button is simply named "Insert" (no separate "Edit Options"
    tab needs to be selected first - it's directly visible/enabled via
    find_ribbon_button/click_ribbon_button as-is once an Equation Set
    document is the active view).
  - Clicking "Insert" opens the "Edit Equation Line" dialog (title exact,
    class "#32770") with real automation_ids: result-type ComboBox=2001,
    register-number Edit=2002, expression Edit=2003, live-preview
    Static=2038, OK=1, Cancel=2, Help=2006.
  - The ComboBox's exact option text for regression.md's "User BOOLEAN
    register..." is "User BOOLEAN register (accessible via comm, etc.)"
    (confirmed via the win32 ComboBoxWrapper's item_texts(); UIA's
    combo.expand()/children() did NOT reliably enumerate the real option
    list in live testing - selection was done via the win32 backend's
    .select(text) instead).
  - OK'ing the dialog appends a new row to the Equation Set grid reading
    "USERBOOL{register} = {expression}" - confirmed live for registers
    1/2/3 with expressions "1"/"2"/"3", producing exactly 3 rows matching
    regression.md E2 step 3's expected result.
  - save_as()/open_file_dialog() (workflows.file_workflows) both work
    unchanged for Equation Set documents (.al4equ) - confirmed a full
    save + reopen round-trip produces identical grid rows.

Remaining gaps (NOT yet implemented/verified):
  - E4-E6/E8: need a live, reachable AccuLoad device AND a not-yet-built
    "AccuMate File Transfer" upload/download dialog workflow (same shared
    gap as driver_db_workflows.py's D6-D8).
  - E7: needs a provided AM3-format Equation Set File (.EQX) that does not
    currently exist in this repo/environment - same class of blocker as
    H3-H8's provided files.
"""

import time

from pywinauto import Application
from pywinauto.keyboard import send_keys

from controls.common_controls import get_list, get_list_row_texts
from controls.ribbon_controls import click_ribbon_button
from workflows.file_workflows import (
    _click_new_document_flyout_item,
    _NEW_FLYOUT_EQUATION_SET_INDEX,
    open_new_document_verified,
)

_EDIT_EQUATION_LINE_DIALOG_TITLE = "Edit Equation Line"
_EDIT_EQUATION_LINE_DIALOG_CLASS = "#32770"
_EDIT_EQUATION_LINE_RESULT_TYPE_COMBO_AUTO_ID = "2001"
_EDIT_EQUATION_LINE_REGISTER_NUMBER_AUTO_ID = "2002"
_EDIT_EQUATION_LINE_EXPRESSION_EDIT_AUTO_ID = "2003"
_EDIT_EQUATION_LINE_OK_AUTO_ID = "1"
_EDIT_EQUATION_LINE_CANCEL_AUTO_ID = "2"

_USER_BOOL_REGISTER_OPTION = "User BOOLEAN register (accessible via comm, etc.)"

_NEW_EQUATION_TITLE_RE = r"Equation\d+ - AccuMate for AccuLoad"
_NEW_EQUATION_TIMEOUT = 20


def create_new_equation_set_file(app_obj, timeout=_NEW_EQUATION_TIMEOUT):
    """
    E1: Create New Equation Files.

    regression.md: "Click the top left circle button then hover your mouse
    over 'New'. Click on 'Equation Set'." -> "The application will display
    a new Equation Set view."

    Uses open_new_document_verified() rather than a single fly-out click:
    live testing showed the fly-out's per-item hit-testing is flaky
    (sporadically lands on a neighboring document type, e.g. Translation
    or Driver Database, or misses entirely) even with a stepped drag and
    generous dwell times - retrying with a fresh verification check is
    more robust than any single fixed offset/timing combination found.
    """
    print("[STEP] Opening Application menu -> New -> Equation Set")

    def _verify(app_obj):
        title = app_obj.get_window().window_text()
        return "Equation" in title and get_list(app_obj) is not None

    open_new_document_verified(app_obj, _NEW_FLYOUT_EQUATION_SET_INDEX, _verify, timeout=timeout)
    print(f"[INFO] New Equation Set file created: {app_obj.get_window().window_text()!r}")


def get_equation_set_rows(app_obj):
    """
    Read all rows currently shown in the Equation Set view (e.g.
    "USERBOOL1 = 1", "USERBOOL2 = 2", ...). Live-confirmed: this is a plain
    SysListView32, same as Config Directory/Driver Database views, so the
    existing get_list/get_list_row_texts primitives apply unchanged.
    """
    lst = get_list(app_obj)
    return [get_list_row_texts(lst, i) for i in range(lst.item_count())]


def insert_equation_line(app_obj, register_number, expression):
    """
    E2 steps 1-2: Click ribbon "Insert" to open the "Edit Equation Line"
    dialog, choose "User BOOLEAN register..." as the result type, set
    `register_number` (so the result target becomes USERBOOLn), enter
    `expression` in the "Use this expression to..." text area, and OK -
    producing a new row reading "USERBOOL{register_number} = {expression}".
    """
    uia_win = app_obj.get_uia_window()
    print("[STEP] Clicking ribbon 'Insert'")
    click_ribbon_button(uia_win, "Insert")
    time.sleep(1.0)

    dlg_spec = app_obj.app.window(
        title=_EDIT_EQUATION_LINE_DIALOG_TITLE, class_name=_EDIT_EQUATION_LINE_DIALOG_CLASS
    )
    dlg_spec.wait("exists visible ready", timeout=10)
    win32_dlg = dlg_spec.wrapper_object()
    hwnd = win32_dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

    # NOTE: UIA's combo.expand()/children() did NOT reliably enumerate the
    # real option list in live testing - use the win32 ComboBoxWrapper's
    # .select(text) instead, matched by control_id.
    combo = next(
        d for d in win32_dlg.descendants(class_name="ComboBox")
        if str(d.control_id()) == _EDIT_EQUATION_LINE_RESULT_TYPE_COMBO_AUTO_ID
    )
    combo.select(_USER_BOOL_REGISTER_OPTION)
    time.sleep(0.3)

    reg_edit = uia_dlg.child_window(
        auto_id=_EDIT_EQUATION_LINE_REGISTER_NUMBER_AUTO_ID, control_type="Edit"
    )
    reg_edit.click_input()
    send_keys("^a")
    send_keys(str(register_number))
    time.sleep(0.2)

    expr_edit = uia_dlg.child_window(
        auto_id=_EDIT_EQUATION_LINE_EXPRESSION_EDIT_AUTO_ID, control_type="Edit"
    )
    expr_edit.click_input()
    send_keys("^a")
    send_keys(str(expression))
    time.sleep(0.2)

    print(f"[INFO] Setting USERBOOL{register_number} = {expression}")
    uia_dlg.child_window(auto_id=_EDIT_EQUATION_LINE_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.8)


def upload_equation_file(app_obj, file_path):
    """
    E4: Upload an Equation File (.al4equ) to a connected AccuLoad via the
    ribbon "Upload File to AccuLoad" button's "AccuMate File Transfer"
    window.

    NOT YET IMPLEMENTED - needs live device access plus a live probe of the
    "AccuMate File Transfer" dialog's controls (shared gap with
    driver_db_workflows.upload_driver_database_file). See module docstring
    "Remaining gaps".
    """
    raise NotImplementedError(
        "E4: 'AccuMate File Transfer' upload dialog has no existing "
        "workflow in this repo and needs live device access plus a live "
        "probe of its controls before this can be implemented."
    )


def download_equation_file(app_obj, save_path):
    """
    E5/E6: Download an Equation File from a connected AccuLoad via the
    ribbon "Download File From AccuLoad" button.

    NOT YET IMPLEMENTED - see upload_equation_file's docstring; same gap.
    """
    raise NotImplementedError(
        "E5/E6: 'AccuMate File Transfer' download dialog has no existing "
        "workflow in this repo and needs live device access plus a live "
        "probe of its controls before this can be implemented."
    )
