import time
from pywinauto import Application
from time import sleep

APP_TITLE = "AccuMate for AccuLoad"
APP_EXE = r"C:\Users\allenma\SoftwareDevelopment\acculoadiv.AccuMate\Release\AccuMate.exe"
BACKEND = "win32"


def connect_app():
    """Start the application."""
    return Application(backend=BACKEND).start(APP_EXE)


#def get_main_window(app):
#    """Resolve the main window safely."""
#    win = app.window(title=APP_TITLE)
#    win.wait("exists enabled visible ready", timeout=10)
#    return win

def get_main_window(app):
    """
    Resolve the correct window dynamically.
    After opening a file, AccuMate uses a new child/document window
    whose title contains the filename (.AL4).
    """
    import time

    for _ in range(10):  # retry loop
        windows = app.windows()

        for w in windows:
            try:
                title = w.window_text()

                print(f"[DEBUG] Candidate window: '{title}'")

                # Prefer the document window
                if title and ".AL4" in title:
                    handle = w.handle

                    win = app.window(handle=handle)
                    win.wait("exists enabled visible ready", timeout=5)
                    print(f"[DEBUG] Using document window: '{title}'")
                    return win

            except Exception:
                continue

        # fallback attempt (original window)
        try:
            win = app.window(title=APP_TITLE)
            if win.exists():
                print(f"[DEBUG] Falling back to main window: '{APP_TITLE}'")
                win.wait("exists enabled visible ready", timeout=5)
                return win
        except Exception:
            pass

        time.sleep(0.5)

    raise RuntimeError("Could not resolve main window")


def safe_descendants(win, retries=3, delay=0.2):
    """Safely enumerate descendants with retry."""
    for _ in range(retries):
        try:
            return win.descendants()
        except Exception:
            time.sleep(delay)
    return []


def snapshot_controls(app):
    """Take a snapshot of all controls."""
    win = get_main_window(app)
    controls = safe_descendants(win)

    snapshot = []

    for c in controls:
        try:
            snapshot.append({
                "id": c.control_id(),
                "class": c.class_name(),
                "text": c.window_text()
            })
        except Exception:
            # Skip unstable controls
            continue

    return snapshot

def wait_for_ui_ready(app, timeout=10):
    """Wait until dynamic controls (list/tree) appear."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        snapshot = snapshot_controls(app)

        has_list = any("List" in c["class"] for c in snapshot)
        has_tree = any("Tree" in c["class"] for c in snapshot)

        if has_list or has_tree:
            return True

        time.sleep(0.5)

    return False
def wait_for_control(app, class_name, timeout=10):
    """
    Wait until a control of a given class exists and is resolvable.
    Handles MFC dynamic UI timing issues.
    """
    import time

    start = time.time()

    while time.time() - start < timeout:
        win = get_main_window(app)

        try:
            ctrl = win.child_window(class_name=class_name)
            ctrl.wrapper_object()  # force resolution
            return ctrl
        except Exception:
            time.sleep(0.3)

    raise TimeoutError(f"{class_name} not found within {timeout} seconds")

def open_file_workflow(app, file_path=None):
    """
    Perform the UI steps required to open a file.
    Customize this based on your app's actual UI.
    """

    win = get_main_window(app)

    # Example approaches — you will tailor this

    # Option 1: Menu
    try:
        win.menu_select("File->Open")
    except Exception:
        pass

    # Option 2: Button (if no menu)
    try:
        btn = wait_for_control(app, "Button")
        btn = btn.wrapper_object()
        btn.click()
    except Exception:
        pass

    # If file dialog appears
    try:
        dlg = app.window(class_name="#32770")  # standard Windows dialog
        dlg.wait("visible", timeout=5)

        edit = dlg.child_window(class_name="Edit")
        edit.set_text(file_path or "test.dat")

        dlg.child_window(title="Open", class_name="Button").click()
    except Exception:
        pass

    # Wait for UI to populate AFTER file load
    wait_for_ui_ready(app, timeout=15)


def open_file_dialog(app, file_path):
    """
    A more robust implementation of the file open workflow.
    Uses keyboard navigation and dynamic waiting to handle MFC quirks.
    """
    import time

    print("[DEBUG] Triggering Open via keyboard")

    win = get_main_window(app)
    win.set_focus()
    win.type_keys("%F")  # Alt+F to open File menu
    time.sleep(0.3)
    win.type_keys("{DOWN}")  # Move to Open
    time.sleep(0.3)
    win.type_keys("{ENTER}")  # Select Open

    print("[DEBUG] Waiting for file dialog")
    dlg = app.window(class_name="#32770")

    try:
        dlg.wait("exists visible enabled ready", timeout=10)
    except Exception:
        raise RuntimeError("File dialog did not appear")

    print("[DEBUG] Setting filename")

    edit = dlg.child_window(class_name="Edit").wrapper_object()
    edit.set_text(file_path)
    time.sleep(0.3)

    print("[DEBUG] Clicking Open in dialog")
    buttons = dlg.descendants(class_name="Button")

    open_btn = None

    for b in buttons:
        try:
            text = b.window_text().strip().lower()
            print(f"[DEBUG] Found button with text: '{text}'")

            if text in ("open", "&open"):
                open_btn = b
                break

        except Exception:
            continue

    if not open_btn:
        raise RuntimeError("Open button not found in dialog")

    open_btn.click()

    print("[DEBUG] Waiting for UI ready")
    wait_for_ui_ready(app, timeout=5)
