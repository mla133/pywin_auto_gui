import time

from pywinauto import Desktop

from controls.ribbon_controls import click_ribbon_button

# The Terminal Emulator is opened via the ribbon "Terminal Emulator" button
# (only enabled while AccuMate has a live device connection - see
# app.application.AccuMateApp.is_device_connected). It replaces the active
# MDI child's content with a command Edit box + Arm selector ComboBox above
# a read-only output Edit box, and adds a contextual "Terminal Emulator"
# ribbon tab. Control IDs discovered via a live win32 descendants() scan of
# the main window while the Terminal Emulator view was active.
_COMMAND_EDIT_ID = 1016
_ARM_COMBOBOX_ID = 1187
_OUTPUT_EDIT_ID = 1017

_HOME_TAB_NAME = "Home"
_TERMINAL_TAB_NAME = "Terminal Emulator"


def _find_by_control_id(win, control_id, class_name=None):
    """
    Find a descendant control by control_id (and optionally class_name, to
    disambiguate ids reused by different control types) on an
    already-resolved win32 window wrapper.
    """
    for ctrl in win.descendants():
        try:
            if ctrl.control_id() != control_id:
                continue
            if class_name is not None and ctrl.class_name() != class_name:
                continue
            return ctrl
        except Exception:
            continue

    raise RuntimeError(f"Control with control_id={control_id} not found")


