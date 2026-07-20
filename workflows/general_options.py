import time

from controls.ribbon_controls import find_ribbon_button

# Control IDs inside the "AccuMate General Options" dialog (opened via the
# ribbon's "General Options" button). Discovered by probing a live instance
# of the dialog and reading each control's win32 control_id/window_text -
# stable regardless of window title/text, unlike title-based lookups.
_DIALOG_TITLE = "AccuMate General Options"
_DIALOG_CLASS = "#32770"

CHECKBOX_GO_ONLINE_AUTOMATICALLY = 2108
CHECKBOX_PROMPT_BEFORE_CHANGES_WHEN_ONLINE = 2109
CHECKBOX_DISPLAY_SECURITY_LEVEL = 2104
CHECKBOX_SUPPRESS_PRINTING_UNUSED_RECIPES = 2105
CHECKBOX_INCLUDE_SECURITY_LEVEL_ON_PRINTOUT = 2106
COMBOBOX_LIMIT_PRINTOUT = 2107

_OK_BUTTON_ID = 1
_CANCEL_BUTTON_ID = 2


def open_general_options(app_obj, retries=3):
    """
    Open the "AccuMate General Options" dialog via the ribbon's "General
    Options" button. Returns the dialog as a win32 wrapper.

    Retries the ribbon click a few times - like other ribbon-triggered UI
    in this codebase, the first click can be missed (confirmed live: a
    back-to-back A26 test run that opens this dialog 5 times in a row hit a
    TimeoutError on one iteration without a retry here).
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            win = app_obj.get_window()
            win.set_focus()
            time.sleep(0.3)

            uia_win = app_obj.get_uia_window()
            find_ribbon_button(uia_win, "General Options").click_input()

            dlg_spec = app_obj.app.window(title=_DIALOG_TITLE, class_name=_DIALOG_CLASS)
            dlg_spec.wait("exists enabled visible ready", timeout=8)

            return dlg_spec.wrapper_object()
        except Exception as e:
            last_error = e
            print(f"[WARN] Attempt {attempt}/{retries} to open General Options failed: {e}")
            time.sleep(1)

    raise RuntimeError(f"Failed to open General Options after {retries} attempts") from last_error


def _find_by_control_id(dlg, control_id):
    """
    Find a descendant control by control_id on an already-resolved dialog
    wrapper (`.child_window()` only exists on WindowSpecification, not a
    resolved wrapper - see other workflows/*.py files for the same pattern).
    """
    for ctrl in dlg.descendants():
        try:
            if ctrl.control_id() == control_id:
                return ctrl
        except Exception:
            continue

    raise RuntimeError(f"Control with control_id={control_id} not found in General Options dialog")


def get_checkbox_state(dlg, control_id):
    """Return True if the named checkbox is currently checked."""
    return bool(_find_by_control_id(dlg, control_id).get_check_state())


def set_checkbox(dlg, control_id, checked):
    """Set a checkbox to the desired checked/unchecked state, clicking only if needed."""
    ctrl = _find_by_control_id(dlg, control_id)

    if bool(ctrl.get_check_state()) != checked:
        ctrl.click_input()

    actual = bool(ctrl.get_check_state())
    if actual != checked:
        raise RuntimeError(f"Failed to set checkbox {control_id} to {checked}, got {actual}")


def get_limit_printout_value(dlg):
    """Return the currently selected text of the "Limit printout of parameters to:" combo box."""
    return _find_by_control_id(dlg, COMBOBOX_LIMIT_PRINTOUT).window_text()


def set_limit_printout_value(dlg, value):
    """Select an item in the "Limit printout of parameters to:" combo box by its visible text."""
    _find_by_control_id(dlg, COMBOBOX_LIMIT_PRINTOUT).select(value)


def close_general_options(dlg, accept=True):
    """Close the General Options dialog, committing changes if accept=True."""
    control_id = _OK_BUTTON_ID if accept else _CANCEL_BUTTON_ID
    _find_by_control_id(dlg, control_id).click_input()
    time.sleep(0.3)
