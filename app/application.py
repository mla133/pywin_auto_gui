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


class AccuMateApp:

    def __init__(self):
        self.app = Application(backend=BACKEND).start(APP_EXE)
        self._uia_app = None

    def get_window(self):
        # Get the window spec by title suffix + main-frame class name
        win_spec = self.app.window(title_re=_TITLE_RE, class_name_re=_CLASS_NAME_RE)

        # Wait on the spec, not the wrapper
        win_spec.wait("exists enabled visible ready", timeout=10)

        # Convert to a wrapper
        return win_spec.wrapper_object()

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
