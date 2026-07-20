import time
import os

from pypdf import PdfReader
from pywinauto import Application, Desktop

from workflows.file_workflows import _click_app_menu_item

# Print(5) in the Application Button's backstage menu (see file_workflows.py
# for the full item order/coordinate-click mechanics - the popup is entirely
# custom-drawn, so items are clicked by coordinate, not found via UIA).
_APP_MENU_PRINT_INDEX = 5

_PRINT_DIALOG_TITLE = "Print"
_PRINT_DIALOG_CLASS = "#32770"
_PRINTER_NAME_COMBOBOX_ID = 1139
_PRINT_OK_BUTTON_ID = 1
_MICROSOFT_PRINT_TO_PDF = "Microsoft Print to PDF"

_SAVE_DIALOG_TITLE_RE = ".*Save Print Output As.*"
_SAVE_DIALOG_CLASS = "#32770"
_SAVE_FILENAME_AUTO_ID = "1001"
_SAVE_BUTTON_AUTO_ID = "1"

# Once "Microsoft Print to PDF" is confirmed, AccuMate shows its own
# "Printing" status window (title exactly "AccuMate", class "#32770",
# distinguishable from every other #32770 dialog only by process+title -
# confirmed live) while it spools the document; this closes on its own once
# spooling finishes.
_PRINTING_STATUS_TITLE = "AccuMate"


def _find_by_control_id(dlg, control_id):
    for ctrl in dlg.descendants():
        try:
            if ctrl.control_id() == control_id:
                return ctrl
        except Exception:
            continue
    raise RuntimeError(f"Control with control_id={control_id} not found")


def _remove_existing_file(pdf_path, timeout=60):
    """
    Remove `pdf_path` if it exists, retrying briefly. A file left over from
    a prior print can still be held open for a while after the previous
    print's status window has closed and its own %%EOF marker has already
    appeared - confirmed live, this is Windows Defender's real-time
    protection (MsMpEng) transiently locking the freshly-written PDF to
    scan it, not the print spooler itself (no spooler process was even
    running at the time of a reproduced lock). A generous retry budget is
    needed since a Defender scan of a multi-hundred-page PDF can take
    upwards of 30+ seconds.
    """
    if not os.path.exists(pdf_path):
        return

    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            os.remove(pdf_path)
            return
        except (PermissionError, OSError) as e:
            last_error = e
            time.sleep(1)

    raise RuntimeError(f"Could not remove stale file before printing: {pdf_path}") from last_error


def _is_printing_status_window_open(app_obj, pid):
    try:
        windows = Desktop(backend="win32").windows()
    except Exception:
        # A window can close mid-enumeration (race with the printing status
        # window itself closing) - treat as "can't tell right now", not a
        # hard failure; the caller just polls again shortly after.
        return True

    for w in windows:
        try:
            if (
                w.process_id() == pid
                and w.class_name() == _SAVE_DIALOG_CLASS
                and w.window_text() == _PRINTING_STATUS_TITLE
            ):
                return True
        except Exception:
            continue
    return False


def _wait_for_file_ready(pdf_path, timeout):
    """
    Poll until `pdf_path` exists, can be opened exclusively, AND its last
    bytes contain the "%%EOF" trailer marker that terminates a complete PDF
    file. "Microsoft Print to PDF" creates the file immediately but the
    print spooler (splwow64, since AccuMate is a 32-bit app) keeps writing
    to/re-locking it for a while afterward - live testing against a real
    ~250-page AccuMate config printout showed the file stays intermittently
    locked (PermissionError) for ~30s after the app-level "Printing" status
    window closes, and even once briefly unlocked/openable, its content can
    still be mid-write; checking for a trailing "%%EOF" is what actually
    confirms the PDF writer has finished, not just that no process
    currently holds a lock at that instant.
    Raises RuntimeError if the file never becomes ready in time.
    """
    start = time.time()

    while time.time() - start < timeout:
        if os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 0:
            try:
                with open(pdf_path, "rb") as f:
                    f.seek(-32, os.SEEK_END)
                    tail = f.read()
                if b"%%EOF" in tail:
                    if _is_valid_pdf(pdf_path):
                        return
            except (PermissionError, OSError):
                pass
        time.sleep(1)

    raise RuntimeError(f"Printed PDF never became ready for reading: {pdf_path}")


