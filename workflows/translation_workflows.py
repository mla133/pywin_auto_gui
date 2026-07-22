"""
Translation document type workflows (scenarios/regression.md C1-C7).

C1-C3 are LIVE-VERIFIED against the real running app (control ids, dialog
title, and the "New" fly-out mechanism all confirmed live - see
workflows/file_workflows.py's _click_new_document_flyout_item for the
fly-out mechanism itself, now keyboard-navigation-based). C4-C7 remain
unimplemented - see the "Remaining gaps" section below.

Live-verified findings:
  - Selecting "Translation" from the "New" fly-out creates a new document
    titled "Lang<n> - AccuMate for AccuLoad" with a two-column
    SysListView32 grid (column 0: the English source text, column 1: the
    translated text, initially blank) - same get_list/get_list_row_texts
    primitives used elsewhere in this repo for Config Directory/Driver
    Database/Equation Set listviews work unchanged here. Live-confirmed
    the grid has ~4696 rows (every translatable string in the app).
  - Double-clicking a grid row opens the "Edit Text" dialog (title
    confirmed exact, class "#32770") with these real automation_ids:
    - Edit control auto_id=1015: read-only "Original Text:" (English)
    - Edit control auto_id=1014: editable "New Text:" (the translation)
    - Button auto_id=1: OK
    - Button auto_id=2: Cancel
  - Reading Edit control values reliably requires the win32 backend's
    descendants(class_name="Edit") + .window_text() (matched by
    .control_id()), same as workflows/driver_db_workflows.py's
    _read_edit_field - the UIA backend was unreliable for these fields in
    this app in prior live testing of other document types.

Remaining gaps (NOT yet implemented/verified):
  - C4 (Upload)/C5 (Download)/C6 (No file to download): need a live,
    reachable AccuLoad device AND a not-yet-built "AccuMate File
    Transfer" upload/download dialog workflow (same gap documented in
    workflows/driver_db_workflows.py and workflows/equation_workflows.py
    for D6-D8/E4-E6).
  - C7: needs a provided AM3-format Translation File (.LGX) that does not
    currently exist in this repo/environment - same class of blocker as
    D9/E7/H3-H8's provided files.
"""

import time

from pywinauto.keyboard import send_keys
from pywinauto import Application

from controls.common_controls import get_list, get_list_row_texts
from workflows.file_workflows import (
    _click_new_document_flyout_item,
    _NEW_FLYOUT_TRANSLATION_INDEX,
    open_new_document_verified,
)

_EDIT_TEXT_DIALOG_TITLE = "Edit Text"
_EDIT_TEXT_DIALOG_CLASS = "#32770"
_EDIT_TEXT_ORIGINAL_AUTO_ID = "1015"
_EDIT_TEXT_NEW_TEXT_AUTO_ID = "1014"
_EDIT_TEXT_OK_AUTO_ID = "1"
_EDIT_TEXT_CANCEL_AUTO_ID = "2"

_NEW_TRANSLATION_TIMEOUT = 20


def create_new_translation_file(app_obj, timeout=_NEW_TRANSLATION_TIMEOUT):
    """
    C1: Creating New Translation Files.

    regression.md: "Click the top left circle button then hover your
    mouse over 'New'... Click on 'Translation'." -> a new Translation view
    (titled "Lang<n> - AccuMate for AccuLoad") is displayed with a
    populated grid of translatable strings.

    Uses open_new_document_verified() rather than a single fly-out click -
    see workflows/file_workflows.py and workflows/equation_workflows.py
    for why (the fly-out's per-item hit-testing was found to be flaky).
    """
    print("[STEP] Opening Application menu -> New -> Translation")

    def _verify(app_obj):
        title = app_obj.get_window().window_text()
        return "Lang" in title and get_list(app_obj).item_count() >= 1

    open_new_document_verified(app_obj, _NEW_FLYOUT_TRANSLATION_INDEX, _verify, timeout=timeout)
    print(f"[INFO] New Translation file created: {app_obj.get_window().window_text()!r}")


def get_translation_rows(app_obj):
    """
    Read all rows currently shown in the Translation grid view (English
    source text, translated text).
    """
    lst = get_list(app_obj)
    return [get_list_row_texts(lst, i) for i in range(lst.item_count())]


def _get_dialog(app_obj, title, class_name, timeout=10):
    dlg_spec = app_obj.app.window(title=title, class_name=class_name)
    dlg_spec.wait("exists visible ready", timeout=timeout)
    win32_dlg = dlg_spec.wrapper_object()
    hwnd = win32_dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)
    return win32_dlg, uia_dlg


def open_edit_text_dialog(app_obj, row_index=0):
    """
    C2 step 1: Double-click a Translation grid row to open the
    "Edit Text" dialog. Returns (win32_dlg, uia_dlg) - the win32 wrapper
    is used for reliable text reads, the uia wrapper for automation_id-
    based control lookups.
    """
    lst = get_list(app_obj)

    if row_index >= lst.item_count():
        raise RuntimeError(
            f"Translation grid only has {lst.item_count()} row(s), "
            f"cannot open row {row_index}"
        )

    item = lst.get_item(row_index)
    item.select()

    rect = item.rectangle()
    x = rect.left + 60
    y = rect.top + rect.height() // 2

    print(f"[INFO] Opening 'Edit Text' dialog for row {row_index}")
    lst.click_input(coords=(x, y))
    lst.click_input(coords=(x, y), double=True)

    return _get_dialog(app_obj, _EDIT_TEXT_DIALOG_TITLE, _EDIT_TEXT_DIALOG_CLASS)


def set_translation_text(uia_dlg, new_text):
    """
    C2 step 1: enter a value into the "New Text:" field of an open
    "Edit Text" dialog and click OK.
    """
    edit = uia_dlg.child_window(auto_id=_EDIT_TEXT_NEW_TEXT_AUTO_ID, control_type="Edit")
    edit.click_input()
    time.sleep(0.15)
    send_keys("^a")
    send_keys(str(new_text).replace(" ", "{SPACE}"))
    time.sleep(0.15)

    uia_dlg.child_window(auto_id=_EDIT_TEXT_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.5)


def enter_translation_for_row(app_obj, row_index, new_text):
    """Convenience wrapper: open the Edit Text dialog for `row_index` and
    set its New Text value in one call (C2 step 1's repeated action)."""
    win32_dlg, uia_dlg = open_edit_text_dialog(app_obj, row_index)
    set_translation_text(uia_dlg, new_text)
