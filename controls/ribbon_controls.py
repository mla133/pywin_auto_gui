import time


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