"""
Bridge to the AccuLoad device's own embedded web HMI, via the company's
internal Selenium API (`UserInterfaceSeleniumAPI.py`, checked out separately
at `INTERNAL_TOOLS_REPO` below, branch `accumate_ai`).

Why this exists: several regression.md sections (A7-A14) require setting or
verifying values on the AccuLoad device's own web UI, not just AccuMate's
desktop app - something no amount of pywinauto automation can reach. The
internal Selenium API already knows how to drive that web UI; this module
just wraps it so it fits into pywin_auto_gui's fixture/test conventions.

Import-time gotcha this module works around: `UserInterfaceSeleniumAPI`
launches a Chrome browser as a MODULE-LEVEL side effect
(`driver = create_driver()` runs at import time), driven by env vars
(`SELENIUM_BROWSER_MODE`, etc.) read at that same moment. To avoid launching
a browser merely by importing this file (e.g. during pytest collection), the
internal module is imported LAZILY, inside `AccuLoadWebSession.__enter__`,
after the required env vars have been set for that specific session.

Real device navigation flow (confirmed live - this is the actual
user-facing path, NOT the previously-used `?secret=HMI` bypass link, which
lands on the same HTML but skips the take-over handshake below and was
found to be an incorrect shortcut for this purpose):
  1. GET `http://<device_ip>/` -> lands on the "Landing" page, which offers
     three real buttons: "Control AccuLoad" (`id=btnObserve`, actually
     navigates to `?mode=observe#Follower/Index` despite the "observe" in
     the URL), "View AccuLoad" (`id=btnBrowse`, `?mode=browse` - read-only
     Dynamic Display viewer), and "Launch VLR" (`id=btnStartVLR`).
  2. Click "Control AccuLoad" (`btnObserve`) -> the device's live screen
     mirrors into the browser, titled "AccuLoad IV Follower", but a
     full-page transparent overlay (`id=takeOverLandingPageBtn`) blocks all
     clicks on the mirrored UI until you explicitly take over control.
  3. Click that overlay -> opens a "Follower Menu" popup ("Please Select An
     Option") with three buttons: "Take Over" (`id=btnPopup0`), "Return To
     Menu" (`id=btnPopup1`), "Cancel" (`id=btnPopup2`).
  4. Click "Take Over" (`btnPopup0`) -> the overlay and popup are dismissed
     and the mirrored UI becomes genuinely interactive (confirmed live:
     clicking `btnProgramMode` afterward actually navigates the device to
     `?mode=observe#ProgramMode` and shows the real Program Mode menu -
     Config/System/Bays/Arms/Recipes/Split Architecture/Cancel and
     Exit/Save and Exit, matching exactly what `UserInterfaceSeleniumAPI`'s
     `clickConfigButton()`/`clickSystemButton()`/etc. already expect).
"""

import os
import sys
import time

# Local checkout of the internal Selenium API repo. Override via the
# ACCULOAD_TOOLS_REPO env var if checked out elsewhere.
INTERNAL_TOOLS_REPO = os.environ.get(
    "ACCULOAD_TOOLS_REPO",
    r"C:\Users\allenma\SoftwareDevelopment\Internal-Software-Tools.automated_testing",
)
INTERNAL_TOOLS_MODULES_DIR = os.path.join(INTERNAL_TOOLS_REPO, "python", "modules")

_LANDING_CONTROL_BUTTON_ID = "btnObserve"
_TAKEOVER_OVERLAY_ID = "takeOverLandingPageBtn"
_TAKEOVER_POPUP_BUTTON_ID = "btnPopup0"


