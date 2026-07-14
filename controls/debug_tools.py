from .uia_sta import run_in_sta


def _describe_control(ctrl, name):
    info = {
        "name": ctrl.window_text(),
        "control_type": ctrl.element_info.control_type,
        "automation_id": ctrl.element_info.automation_id,
        "class_name": ctrl.element_info.class_name,
        "enabled": ctrl.is_enabled(),
        "visible": ctrl.is_visible(),
    }

    return info


def _find_and_describe(win, name):
    try:
        spec = win.child_window(title=name, control_type="Button")
        ctrl = spec.wrapper_object()
        return _describe_control(ctrl, name)
    except Exception:
        # Fall back to a descendants scan in case the control isn't an exact
        # title match or isn't a "Button" control type (ribbon controls can
        # vary between MFC ribbon implementations).
        for ctrl in win.descendants():
            try:
                if name in ctrl.window_text():
                    return _describe_control(ctrl, name)
            except Exception:
                continue

        return {"name": name, "error": "control not found"}


def safe_dump_control(win, name):
    """
    Locate a control by visible title under `win` and return a dict describing
    it (name, control_type, automation_id, class_name, enabled, visible).

    Runs inside a dedicated STA thread via run_in_sta, since pywinauto's UIA
    backend requires STA-threaded COM and this may be called from a test's
    default (non-STA-guaranteed) thread.
    """
    try:
        return run_in_sta(_find_and_describe, win, name)
    except Exception as e:
        print(f"[safe_dump_control] UIA dump failed: {e}")
        return {"name": name, "error": str(e)}
