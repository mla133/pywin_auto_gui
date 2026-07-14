import time

from controls.ribbon_controls import click_ribbon_button

# Control IDs inside the "AccuMate Communications Settings" dialog (opened via
# the ribbon's "Document Options" button). Discovered by probing a live
# instance of the dialog - these are stable regardless of window title/text,
# unlike title-based lookups which can be ambiguous or change with locale.
_COMM_DIALOG_TITLE = "AccuMate Communications Settings"
_COMM_DIALOG_CLASS = "#32770"
_IP_ADDRESS_CONTROL_ID = 1028   # SysIPAddress32
_OK_BUTTON_ID = 1


def open_communications_settings(app_obj, retries=2):
    """
    Open the "AccuMate Communications Settings" dialog via the ribbon's
    "Document Options" button. Returns the dialog as a win32 wrapper.

    Retries the click a couple of times - immediately after loading a config
    file, the main window can still be settling (e.g. finishing its initial
    "Attempting to connect..." dialog) and the very first ribbon click can be
    missed.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            win = app_obj.get_window()
            win.set_focus()
            time.sleep(0.5)

            uia_win = app_obj.get_uia_window()
            click_ribbon_button(uia_win, "Document Options")

            dlg_spec = app_obj.app.window(title=_COMM_DIALOG_TITLE, class_name=_COMM_DIALOG_CLASS)
            dlg_spec.wait("exists enabled visible ready", timeout=10)

            return dlg_spec.wrapper_object()
        except Exception as e:
            last_error = e
            print(f"[WARN] Attempt {attempt}/{retries} to open Communications Settings failed: {e}")
            time.sleep(1)

    raise RuntimeError(
        f"Failed to open Communications Settings dialog after {retries} attempts"
    ) from last_error


def _find_by_control_id(dlg, control_id):
    """
    Find a descendant control by control_id on an already-resolved dialog
    wrapper. `.child_window()` only exists on WindowSpecification objects,
    not on resolved wrappers (dlg is a wrapper here, see
    open_communications_settings), so scan descendants instead.
    """
    for ctrl in dlg.descendants():
        try:
            if ctrl.control_id() == control_id:
                return ctrl
        except Exception:
            continue

    raise RuntimeError(f"Control with control_id={control_id} not found in dialog")


def set_device_ip(dlg, ip_address):
    """
    Set the IP Address field (SysIPAddress32) in an already-open
    Communications Settings dialog.

    NOTE: setting this control's value via ctypes SendMessage
    (IPM_SETADDRESS) is unreliable - readback via IPM_GETADDRESS returns
    0.0.0.0 across the 32-bit/64-bit process boundary even when the set
    actually succeeded. click_input() + type_keys() is the reliable method,
    verified via window_text() readback instead.
    """
    ip_ctrl = _find_by_control_id(dlg, _IP_ADDRESS_CONTROL_ID)
    ip_ctrl.click_input()
    ip_ctrl.type_keys("^a")  # select all
    ip_ctrl.type_keys(ip_address)

    actual = ip_ctrl.window_text()
    if ip_address not in actual:
        raise RuntimeError(
            f"Failed to set device IP address: expected '{ip_address}', got '{actual}'"
        )


def close_communications_settings(dlg, accept=True):
    """Close the Communications Settings dialog, committing changes if accept=True."""
    control_id = _OK_BUTTON_ID if accept else 2  # 2 == IDCANCEL
    _find_by_control_id(dlg, control_id).click_input()


def configure_ip_and_connect(app_obj, ip_address, timeout=15):
    """
    Configure AccuMate's device IP address and attempt a live connection:

      1. Open the Communications Settings dialog (Document Options ribbon
         button).
      2. Set the IP Address field to `ip_address`.
      3. Commit the dialog (OK).
      4. Click the ribbon "Retry Comm" button to trigger a connection
         attempt.
      5. Poll AccuMateApp.is_device_connected() until it reports True or
         `timeout` seconds elapse.

    Returns True if AccuMate reports a live connection within `timeout`
    seconds, False otherwise. Never raises for connection failures - only
    for failures interacting with the UI itself (e.g. dialog/control not
    found).
    """
    print(f"[STEP] Opening Communications Settings, setting IP to {ip_address}")
    dlg = open_communications_settings(app_obj)
    set_device_ip(dlg, ip_address)
    close_communications_settings(dlg, accept=True)
    time.sleep(0.5)

    print("[STEP] Clicking ribbon 'Retry Comm'")
    uia_win = app_obj.get_uia_window()
    click_ribbon_button(uia_win, "Retry Comm")

    print(f"[STEP] Waiting up to {timeout}s for AccuMate to report a live connection")
    return app_obj.wait_for_device_connection(timeout=timeout)
