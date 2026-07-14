import time


def find_ribbon_button(uia_win, button_name):
    """Locate a ribbon button by its visible title via the UIA backend.

    `uia_win` is a resolved wrapper (see AccuMateApp.get_uia_window), so we
    scan descendants rather than using child_window (which requires a
    WindowSpecification, not a wrapper).
    """

    for ctrl in uia_win.descendants():
        try:
            if button_name in ctrl.window_text():
                return ctrl
        except Exception:
            continue

    raise RuntimeError(f"Ribbon button '{button_name}' not found")


def is_ribbon_button_enabled(uia_win, button_name):
    """Return True if the named ribbon button exists and is enabled."""

    try:
        btn = find_ribbon_button(uia_win, button_name)
        return btn.is_enabled()
    except Exception as e:
        print(f"[WARN] Ribbon button '{button_name}' not found: {e}")
        return False


def click_ribbon_button(uia_win, button_name):
    """Click a ribbon button by its visible title."""

    btn = find_ribbon_button(uia_win, button_name)

    print(f"[DEBUG] Clicking ribbon button: {button_name}")
    btn.click_input()


def open_file_menu(app_obj):
    """
    Open File -> Open... from Ribbon (MFC-safe)
    """
    win = app_obj.get_window()

    print("[DEBUG] Ribbon: File -> Open")

    win.set_focus()

    win.type_keys("%F")   # Alt+F
    time.sleep(0.3)

    win.type_keys("{DOWN}")   # Move to Open
    time.sleep(0.2)

    win.type_keys("{ENTER}")  # Execute
    time.sleep(0.5)