def open_terminal_emulator(app_obj, retries=3, poll_timeout=6):
    """
    Open the Terminal Emulator view via the ribbon "Terminal Emulator"
    button. Requires AccuMate to already have a live device connection (the
    button is disabled otherwise). Returns the main win32 window wrapper for
    use with the other functions in this module.

    Retries the ribbon click a few times and polls for the command Edit box
    to appear - like other ribbon-button-triggered UI changes in this
    codebase (see workflows.comm_workflows.open_communications_settings),
    the very first click can be missed if the app is still settling right
    after a "Retry Comm" connection attempt.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            uia_win = app_obj.get_uia_window()
            print(f"[STEP] Opening Terminal Emulator (attempt {attempt}/{retries})")
            click_ribbon_button(uia_win, _TERMINAL_TAB_NAME)

            win = app_obj.get_window()
            start = time.time()
            while time.time() - start < poll_timeout:
                try:
                    get_command_box(win)
                    return win
                except Exception:
                    time.sleep(0.5)

            raise RuntimeError("Terminal Emulator command box did not appear in time")
        except Exception as e:
            last_error = e
            print(f"[WARN] Attempt {attempt}/{retries} to open Terminal Emulator failed: {e}")
            time.sleep(1)

    raise RuntimeError(
        f"Failed to open Terminal Emulator after {retries} attempts"
    ) from last_error


def get_command_box(win):
    return _find_by_control_id(win, _COMMAND_EDIT_ID, class_name="Edit")


def get_arm_combobox(win):
    return _find_by_control_id(win, _ARM_COMBOBOX_ID, class_name="ComboBox")


def get_output_text(win):
    """Read the full text of the read-only output/response Edit box."""
    return _find_by_control_id(win, _OUTPUT_EDIT_ID, class_name="Edit").window_text()


def send_command(win, command, settle_time=2.0):
    """
    Type `command` into the Terminal Emulator's command box and press Enter.
    Waits `settle_time` seconds for the AccuLoad's response to be appended
    to the output box before returning.
    """
    print(f"[STEP] Sending Terminal Emulator command: {command}")
    cmd_box = get_command_box(win)
    cmd_box.click_input()
    cmd_box.type_keys("^a")  # select all (clear any leftover text)
    cmd_box.type_keys(command, with_spaces=True)
    cmd_box.type_keys("{ENTER}")
    time.sleep(settle_time)


def wait_for_progress_dialog_to_close(app_obj, timeout=400, poll_interval=2.0, appear_timeout=15):
    """
    Wait for the "Writing data in <config> to <device> [NN%]" / "Downloading
    data..." progress window (shown by PUSH/PULL while transferring config
    data to/from the AccuLoad) to close, indicating the transfer has
    finished.

    IMPORTANT: this window is NOT a standard "#32770" common dialog - live
    probing (via a Desktop window-enumeration monitor watching a real PUSH
    run start-to-finish) showed its actual win32 class is a dynamic,
    per-run string like "Afx:007D0000:23:00010019:351019FE:00000000", with
    the *title* carrying the real state ("Writing data in AL4ConfigFile1 to
    AL4-1000 [42%]", counting up to [100%] before closing). An earlier
    version of this function filtered on class_name() == "#32770", which
    never matched this window at all - _dialog_open() was therefore always
    False and the function returned "complete" almost immediately after
    sending PUSH, well before the real transfer had even reached 1%. Detect
    the window by title substring instead (matches both "Writing data..."
    for PUSH and "Downloading..." for PULL).

    A full PUSH of a blank/default config was also clocked live at ~300-350
    seconds (0% to 100%, roughly linear, ~3s per percentage point) - the
    default `timeout` here is set generously above that to avoid a real
    in-progress transfer being mistaken for "stuck".

    First waits up to `appear_timeout` seconds for the window to actually
    appear at all, to tolerate PUSH/PULL not popping it instantaneously
    after the command is sent. If it never appears, proceeds to the
    close-wait anyway (in case the transfer was too fast to catch), but
    logs a warning since this could otherwise mask a false "completed"
    result if the transfer never actually started.

    NOTE: must enumerate windows via pywinauto.Desktop filtered by the
    app's process id - Application.connect(process=pid).windows() does NOT
    reliably list this window (confirmed live: it silently reported no
    matching window while it was clearly visible on screen), unlike
    Desktop(backend="win32").windows() filtered by process_id.

    Returns True if the window closed within `timeout` seconds, False if it
    was still open when the timeout elapsed (never raises for a timeout -
    callers should treat False as "transfer still in progress / stuck").
    """
    pid = app_obj.get_window().process_id()

    def _progress_window_open():
        try:
            windows = Desktop(backend="win32").windows()
        except Exception:
            # A window (e.g. the progress dialog itself, right as it hits
            # 100% and closes) can vanish mid-enumeration, raising
            # InvalidWindowHandle from inside Desktop.windows() itself -
            # before the per-window try/except below even runs. Treat this
            # as "couldn't tell this poll" rather than letting it propagate
            # and fail the whole wait.
            return False

        for w in windows:
            try:
                if w.process_id() != pid or not w.is_visible():
                    continue
                title = w.window_text()
                if "Writing data" in title or "Downloading" in title:
                    return True
            except Exception:
                continue
        return False

    appear_start = time.time()
    seen_open = False
    while time.time() - appear_start < appear_timeout:
        if _progress_window_open():
            seen_open = True
            break
        time.sleep(0.5)

    if not seen_open:
        print(
            "[WARN] PUSH/PULL progress window never observed opening within "
            f"{appear_timeout}s - proceeding to close-wait anyway in case the "
            "transfer was too fast to catch it, but this may mask a false "
            "'completed' result if the transfer never actually ran."
        )

    start = time.time()

    while time.time() - start < timeout:
        if not _progress_window_open():
            return True

        time.sleep(poll_interval)

    return False



def switch_to_home_ribbon_tab(app_obj):
    """
    Switch the ribbon back to the "Home" tab. The Terminal Emulator view
    adds its own contextual ribbon tab and can leave "Home" (and therefore
    ribbon buttons like "Go Offline"/"Pull All From AccuLoad") not current -
    call this after Terminal Emulator interactions if subsequent steps rely
    on Home-tab ribbon buttons (e.g. AccuMateApp.is_device_connected()).
    """
    uia_win = app_obj.get_uia_window()
    for ctrl in uia_win.descendants():
        try:
            if ctrl.element_info.control_type == "TabItem" and ctrl.window_text() == _HOME_TAB_NAME:
                ctrl.click_input()
                return
        except Exception:
            continue

    raise RuntimeError("Ribbon 'Home' tab not found")