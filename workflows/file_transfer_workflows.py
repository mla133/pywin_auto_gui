"""
Shared workflow for the "AccuMate File Transfer" dialog family - drives
uploading a file TO a connected AccuLoad IV device and downloading a file
FROM one. This is the shared mechanism behind regression.md's B4-B10/B13-14
(Report Files), C4-C6 (Translation Files), D6-D8 (Driver Database Files),
E4-E6/E8 (Equations File), and F1-F8 (Transaction/Event/Audit Trail Log,
License Status File) sections - every one of those steps ultimately clicks
the ribbon's "Upload File to AccuLoad"/"Download File From AccuLoad" button
and drives the same dialog(s) documented here.

LIVE-PROBED against a real AccuLoad IV at 10.55.66.70 (reachable via TCP
port 7734 - this device's Smith protocol does not respond to ICMP ping, so
use `Test-NetConnection -ComputerName <ip> -Port 7734` to check reachability,
never a plain ping).

*** Dialog flow discovered live ***

1. Upload: clicking ribbon "Upload File to AccuLoad" goes STRAIGHT to the
   "AccuMate File Transfer" dialog (see below) - the file's own extension
   presumably tells AccuMate what kind of upload it is, so there's no
   separate category-selection step.

2. Download: clicking ribbon "Download File From AccuLoad" first opens a
   **"File Download Selection"** dialog (class "#32770") - a group of radio
   buttons (grouped visually into "Logs"/"Configurations"/"Miscellaneous",
   though those group buttons are NOT clickable - id -1) plus OK (id 1) /
   Cancel (id 2):
       Transaction Log       id 1022
       Event Log             id 1029
       Audit Trail Log       id 1024
       Equations File        id 1025
       Report Files          id 1026
       Driver Database File  id 1027
       Translation File      id 1028
       License Status File   id 1023
   Selecting a radio then clicking OK (id 1) opens the SAME "AccuMate File
   Transfer" dialog as Upload, but with its Static label (id 1009) reading
   "Please select save location:" instead of "Please select upload file:".

3. "AccuMate File Transfer" dialog (class "#32770", title "AccuMate File
   Transfer") - identical control layout for both directions:
       id 1009 (Static)         "Please select upload file:" / "Please
                                 select save location:"
       id 1007 (Edit)           the file path (read-only from the user's
                                 perspective in practice - see gotcha below)
       id 1003 (Button)         "Browse..."
       id 1010 (Button)         "Start" (label flips to "Cancel" once a
                                 transfer is in progress) - DISABLED until
                                 a path has been set via Browse (see gotcha)
       id 1013 (ProgressBar)    msctls_progress32
       id 1018 (Static)         "Status:" (fixed label)
       id 1017 (Static)         live status text - "Ready" before starting,
                                 "Connected / Ready" once a transfer is
                                 underway/connected
       id 1011 (Button)         "Exit" - closes the dialog

*** CRITICAL GOTCHA: "Start" only enables via the Browse... dialog ***
Programmatically setting the id-1007 Edit control's text directly (e.g.
`set_edit_text(path)`) does NOT enable the "Start" button, even though the
Edit control's text visibly updates. AccuMate's own dialog handler appears
to gate "Start" on a member variable set only inside its Browse button's
own OnBrowse handler (i.e. on the underlying common Open/Save dialog's own
commit event), not on the Edit control's OnChange. Confirmed live,
repeatedly. **Always drive the path via the Browse... button + the native
common dialog it opens, never by writing directly into the Edit control.**
The Browse dialog itself is a standard Explorer-style common dialog:
  - For Upload, Browse opens a standard **Open** dialog - use automation_id
    "1148" for the filename Edit and "1" for the commit ("Open") button,
    same convention as workflows.file_workflows.open_file_dialog.
  - For Download, Browse opens a standard **Save As** dialog - use
    automation_id "1001" for the filename Edit (a ComboBox-hosted edit, NOT
    "1148" - that id doesn't exist in this variant) and "1" for the commit
    ("Save") button. An overwrite confirmation (`&Yes`/id 6) may follow if
    the target file already exists, same pattern as
    workflows.file_workflows.save_as's overwrite handling.

*** Status polling gotcha: the app's UI thread can go unresponsive during
a real transfer ***
While a transfer is actively running, ALL of AccuMate's own window
titles/control texts observed via `window_text()` can return **empty
strings** for several seconds at a time (confirmed live) - this is the
app's UI thread being busy servicing the socket, not a hung/crashed
process. Don't treat a single blank read as a failure; keep polling.

*** LIVE FINDING (environment limitation, not an automation bug): the test
device at 10.55.66.70 consistently returned "The operation timed out" (a
plain "AccuMate" message box, class "#32770", with an "OK" button at
control id 2 and the message itself in a Static at control id 65535) for
EVERY download category tried (Driver Database File, Transaction Log) after
~60-90s, despite `AccuMateApp.is_device_connected()` reporting a live
connection throughout. This is a DIFFERENT failure mode than regression.md's
documented "no information to pull from the AccuLoad" warning (an expected,
different popup for several B/C/D/E sections when a category is genuinely
empty on the device) - a timeout suggests the file-transfer data channel
itself isn't reachable/enabled on this device/network path, even though the
Smith protocol control channel (port 7734) is. Live-verifying D6-D8/F1-F8/
B4-B10/B13-14/E4-E6/E8 end-to-end (i.e. an ACTUAL successful transfer, not
just this dialog automation) may require a device/network configuration
change outside this repo's control. The dialog automation itself (up
through clicking Start and observing the resulting status/message) is
verified correct independent of that.
"""
import os
import time

