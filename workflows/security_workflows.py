import time


def enter_passcode(app_obj, passcode):
    """
    Enter passcode and handle incorrect passcode dialog if it appears.
    """

    print("[STEP] Waiting for passcode dialog...")

    dlg = app_obj.app.window(class_name="#32770")
    dlg.wait("exists visible enabled ready", timeout=10)

    print("[DEBUG] Passcode dialog detected")

    dlg.set_focus()

    edit = dlg.child_window(class_name="Edit").wrapper_object()
    edit.set_text(passcode)

    time.sleep(0.2)

    print("[DEBUG] Submitting passcode")
    edit.type_keys("{ENTER}")

    time.sleep(0.5)

    # NEW: handle incorrect passcode popup
    if handle_incorrect_passcode(app_obj):
        print("[WARN] Incorrect passcode entered")
        return False

    print("[INFO] Passcode accepted")
    return True


def handle_incorrect_passcode(app_obj):
    """
    Detects and dismisses 'Passcode incorrect' dialog.
    Returns True if dialog was found.
    """

    try:
        dlg = app_obj.app.window(class_name="#32770")

        dlg.wait("visible", timeout=2)

        print("[DEBUG] Checking for error dialog...")

        for ctrl in dlg.descendants():
            try:
                text = ctrl.window_text()
                if "incorrect" in text.lower():
                    print(f"[INFO] Error message detected: {text}")

                    # Click OK
                    for b in dlg.descendants(class_name="Button"):
                        if "ok" in b.window_text().lower():
                            print("[DEBUG] Clicking OK")
                            b.click()
                            time.sleep(0.5)
                            return True
            except Exception:
                continue

    except Exception:
        return False

    return False
