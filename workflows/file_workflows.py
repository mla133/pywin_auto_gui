import time
import os
from pywinauto.keyboard import send_keys
from pywinauto import Application

TEST_FILE = os.path.normpath(
    r"C:\\Users\\allenma\\Documents\\Testing\\Auto_Test.AL4"
    )

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