from pywinauto import Application

from controls.ribbon_controls import click_ribbon_button, find_ribbon_button, is_ribbon_button_enabled

_FILE_TRANSFER_DIALOG_TITLE = "AccuMate File Transfer"
_DOWNLOAD_SELECTION_DIALOG_TITLE = "File Download Selection"
_DIALOG_CLASS = "#32770"

# Control IDs inside the "AccuMate File Transfer" dialog - stable regardless
# of direction (upload/download) or which file category was selected.
_PATH_EDIT_ID = 1007
_BROWSE_BUTTON_ID = 1003
_START_BUTTON_ID = 1010
_EXIT_BUTTON_ID = 1011
_STATUS_TEXT_ID = 1017

# "File Download Selection" dialog's per-category radio button control IDs
# (see module docstring). Matches regression.md's B/C/D/E/F section category
# names verbatim.
DOWNLOAD_CATEGORY_IDS = {
    "Transaction Log": 1022,
    "Event Log": 1029,
    "Audit Trail Log": 1024,
    "Equations File": 1025,
    "Report Files": 1026,
    "Driver Database File": 1027,
    "Translation File": 1028,
    "License Status File": 1023,
}
_DOWNLOAD_OK_BUTTON_ID = 1
_DOWNLOAD_CANCEL_BUTTON_ID = 2

# Standard Windows common-dialog automation ids (see module docstring
# gotcha) - same convention as workflows.file_workflows.open_file_dialog/
# save_as.
_OPEN_DIALOG_FILENAME_AUTO_ID = "1148"
_SAVE_DIALOG_FILENAME_AUTO_ID = "1001"
_COMMON_DIALOG_COMMIT_AUTO_ID = "1"
_OVERWRITE_CONFIRM_YES_ID = 6


def _find_dialog_by_title(app_obj, title):
    for w in app_obj.app.windows():
        try:
            if w.window_text() == title and w.class_name() == _DIALOG_CLASS:
                return w
        except Exception:
            continue
    return None


def _find_child_by_id(win32_wrapper, control_id):
    for ctrl in win32_wrapper.children(recurse=True):
        try:
            if ctrl.control_id() == control_id:
                return ctrl
        except Exception:
            continue
    return None


