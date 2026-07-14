import time
import os
from pywinauto.keyboard import send_keys
from pywinauto import Application

from controls.ribbon_controls import find_app_button

TEST_FILE = os.path.normpath(
    r"C:\\Users\\allenma\\Documents\\Testing\\Auto_Test.AL4"
    )

# The Application Button's backstage menu is entirely custom-drawn (no UIA
# text/automation_id exposed for any of its items - a `.descendants()` scan
# of the popup's own HWNDs after opening returns 0 elements), so items must
# be clicked by coordinate. These offsets are relative to the Application
# Button's own rectangle (found via UIA, see find_app_button), which keeps
# them correct regardless of the main window's position/size on screen.
_APP_MENU_ITEM_X_OFFSET = 85
_APP_MENU_FIRST_ITEM_Y_OFFSET = 27  # from button bottom, to the "New" item
_APP_MENU_ITEM_ROW_HEIGHT = 52
# Menu item order: New(0), Open...(1), Save(2), Save As...(3)
_APP_MENU_SAVE_AS_INDEX = 3

_SAVE_AS_DIALOG_TITLE = "Save As"
_SAVE_AS_DIALOG_CLASS = "#32770"
_SAVE_AS_FILENAME_AUTO_ID = "1001"
_SAVE_AS_SAVE_BUTTON_AUTO_ID = "1"

def open_file_dialog(app_obj, file_path):
    win = app_obj.get_window()
    win.set_focus()

    print("[DEBUG] Triggering Ctrl-O")
    win.type_keys("^o", set_foreground=True)

    time.sleep(0.5)

    # Step 1: Attach to the dialog using Win32 backend
    dlg = app_obj.app.window(class_name="#32770")
    dlg.wait("visible enabled ready", timeout=10)

    # Get the HWND of the dialog
    hwnd = dlg.handle

    print(f"[DEBUG] Dialog HWND = {hex(hwnd)}")

    # Step 2: Attach to the SAME dialog using UIA backend
    uia_app = Application(backend="uia").connect(handle=hwnd)
    uia_dlg = uia_app.window(handle=hwnd)

    print("[DEBUG] Locating filename edit box via UIA")

    # Step 3: Find the Edit control under UIA.
    # NOTE: a plain control_type="Edit" lookup is ambiguous in modern
    # Explorer-style Open dialogs (list view column headers, the search box,
    # etc. are also exposed as Edit controls). automation_id "1148" is the
    # standard Windows common-dialog id for the filename edit box and is
    # unique regardless of how many items/columns are shown.
    filename_edit = uia_dlg.child_window(auto_id="1148", control_type="Edit")

    if not filename_edit.exists():
        raise RuntimeError("UIA Edit control not found in file dialog")

    filename_edit.set_edit_text(file_path)

    print("[DEBUG] Clicking Open")
    # NOTE: title="Open" alone is ambiguous — the "Open" split-button
    # dropdown arrows on the list view items also expose that title. The
    # real dialog commit button is automation_id "1" (standard Windows
    # common-dialog IDOK).
    uia_dlg.child_window(auto_id="1", control_type="Button").click_input()

def load_test_file(app_obj):
    open_file_dialog(app_obj, TEST_FILE)


def load_config_file(app_obj, config_path):
    """
    Open an arbitrary, previously-saved AccuMate config file (e.g.
    DefaultAL4.dat or a specific .AL4 file) via the same Open-file dialog
    flow as load_test_file. Useful for device-connectivity checks, since a
    saved config may already carry the real device's connection settings
    (IP/COM port/etc.) rather than the generic Auto_Test.AL4 test data.
    """
    config_path = os.path.normpath(config_path)

    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"AccuMate config file not found: {config_path}")

    open_file_dialog(app_obj, config_path)


def _click_app_menu_item(app_obj, item_index):
    """
    Open the ribbon's Application Button backstage menu and click the item
    at `item_index` (0-based, in on-screen top-to-bottom order: New, Open...,
    Save, Save As..., ...).
    """
    win = app_obj.get_window()
    win.set_focus()
    time.sleep(0.3)

    uia_win = app_obj.get_uia_window()
    app_button = find_app_button(uia_win)
    app_button.click_input()
    time.sleep(1)  # let the (custom-drawn, non-UIA) popup finish rendering

    win_rect = win.rectangle()
    btn_rect = app_button.rectangle()

    x = (btn_rect.left - win_rect.left) + _APP_MENU_ITEM_X_OFFSET
    y = (btn_rect.bottom - win_rect.top) + _APP_MENU_FIRST_ITEM_Y_OFFSET + item_index * _APP_MENU_ITEM_ROW_HEIGHT

    win.click_input(coords=(x, y))


