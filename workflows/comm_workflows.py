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

# "Communications Addresses:" Edit controls in the Communications Settings
# dialog, one per arm (Arm 1 (Base) .. Arm 6), 1-indexed to match the UI
# labels. Discovered via a live descendants() scan - each is a plain 'Edit'
# control (not SysIPAddress32), default text is the arm number itself
# (Arm 1 -> "1", Arm 2 -> "2", etc).
_ARM_ADDRESS_CONTROL_IDS = {
    1: 1030,
    2: 1071,
    3: 1072,
    4: 1073,
    5: 1074,
    6: 1075,
}


def open_communications_settings(app_obj, retries=2):
    """
    Open the "AccuMate Communications Settings" dialog via the ribbon's
    "Document Options" button. Returns the dialog as a win32 wrapper.

    Retries the click a couple of times - immediately after loading a config
    file, the main window can still be settling (e.g. finishing its initial
    "Attempting to connect..." dialog) and the very first ribbon click can be
    missed.

    Each attempt first checks whether the dialog is ALREADY open before
    clicking the ribbon again (confirmed live: the main frame reports
    enabled=False whenever this dialog is open, so a naive retry loop that
    always starts with `app_obj.get_window()` - which waits for the main
    frame to be enabled - can get stuck forever on retry if a *previous*
    attempt's ribbon click actually succeeded and opened the dialog, but the
    wait() that confirms it raised for an unrelated transient reason. Without
    this check, that leaves the dialog genuinely open with no way to ever
    re-click "Document Options" - accepting/short-circuiting on an
    already-open dialog avoids that self-defeating retry pattern).
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            existing = app_obj.app.window(title=_COMM_DIALOG_TITLE, class_name=_COMM_DIALOG_CLASS)
            if existing.exists(timeout=1):
                return existing.wrapper_object()
        except Exception:
            pass

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


def get_configured_ip(dlg):
    """Read the current value of the IP Address field without changing it."""
    return _find_by_control_id(dlg, _IP_ADDRESS_CONTROL_ID).window_text()


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


def get_arm_address(dlg, arm_number):
    """Read the current Communications Address for the given arm (1-6)."""
    control_id = _ARM_ADDRESS_CONTROL_IDS[arm_number]
    return _find_by_control_id(dlg, control_id).window_text()


def set_arm_address(dlg, arm_number, address):
    """
    Set the Communications Address Edit field for a single arm (1-6) in an
    already-open Communications Settings dialog.
    """
    control_id = _ARM_ADDRESS_CONTROL_IDS[arm_number]
    ctrl = _find_by_control_id(dlg, control_id)
    ctrl.click_input()
    ctrl.type_keys("^a")  # select all
    ctrl.type_keys(str(address))

    actual = ctrl.window_text()
    if str(address) != actual:
        raise RuntimeError(
            f"Failed to set Arm {arm_number} address: expected '{address}', got '{actual}'"
        )


def set_arm_addresses(dlg, addresses):
    """
    Set Communications Addresses for arms 1..len(addresses) in one pass.
    `addresses` is a sequence of values applied in order (index 0 -> Arm 1).
    """
    for arm_number, address in enumerate(addresses, start=1):
        set_arm_address(dlg, arm_number, address)


def close_communications_settings(dlg, accept=True):
    """Close the Communications Settings dialog, committing changes if accept=True."""
    control_id = _OK_BUTTON_ID if accept else 2  # 2 == IDCANCEL
    _find_by_control_id(dlg, control_id).click_input()


def wait_for_warning_dialog(app_obj, timeout=5, exclude_title=_COMM_DIALOG_TITLE):
    """
    Poll for any NEW top-level "#32770" message-box-style dialog other than
    the Communications Settings dialog itself (e.g. the "Arm Address 1
    cannot be 0" warning triggered by set_arm_address(dlg, 1, 0) - see A9).
    Returns the dialog's win32 wrapper if one appears within `timeout`
    seconds, or None otherwise. Doesn't assume any specific title/text,
    since the exact wording of these AccuMate warnings hasn't been
    confirmed live yet - callers should print/inspect `.window_text()` of
    the dialog and any static text descendants to see the real message.
    """
    start = time.time()

    while time.time() - start < timeout:
        try:
            for w in app_obj.app.windows(class_name=_COMM_DIALOG_CLASS):
                title = w.window_text()
                if title and title != exclude_title:
                    return w
        except Exception:
            pass

        time.sleep(0.3)

    return None


def dismiss_dialog(dlg, prefer_text=("OK",)):
    """
    Click the first Button descendant whose text matches one of
    `prefer_text` (case-insensitive substring). Falls back to control_id 1
    (the conventional IDOK) for classic #32770 message boxes, and finally to
    the first Button descendant found at all - confirmed live that not
    every warning here is a classic MessageBox (e.g. the Arm 2 = 0 warning
    is a modern "Dialog"-class window with no numeric IDOK control_id, so
    the control_id fallback alone isn't sufficient).
    """
    for wanted in prefer_text:
        for ctrl in dlg.descendants(class_name="Button"):
            try:
                if wanted.lower() in ctrl.window_text().lower():
                    ctrl.click_input()
                    return
            except Exception:
                continue

    try:
        _find_by_control_id(dlg, _OK_BUTTON_ID).click_input()
        return
    except Exception:
        pass

    buttons = dlg.descendants(class_name="Button")
    if buttons:
        buttons[0].click_input()
        return

    # No Button descendants at all - matches this codebase's established
    # pattern for custom-drawn/non-automatable popups (e.g. the ribbon
    # Application Button's backstage menu). Fall back to a keystroke, which
    # DOES work for at least some of these even when clicking doesn't apply
    # (unlike the Application Button menu, where {DOWN} silently closed it -
    # confirm {ENTER} actually dismisses this specific dialog live).
    try:
        dlg.set_focus()
        dlg.type_keys("{ENTER}")
        return
    except Exception:
        pass

    raise RuntimeError(f"Could not find a button to dismiss dialog {dlg.window_text()!r}")


def configure_ip_and_connect(app_obj, ip_address, timeout=45, arm_addresses=None):
    """
    Configure AccuMate's device IP address and attempt a live connection:

      1. Open the Communications Settings dialog (Document Options ribbon
         button).
      2. Optionally set the per-arm Communications Addresses (see
         set_arm_addresses) - a blank/new config's default addresses
         (1, 2, 3, 4, 5, 6) may not match the physical AccuLoad's actual
         configured arm addresses, in which case the connection attempt
         below will fail/time out even though the IP itself is reachable.
      3. Set the IP Address field to `ip_address`.
      4. Commit the dialog (OK).
      5. Click the ribbon "Retry Comm" button to trigger a connection
         attempt.
      6. Poll AccuMateApp.is_device_connected() until it reports True or
         `timeout` seconds elapse.

    Returns True if AccuMate reports a live connection within `timeout`
    seconds, False otherwise. Never raises for connection failures - only
    for failures interacting with the UI itself (e.g. dialog/control not
    found).
    """
    print(f"[STEP] Opening Communications Settings, setting IP to {ip_address}")
    dlg = open_communications_settings(app_obj)
    if arm_addresses is not None:
        set_arm_addresses(dlg, arm_addresses)
    set_device_ip(dlg, ip_address)
    close_communications_settings(dlg, accept=True)
    time.sleep(0.5)

    print("[STEP] Clicking ribbon 'Retry Comm'")
    uia_win = app_obj.get_uia_window()
    click_ribbon_button(uia_win, "Retry Comm")

    print(f"[STEP] Waiting up to {timeout}s for AccuMate to report a live connection")
    return app_obj.wait_for_device_connection(timeout=timeout)