def _wait_for_dialog(app_obj, title, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        dlg = _find_dialog_by_title(app_obj, title)
        if dlg is not None:
            return dlg
        time.sleep(0.5)
    raise RuntimeError(f"'{title}' dialog did not appear within {timeout}s")


def open_upload_dialog(app_obj, timeout=10):
    """
    Click the ribbon "Upload File to AccuLoad" button and return the
    resulting "AccuMate File Transfer" dialog (win32 wrapper). Raises if the
    ribbon button is disabled (device not connected) or the dialog never
    appears.
    """
    uia_win = app_obj.get_uia_window()
    if not is_ribbon_button_enabled(uia_win, "Upload File to AccuLoad"):
        raise RuntimeError(
            "'Upload File to AccuLoad' ribbon button is disabled - device "
            "likely not connected."
        )

    print("[STEP] Clicking ribbon 'Upload File to AccuLoad'")
    click_ribbon_button(uia_win, "Upload File to AccuLoad")

    return _wait_for_dialog(app_obj, _FILE_TRANSFER_DIALOG_TITLE, timeout=timeout)


def open_download_dialog(app_obj, category, timeout=10):
    """
    Click the ribbon "Download File From AccuLoad" button, select
    `category` (a key of DOWNLOAD_CATEGORY_IDS, e.g. "Transaction Log",
    "Driver Database File") in the "File Download Selection" dialog, click
    OK, and return the resulting "AccuMate File Transfer" dialog (win32
    wrapper).

    Raises if the ribbon button is disabled, `category` is not a known key,
    or either dialog never appears.
    """
    if category not in DOWNLOAD_CATEGORY_IDS:
        raise ValueError(
            f"Unknown download category {category!r}; expected one of "
            f"{sorted(DOWNLOAD_CATEGORY_IDS)}"
        )

    uia_win = app_obj.get_uia_window()
    if not is_ribbon_button_enabled(uia_win, "Download File From AccuLoad"):
        raise RuntimeError(
            "'Download File From AccuLoad' ribbon button is disabled - "
            "device likely not connected."
        )

    print(f"[STEP] Clicking ribbon 'Download File From AccuLoad', selecting {category!r}")
    click_ribbon_button(uia_win, "Download File From AccuLoad")

    selection_dlg = _wait_for_dialog(app_obj, _DOWNLOAD_SELECTION_DIALOG_TITLE, timeout=timeout)
    radio = _find_child_by_id(selection_dlg, DOWNLOAD_CATEGORY_IDS[category])
    if radio is None:
        raise RuntimeError(f"Radio button for category {category!r} not found")
    radio.click_input()
    time.sleep(0.3)

    ok_btn = _find_child_by_id(selection_dlg, _DOWNLOAD_OK_BUTTON_ID)
    if ok_btn is None:
        raise RuntimeError("OK button not found on 'File Download Selection' dialog")
    ok_btn.click_input()

    return _wait_for_dialog(app_obj, _FILE_TRANSFER_DIALOG_TITLE, timeout=timeout)


def set_upload_file_path(transfer_dlg, file_path, timeout=10):
    """
    Set the file to upload via the "Browse..." button (opens a standard
    Open dialog) - see module docstring gotcha for why this must go through
    Browse rather than writing to the Edit control directly.
    """
    _browse_and_set_path(
        transfer_dlg, file_path, is_save=False, timeout=timeout
    )


def set_download_save_path(transfer_dlg, save_path, timeout=10):
    """
    Set the local save location for a download via the "Browse..." button
    (opens a standard Save As dialog) - see module docstring gotcha.
    """
    _browse_and_set_path(
        transfer_dlg, save_path, is_save=True, timeout=timeout
    )


def _browse_and_set_path(transfer_dlg, path, is_save, timeout):
    browse_btn = _find_child_by_id(transfer_dlg, _BROWSE_BUTTON_ID)
    if browse_btn is None:
        raise RuntimeError("'Browse...' button not found on File Transfer dialog")
    browse_btn.click_input()

    common_dlg_title = "Save As" if is_save else "Open"

    # Search all top-level windows for the common dialog by title (dual
    # win32+uia pattern, see workflows.file_workflows.open_file_dialog).
    app = Application(backend="win32").connect(process=transfer_dlg.process_id())
    common_dlg = None
    end = time.time() + timeout
    while time.time() < end and common_dlg is None:
        for w in app.windows():
            try:
                if w.window_text() == common_dlg_title and w.class_name() == _DIALOG_CLASS:
                    common_dlg = w
                    break
            except Exception:
                continue
        if common_dlg is None:
            time.sleep(0.3)

    if common_dlg is None:
        raise RuntimeError(
            f"'{common_dlg_title}' dialog did not appear within {timeout}s after clicking Browse..."
        )

    hwnd = common_dlg.handle
    uia_app = Application(backend="uia").connect(handle=hwnd)
    uia_dlg = uia_app.window(handle=hwnd)

    auto_id = _OPEN_DIALOG_FILENAME_AUTO_ID if not is_save else _SAVE_DIALOG_FILENAME_AUTO_ID
    filename_edit = uia_dlg.child_window(auto_id=auto_id, control_type="Edit")
    filename_edit.set_edit_text(path)
    time.sleep(0.3)

    commit_btn = uia_dlg.child_window(auto_id=_COMMON_DIALOG_COMMIT_AUTO_ID, control_type="Button")
    commit_btn.click_input()
    time.sleep(0.5)

    # Handle an overwrite confirmation, if any (Save As only).
    if is_save:
        try:
            for w in app.windows():
                try:
                    if w.window_text() and "Confirm" in w.window_text():
                        yes_btn = _find_child_by_id(w, _OVERWRITE_CONFIRM_YES_ID)
                        if yes_btn is not None:
                            yes_btn.click_input()
                            time.sleep(0.5)
                except Exception:
                    continue
        except Exception:
            pass


def start_transfer(transfer_dlg, timeout=90, poll_interval=2):
    """
    Click "Start" on an "AccuMate File Transfer" dialog (path must already
    be set via set_upload_file_path/set_download_save_path - Start stays
    disabled otherwise) and poll until either:
      - a plain "AccuMate" message box appears (success/warning/error - see
        below), or
      - `timeout` seconds elapse with no such message box.

    Returns a dict: {"message": str or None, "timed_out": bool}. `message`
    is the text of the "AccuMate" popup if one appeared (e.g. "The
    operation timed out", or regression.md's expected "...no information to
    pull from the AccuLoad..." warning for an empty category) - the caller
    is responsible for interpreting that text against what the specific
    regression.md step expects, since both a real success confirmation and
    several different expected warnings/errors surface through this same
    generic message box. Never raises for a transfer-level failure (e.g. a
    device timeout) - only for automation-level failures (Start not found/
    still disabled).

    NOTE: while a transfer is actively running, ALL of AccuMate's own
    window texts (including this dialog's own controls) can transiently
    return empty strings for several seconds - the app's UI thread is busy
    servicing the socket, not hung. This polls tolerantly for that.
    """
    start_btn = _find_child_by_id(transfer_dlg, _START_BUTTON_ID)
    if start_btn is None:
        raise RuntimeError("'Start' button not found on File Transfer dialog")
    if not start_btn.is_enabled():
        raise RuntimeError(
            "'Start' button is disabled - did you set the path via "
            "set_upload_file_path/set_download_save_path (which drives the "
            "Browse... dialog) rather than writing to the Edit control "
            "directly? See module docstring gotcha."
        )

    print("[STEP] Clicking 'Start'")
    start_btn.click_input()

    app = Application(backend="win32").connect(process=transfer_dlg.process_id())
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(poll_interval)
        for w in app.windows():
            try:
                if w.window_text() == "AccuMate" and w.class_name() == _DIALOG_CLASS:
                    message = None
                    for ctrl in w.children(recurse=True):
                        try:
                            if ctrl.control_id() == 65535:
                                message = ctrl.window_text().strip()
                                break
                        except Exception:
                            continue
                    print(f"[INFO] 'AccuMate' message box appeared: {message!r}")
                    return {"message": message, "timed_out": False}
            except Exception:
                continue

    print(f"[WARN] No completion message box appeared within {timeout}s")
    return {"message": None, "timed_out": True}


def dismiss_message_box(app_obj):
    """
    Click OK on the plain "AccuMate" message box left open by
    start_transfer (if any). Safe to call even if none is open.
    """
    dlg = _find_dialog_by_title(app_obj, "AccuMate")
    if dlg is None:
        return
    for ctrl in dlg.children(recurse=True):
        try:
            if ctrl.class_name() == "Button":
                ctrl.click_input()
                time.sleep(0.3)
                return
        except Exception:
            continue


def close_transfer_dialog(transfer_dlg):
    """Click "Exit" to close an "AccuMate File Transfer" dialog."""
    exit_btn = _find_child_by_id(transfer_dlg, _EXIT_BUTTON_ID)
    if exit_btn is None:
        raise RuntimeError("'Exit' button not found on File Transfer dialog")
    exit_btn.click_input()
    time.sleep(0.5)


def upload_file(app_obj, file_path, timeout=90):
    """
    High-level helper: open the Upload File Transfer dialog, set
    `file_path`, click Start, wait for a result message, then close the
    dialog. Returns the same dict as start_transfer(). Dismisses any
    trailing "AccuMate" message box and the transfer dialog itself before
    returning, regardless of outcome.
    """
    dlg = open_upload_dialog(app_obj)
    try:
        set_upload_file_path(dlg, file_path)
        result = start_transfer(dlg, timeout=timeout)
        return result
    finally:
        dismiss_message_box(app_obj)
        try:
            close_transfer_dialog(dlg)
        except Exception as e:
            print(f"[WARN] Failed to close File Transfer dialog: {e}")


def download_file(app_obj, category, save_path, timeout=90):
    """
    High-level helper: open the Download File Transfer dialog for
    `category` (see DOWNLOAD_CATEGORY_IDS), set `save_path`, click Start,
    wait for a result message, then close the dialog. Returns the same
    dict as start_transfer(). Dismisses any trailing "AccuMate" message box
    and the transfer dialog itself before returning, regardless of outcome.
    """
    dlg = open_download_dialog(app_obj, category)
    try:
        set_download_save_path(dlg, save_path)
        result = start_transfer(dlg, timeout=timeout)
        return result
    finally:
        dismiss_message_box(app_obj)
        try:
            close_transfer_dialog(dlg)
        except Exception as e:
            print(f"[WARN] Failed to close File Transfer dialog: {e}")
