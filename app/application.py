from pywinauto import Application
import re
import time

APP_TITLE = "AccuMate for AccuLoad"
APP_EXE = r"C:\\Users\\allenma\\SoftwareDevelopment\\acculoadiv.AccuMate\\Release\\AccuMate.exe"
BACKEND = "win32"

# Once a config file is loaded, the main frame's title changes to
# "<filename> - AccuMate for AccuLoad", so an exact title=APP_TITLE match
# (as pywinauto does by default) stops matching. The ribbon's docking
# "AFX_SUPERBAR_TAB:..." window also shares the same title text, so a plain
# title_re match is ambiguous (2 windows). Match on the title *suffix* plus
# the main frame's class name prefix ("Afx:...", as opposed to
# "AFX_SUPERBAR_TAB:...") to reliably find just the one real app window,
# whether or not a file has been loaded yet.
_TITLE_RE = r".*" + re.escape(APP_TITLE) + r"\s*$"
_CLASS_NAME_RE = r"^Afx:"

# Position/size used to keep the automated app window on a secondary
# monitor (off to the side of wherever the user is actively working), so
# repeated focus/re-focus during UI automation doesn't interrupt them.
# Auto-detected on first use (see _detect_secondary_monitor_rect()) unless
# explicitly overridden via set_secondary_monitor_target(); None means "no
# secondary monitor available / detection failed" (single-monitor setups
# fall back to leaving the window wherever Windows placed it).
_SECONDARY_MONITOR_RECT = "auto"


def set_secondary_monitor_target(left, top, width=1400, height=900):
    """
    Explicitly configure the screen rectangle AccuMateApp should move its
    window to (see move_to_secondary_monitor()), overriding auto-detection.
    Call once at the start of a session with the secondary monitor's
    coordinates (e.g. from System.Windows.Forms.Screen.AllScreens) before
    launching/using AccuMateApp, so every subsequent window it manages
    stays off the primary monitor. Pass left=None to disable repositioning
    entirely (e.g. for genuinely single-monitor setups where auto-detection
    should not be trusted).
    """
    global _SECONDARY_MONITOR_RECT
    if left is None:
        _SECONDARY_MONITOR_RECT = None
    else:
        _SECONDARY_MONITOR_RECT = (left, top, width, height)


def _detect_secondary_monitor_rect(width=1400, height=900):
    """
    Auto-detect a non-primary monitor via win32api.EnumDisplayMonitors and
    return a (left, top, width, height) rectangle positioned near its
    top-left corner, sized `width`x`height`. Returns None if there's only
    one monitor or detection fails for any reason (best-effort - a failure
    here should never block launching/using the app, just leaves the
    window at Windows' own default placement).
    """
    try:
        import win32api

        monitors = win32api.EnumDisplayMonitors()
        if len(monitors) < 2:
            return None

        primary_handle = win32api.MonitorFromPoint((0, 0))
        for handle, _, _ in monitors:
            if handle == primary_handle:
                continue
            info = win32api.GetMonitorInfo(handle)
            mon_left, mon_top, mon_right, mon_bottom = info["Monitor"]
            left = mon_left + 20
            top = mon_top + 40
            return (left, top, width, height)
    except Exception:
        pass
    return None


class AccuMateApp:

    def __init__(self):
        self.app = Application(backend=BACKEND).start(APP_EXE)
        self._uia_app = None
        self._moved_to_secondary = False

    def _move_to_secondary_monitor_if_configured(self, win):
        """
        Move `win` to the configured (or auto-detected) secondary-monitor
        rectangle the first time a window handle is resolved. Only
        attempted once per AccuMateApp instance (repeated moves on every
        get_window() call would be wasteful and could fight with the user
        manually repositioning it); best-effort only - swallows failures
        rather than blocking UI automation on this.
        """
        global _SECONDARY_MONITOR_RECT
        if self._moved_to_secondary:
            return
        self._moved_to_secondary = True

        if _SECONDARY_MONITOR_RECT == "auto":
            _SECONDARY_MONITOR_RECT = _detect_secondary_monitor_rect()

        if _SECONDARY_MONITOR_RECT is None:
            return

        try:
            import win32gui

            left, top, width, height = _SECONDARY_MONITOR_RECT
            win32gui.MoveWindow(win.handle, left, top, width, height, True)
        except Exception:
            pass

    def get_window(self):
        # Get the window spec by title suffix + main-frame class name
        win_spec = self.app.window(title_re=_TITLE_RE, class_name_re=_CLASS_NAME_RE)

        # Wait on the spec, not the wrapper
        win_spec.wait("exists enabled visible ready", timeout=10)

        # Convert to a wrapper
        win = win_spec.wrapper_object()
        self._move_to_secondary_monitor_if_configured(win)
        return win

    def get_uia_window(self):
        """Attach to the same top-level window via the UIA backend.

        MFC ribbon buttons aren't exposed as native win32 controls, so ribbon
        inspection/interaction (see controls/ribbon_controls.py and
        controls/debug_tools.py) requires attaching via UIA to the same HWND.
        """
        win = self.get_window()
        hwnd = win.handle

        if self._uia_app is None:
            self._uia_app = Application(backend="uia").connect(handle=hwnd)

        uia_win_spec = self._uia_app.window(handle=hwnd)
        uia_win_spec.wait("exists enabled visible ready", timeout=10)

        return uia_win_spec.wrapper_object()

    def is_device_connected(self):
        """
        Return True if AccuMate currently has a *live* connection to a
        physical AccuLoad device, False otherwise.

        NOTE: the presence of the System Directory tree (SysTreeView32) is
        NOT a valid signal here - the tree populates as soon as a config
        FILE is loaded/parsed, completely independent of whether AccuMate
        has an active device connection. The status bar text ("ONLINE" vs
        "Offline"/"Comm Not Enabled") reflects real connectivity, but it's
        rendered as a non-accessible, owner-drawn region (no matching
        control/text found via either the win32 or UIA backend).

        Instead, use the ribbon's "Pull All From AccuLoad" button as a
        reliable proxy: it (along with "Push All to AccuLoad" and "Go
        Offline") is only enabled while genuinely online, and disabled
        while offline - this was confirmed empirically by toggling
        "Go Offline"/"Retry Comm" against the visible status bar text.
        """
        from controls.ribbon_controls import is_ribbon_button_enabled

        try:
            uia_win = self.get_uia_window()
            return is_ribbon_button_enabled(uia_win, "Pull All From AccuLoad")
        except Exception:
            return False

    def wait_for_device_connection(self, timeout=10):
        """
        Poll is_device_connected() to determine whether AccuMate has
        established a live connection to a physical AccuLoad device.

        Returns True if connected within `timeout` seconds, False
        otherwise. Never raises - callers should treat False as "no device
        reachable" rather than an error.
        """
        start = time.time()

        while time.time() - start < timeout:
            if self.is_device_connected():
                return True
            time.sleep(0.5)

        return False
