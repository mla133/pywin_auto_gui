import time
import os
from pywinauto.keyboard import send_keys

TEST_FILE = os.path.normpath(
    r"C:\\Users\\allenma\\Documents\\AccuMate Files\\Kitchen_Sink-1_12.AL4"
    )


def open_file_dialog(app_obj, file_path):
    print("[DEBUG] Triggering Open via keyboard")

    win = app_obj.get_window()
    win.set_focus()

    win.type_keys("%F")
    time.sleep(0.3)

    win.type_keys("{DOWN}")
    time.sleep(0.3)

    win.type_keys("{ENTER}")

    print("[DEBUG] Waiting for file dialog")

    dlg = app_obj.app.window(class_name="#32770")

    dlg.wait("exists visible enabled ready", timeout=10)

    print("[DEBUG] Setting filename")

    edit = dlg.child_window(class_name="Edit").wrapper_object()
    edit.set_text(file_path)

    time.sleep(0.3)

    print("[DEBUG] Clicking Open")

    for b in dlg.descendants(class_name="Button"):
        try:
            text = b.window_text().lower().strip()
            if text in ("open", "&open"):
                b.click()
                break
        except Exception:
            continue

    time.sleep(1)


def load_test_file(app_obj):
    open_file_dialog(app_obj, TEST_FILE)