def _open_save_as_dialog(app_obj, retries=3):
    """
    Open the ribbon Application Button -> "Save As..." menu item and wait
    for the resulting "Save As" common dialog. Retries a few times: the
    backstage menu is entirely custom-drawn (no UIA text/automation_id
    exposed for any of its items - see find_app_button/_click_app_menu_item),
    so the coordinate-based click can occasionally miss if the popup is
    still animating in, or land on nothing if the menu didn't open at all.
    Presses Escape between attempts to dismiss any stuck/mis-clicked menu.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            _click_app_menu_item(app_obj, _APP_MENU_SAVE_AS_INDEX)

            dlg_spec = app_obj.app.window(title=_SAVE_AS_DIALOG_TITLE, class_name=_SAVE_AS_DIALOG_CLASS)
            dlg_spec.wait("exists enabled visible ready", timeout=8)

            return dlg_spec
        except Exception as e:
            last_error = e
            print(f"[WARN] Attempt {attempt}/{retries} to open Save As dialog failed: {e}")
            try:
                app_obj.get_window().type_keys("{ESC}")
            except Exception:
                pass
            time.sleep(1)

    raise RuntimeError(f"Failed to open Save As dialog after {retries} attempts") from last_error


def save_as(app_obj, save_path):
    """
    Save the currently-open AccuMate document to a new path via the ribbon's
    Application Button -> "Save As..." menu item.

    NOTE: there's no dedicated ribbon button or keyboard accelerator for
    Save As - F12 and Ctrl+Shift+S both do nothing, and it isn't reachable
    via the classic Alt+F menu key either (this ribbon skin has no menu bar
    at all). The only path is the Application Button's backstage menu.

    `save_path` may include a directory; the standard Windows Save dialog
    accepts a full path typed into the filename field and will navigate
    there directly. Raises FileNotFoundError if the target directory
    doesn't exist, and RuntimeError if the save doesn't produce the
    expected file (e.g. the dialog failed to open/commit).
    """
    save_path = os.path.normpath(save_path)
    directory = os.path.dirname(save_path)

    if directory and not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory does not exist: {directory}")

    print("[STEP] Opening Application menu -> Save As...")
    dlg_spec = _open_save_as_dialog(app_obj)
    hwnd = dlg_spec.wrapper_object().handle

    uia_app = Application(backend="uia").connect(handle=hwnd)
    uia_dlg = uia_app.window(handle=hwnd)

    filename_edit = uia_dlg.child_window(auto_id=_SAVE_AS_FILENAME_AUTO_ID, control_type="Edit")
    if not filename_edit.exists():
        raise RuntimeError("UIA Edit control not found in Save As dialog")

    filename_edit.set_edit_text(save_path)

    print(f"[STEP] Saving as: {save_path}")
    uia_dlg.child_window(auto_id=_SAVE_AS_SAVE_BUTTON_AUTO_ID, control_type="Button").click_input()
    time.sleep(1)

    # If save_path already exists, this can trigger up to two overwrite
    # confirmations in sequence:
    #   1. The OS-level common-dialog "Confirm Save As" prompt (IDYES=6,
    #      button title is "&Yes" with an accelerator - NOT "Yes").
    #   2. AccuMate's own app-level confirmation, once it actually opens the
    #      file for writing.
    # Handle both, since not doing so leaves a stuck modal dialog that only
    # surfaces later as a screenshot/teardown timeout - not a clear failure
    # at the point it actually went wrong.
    for _ in range(2):
        try:
            confirm_dlg_spec = app_obj.app.window(title_re=".*(onfirm|verwrite).*", class_name="#32770")
            if not confirm_dlg_spec.exists(timeout=2):
                break
        except Exception:
            break

        print("[STEP] Confirming overwrite")
        confirm_dlg = confirm_dlg_spec.wrapper_object()

        # Prefer the standard IDYES control_id (6) - robust regardless of
        # the button's displayed accelerator text ("&Yes" vs "Yes").
        clicked = False
        for ctrl in confirm_dlg.descendants(class_name="Button"):
            try:
                if ctrl.control_id() == 6 or "Yes" in ctrl.window_text():
                    ctrl.click_input()
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            raise RuntimeError("Could not find 'Yes' button on overwrite confirmation dialog")

        time.sleep(1)

    if not os.path.isfile(save_path):
        raise RuntimeError(f"Save As did not create the expected file: {save_path}")

    print(f"[INFO] Saved: {save_path}")