def _is_valid_pdf(pdf_path):
    """
    Confirm `pdf_path` is a fully-written, parseable PDF (not just a file
    whose last bytes happen to contain "%%EOF" while still mid-write) by
    actually loading it with pypdf and touching every page's text - live
    testing showed a %%EOF-only check can still pass against a PDF that
    parses "successfully" but returns truncated/empty page text for pages
    still being flushed to disk, causing spurious text-search failures
    downstream.
    """
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            return False
        for page in reader.pages:
            page.extract_text()
        return True
    except Exception:
        return False



def _open_print_dialog(app_obj, retries=3):
    """
    Open the ribbon Application Button -> "Print" menu item and wait for
    the resulting "Print" common dialog. Retries a few times since - like
    every other Application Button item in this codebase - the coordinate
    click can occasionally miss (confirmed live: a back-to-back A26 run
    opening Print 5 times in a row hit a TimeoutError on one iteration
    without a retry here).
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            print("[STEP] Opening Application menu -> Print")
            _click_app_menu_item(app_obj, _APP_MENU_PRINT_INDEX)

            print_dlg_spec = app_obj.app.window(title=_PRINT_DIALOG_TITLE, class_name=_PRINT_DIALOG_CLASS)
            print_dlg_spec.wait("exists enabled visible ready", timeout=8)

            return print_dlg_spec
        except Exception as e:
            last_error = e
            print(f"[WARN] Attempt {attempt}/{retries} to open Print dialog failed: {e}")
            try:
                app_obj.get_window().type_keys("{ESC}")
            except Exception:
                pass
            time.sleep(1)

    raise RuntimeError(f"Failed to open Print dialog after {retries} attempts") from last_error


def print_to_pdf(app_obj, pdf_path, timeout=180):
    """
    Print the currently-open AccuMate document to a PDF file via the
    ribbon's Application Button -> "Print" menu item, selecting the
    "Microsoft Print to PDF" printer and saving to `pdf_path`.

    Overwrites `pdf_path` if it already exists (Microsoft Print to PDF's own
    save dialog would otherwise prompt to overwrite, which this doesn't
    currently handle - callers should use a fresh/unique path per print).
    """
    pdf_path = os.path.normpath(pdf_path)
    directory = os.path.dirname(pdf_path)
    if directory and not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    _remove_existing_file(pdf_path)

    pid = app_obj.get_window().process_id()

    print_dlg_spec = _open_print_dialog(app_obj)
    print_dlg = print_dlg_spec.wrapper_object()

    printer_combo = _find_by_control_id(print_dlg, _PRINTER_NAME_COMBOBOX_ID)
    printer_combo.select(_MICROSOFT_PRINT_TO_PDF)

    print(f"[STEP] Printing to '{pdf_path}' via {_MICROSOFT_PRINT_TO_PDF}")
    _find_by_control_id(print_dlg, _PRINT_OK_BUTTON_ID).click_input()

    save_dlg_spec = app_obj.app.window(title_re=_SAVE_DIALOG_TITLE_RE, class_name=_SAVE_DIALOG_CLASS)
    save_dlg_spec.wait("exists enabled visible ready", timeout=10)
    hwnd = save_dlg_spec.wrapper_object().handle

    uia_app = Application(backend="uia").connect(handle=hwnd)
    uia_dlg = uia_app.window(handle=hwnd)
    uia_dlg.child_window(auto_id=_SAVE_FILENAME_AUTO_ID, control_type="Edit").set_edit_text(pdf_path)
    uia_dlg.child_window(auto_id=_SAVE_BUTTON_AUTO_ID, control_type="Button").click_input()

    # Wait for AccuMate's own "Printing" status window to close (spooling in
    # progress), then separately for the PDF file itself to be fully
    # written and readable (see _wait_for_file_ready) - these are given
    # independent timeout budgets since AccuMate always prints the entire
    # config (~250 pages for a blank new document; tree-node selection does
    # NOT scope the printout, confirmed live), which can take well over a
    # minute end-to-end, and the spooler keeps intermittently re-locking the
    # file well after the status window itself has already closed.
    start = time.time()
    while time.time() - start < timeout and _is_printing_status_window_open(app_obj, pid):
        time.sleep(1)

    _wait_for_file_ready(pdf_path, timeout=timeout)

    print(f"[INFO] Printed to PDF: {pdf_path}")
    return pdf_path