class AccuLoadWebSession:
    """
    Lazily-initialized wrapper around `UserInterfaceSeleniumAPI`, scoped to a
    single AccuLoad device's web HMI. Use as a context manager so the browser
    is always closed:

        with AccuLoadWebSession(device_ip="10.55.66.70") as web:
            web.ui.clickConfigButton()
            web.ui.clickSystemButton()
            value = web.ui.getFieldText("some_field_id")

    `web.ui` is the imported `UserInterfaceSeleniumAPI` module itself, so any
    of its ~66 existing functions (and the new `enterNumericFieldValue`/
    `clearNumericField` helpers added for this bridge) are available directly
    - this class deliberately doesn't re-wrap every function individually.

    On entry, drives the real "Control AccuLoad" -> take-over handshake
    described in this module's docstring, so `web.ui`'s functions land on a
    genuinely interactive page rather than a click-blocked mirror.
    """

    def __init__(self, device_ip, browser_mode="local", takeover_timeout=10):
        self.device_ip = device_ip
        self.url = f"http://{device_ip}/"
        self.browser_mode = browser_mode
        self.takeover_timeout = takeover_timeout
        self.ui = None  # set to the imported module in __enter__

    def __enter__(self):
        if not os.path.isdir(INTERNAL_TOOLS_MODULES_DIR):
            raise RuntimeError(
                f"Internal Selenium tools repo not found at {INTERNAL_TOOLS_REPO!r}. "
                "Set ACCULOAD_TOOLS_REPO to its checkout location."
            )

        if INTERNAL_TOOLS_MODULES_DIR not in sys.path:
            sys.path.insert(0, INTERNAL_TOOLS_MODULES_DIR)

        # Must be set BEFORE import, since the module creates its driver at
        # import time using these.
        os.environ["SELENIUM_BROWSER_MODE"] = self.browser_mode
        os.environ["SELENIUM_TEST_URL"] = self.url

        # Import name intentionally not module-level in this file - see
        # docstring above for why (avoids launching Chrome at collection time).
        import UserInterfaceSeleniumAPI as ui  # noqa: N813 (external module's naming)

        self.ui = ui
        self.ui.driver.get(self.url)

        self._control_accuload()

        return self

    def _control_accuload(self):
        """
        Drive the real "Control AccuLoad" -> take-over handshake from the
        device's Landing page, so subsequent clicks via `self.ui`'s
        functions land on a genuinely interactive page. See this module's
        docstring for the full flow this replicates.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException

        driver = self.ui.driver

        print("[STEP] Clicking 'Control AccuLoad' on the device's Landing page")
        WebDriverWait(driver, self.takeover_timeout).until(
            EC.element_to_be_clickable((By.ID, _LANDING_CONTROL_BUTTON_ID))
        ).click()

        try:
            print("[STEP] Dismissing the take-over overlay (mirrored view is click-blocked until taken over)")
            # NOTE: use `presence_of_element_located` + a JS click here, not
            # `element_to_be_clickable().click()`. The overlay is a bare,
            # zero-content full-page <div> (no text/children) inserted by a
            # jQuery Mobile page transition; a real WebDriver click on it was
            # observed to intermittently no-op or raise
            # ElementClickInterceptedException while the transition settles,
            # even though the element is genuinely present and on top. A JS
            # click bypasses that native-event flakiness.
            WebDriverWait(driver, self.takeover_timeout).until(
                EC.presence_of_element_located((By.ID, _TAKEOVER_OVERLAY_ID))
            )
            # A short settle delay before clicking is needed here - clicking
            # immediately after the overlay is merely present in the DOM was
            # observed live to silently no-op (the underlying jQuery Mobile
            # page transition that inserts the overlay hadn't finished
            # binding its click handler yet), even though the click itself
            # didn't raise any exception. Re-find the element fresh right
            # before clicking (rather than reusing the reference above) since
            # the transition can also replace the DOM node during the delay,
            # which would otherwise raise StaleElementReferenceException.
            time.sleep(1.5)
            overlay = driver.find_element(By.ID, _TAKEOVER_OVERLAY_ID)
            driver.execute_script("arguments[0].click();", overlay)

            print("[STEP] Selecting 'Take Over' on the Follower Menu popup")
            WebDriverWait(driver, self.takeover_timeout).until(
                EC.presence_of_element_located((By.ID, _TAKEOVER_POPUP_BUTTON_ID))
            )
            time.sleep(1.5)
            popup_btn = driver.find_element(By.ID, _TAKEOVER_POPUP_BUTTON_ID)
            driver.execute_script("arguments[0].click();", popup_btn)

            # Wait for the click-blocking overlay to actually disappear
            # rather than a fixed sleep - it can briefly persist after the
            # "Take Over" click resolves.
            WebDriverWait(driver, self.takeover_timeout).until(
                EC.invisibility_of_element_located((By.ID, _TAKEOVER_OVERLAY_ID))
            )
            time.sleep(0.5)
        except TimeoutException:
            # No overlay appeared (e.g. this session already has control, or
            # a future firmware skips the handshake when nobody else is
            # connected) - proceed, the page is presumably already
            # interactive.
            print("[INFO] No take-over overlay/popup appeared - assuming already in control")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ui is not None:
            try:
                self.ui.driver.quit()
            except Exception as e:
                print(f"[WARN] Failed to close AccuLoad web session: {e}")

        return False


def ensure_run_ready_mode(ui, timeout=5):
    """
    Best-effort: if the device's web UI is currently sitting inside Program
    Mode (e.g. left over from a previous test run/session), back out to
    Run/Ready Mode via "Cancel and Exit" -> Yes (discarding any unsaved
    Program Mode navigation state, not the device's actual saved
    configuration) so callers can rely on starting from a known screen.
    Silently does nothing if Program Mode's exit button isn't present
    (i.e. the device is already outside Program Mode).
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    driver = ui.driver

    try:
        # JS click (not a native WebDriver click) - see the matching note in
        # `AccuLoadWebSession._control_accuload` for why: a leftover
        # take-over overlay can still be present/settling on top of this
        # button and a native click intermittently raises
        # ElementClickInterceptedException even though the button itself is
        # genuinely present.
        abort_btn = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "program_mode_abort"))
        )
        driver.execute_script("arguments[0].click();", abort_btn)

        time.sleep(1)
        yes_btn = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "btnPopup0"))
        )
        driver.execute_script("arguments[0].click();", yes_btn)

        # After confirming "Yes", the device briefly shows a "reverting
        # changes" transition before it actually leaves Program Mode - a
        # short fixed pause here isn't enough (confirmed live: the Program
        # Mode main menu was still showing moments after the click). Poll
        # for `program_mode_abort` to actually disappear instead of assuming
        # a fixed delay is enough.
        WebDriverWait(driver, max(timeout, 15)).until(
            EC.invisibility_of_element_located((By.ID, "program_mode_abort"))
        )
        print("[INFO] Backed out of a leftover Program Mode session via Cancel and Exit -> Yes")
    except TimeoutException:
        pass

