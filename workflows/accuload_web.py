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

from selenium.webdriver.common.by import By

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

        # NOTE (confirmed live): `UserInterfaceSeleniumAPI` only creates its
        # `driver` ONCE, as a module-level side effect the FIRST time it's
        # imported in this process (`driver = create_driver()` at the bottom
        # of the module) - Python caches imported modules in sys.modules, so
        # every later `import UserInterfaceSeleniumAPI` in the same process
        # (e.g. a second `AccuLoadWebSession` in the same test run, or a
        # retry loop) returns that SAME cached module object, not a fresh
        # one. Since `__exit__` below calls `self.ui.driver.quit()`, any
        # session after the very first one in a process would otherwise
        # reuse an already-quit driver and fail permanently (chromedriver's
        # own local server is gone, "connection actively refused" for every
        # subsequent attempt, forever, until the process restarts). Always
        # create and (re)assign a genuinely fresh driver here instead of
        # trusting the module-level one from import time.
        self.ui.driver = self.ui.create_driver(mode=self.browser_mode)
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


def _js_click(ui, elem_id, settle=1.5):
    """
    Shared navigation primitive for every helper below: click an element by
    ID via JS (`execute_script`), not a native WebDriver `.click()`, with a
    short settle delay and a fresh `find_element` right before the click.
    Confirmed live (see this module's docstring/history) that native clicks
    on this device's jQuery Mobile UI intermittently silently no-op or raise
    ElementClickInterceptedException/StaleElementReferenceException while a
    page transition is still binding handlers or replacing DOM nodes -
    switching to a JS click plus this settle/refetch pattern reliably avoids
    that class of flake for every element observed so far (overlay, popup,
    breadcrumb, tile buttons, dropdown buttons).
    """
    driver = ui.driver
    time.sleep(settle)
    el = driver.find_element(By.ID, elem_id)
    driver.execute_script("arguments[0].click();", el)
    time.sleep(1)


def _submit_program_mode_password_if_prompted(ui, password, timeout=3):
    """
    If entering Program Mode triggered the device's "Enter Password" popup
    (`popupLogin`, initially `display:none` in the DOM on every screen -
    only actually shown, per a live security-level check, after clicking
    `btnProgramMode`), enter `password` and submit. Silently does nothing if
    the popup never becomes visible within `timeout` seconds (i.e. no
    password was required this time - confirmed live this varies with the
    device's currently-configured security level).

    The password field (`passwordPL`) is a hidden <input type="password">
    with a shadow display div (`passwordPL-H`) - same "-H" pattern as the
    read-only fields in `read_field()`. Rather than reverse-engineering
    exactly which on-screen keypad widget this specific field uses (unlike
    the numeric fields `enterNumericFieldValue` targets, this is a
    password-type field, which may not use the same jQuery Mobile numeric
    keyboard), the value is set directly via JS on the hidden input plus a
    dispatched `input` event (so any bound handlers relying on that event
    still fire), then mirrored onto the visible `-H` div, before clicking
    Submit.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    driver = ui.driver

    try:
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.ID, "passwordPL-H"))
        )
    except TimeoutException:
        return  # No password prompt appeared - nothing to do.

    print("[INFO] Program Mode password prompt appeared - submitting configured passcode")
    driver.execute_script(
        """
        var input = document.getElementById('passwordPL');
        var display = document.getElementById('passwordPL-H');
        input.value = arguments[0];
        input.dispatchEvent(new Event('input', {bubbles: true}));
        input.dispatchEvent(new Event('change', {bubbles: true}));
        if (display) { display.textContent = arguments[0]; }
        """,
        str(password),
    )
    time.sleep(0.5)
    _js_click(ui, "btnPasswordSubmit")


def reset_to_program_mode(ui, password=None):
    """
    Reset navigation to the top-level Program Mode menu via its breadcrumb
    (`breadCrumb1`), regardless of whatever sub-screen the device's web UI
    is currently sitting on. Necessary because the physical device retains
    whatever screen a PRIOR script/test session left it on - there is no
    "start fresh" reload short of this breadcrumb click. Safe to call
    unconditionally.

    Handles two starting states:
      - Currently on the outer "Main"/Index page, outside Program Mode
        entirely (breadCrumb1's text reads "Main") - e.g. after a prior
        session cleanly did "Save/Cancel and Exit" - JS-clicks
        `btnProgramMode` to enter it first, then submits `password` (or, if
        not given, the `ACCULOAD_PROGRAM_MODE_PASSWORD` env var - NEVER
        hardcoded in source) if the device's "Enter Password" popup appears
        - see `_submit_program_mode_password_if_prompted`. Whether this
        popup appears at all depends on the device's currently-configured
        security level, confirmed live to vary between sessions.
      - Already inside Program Mode, whether sitting at its own top-level
        menu or several screens deep (breadCrumb1's text is anything other
        than "Main", e.g. "Program Mode", "Config", etc.) - JS-clicks
        `breadCrumb1` itself, which always returns to the top of the CURRENT
        breadcrumb trail (i.e. Program Mode's own top-level menu), regardless
        of how deep the prior sub-screen was. No password needed here since
        we're already inside.

    Note `breadCrumb1` is present on EVERY screen of this UI (it's the
    global breadcrumb trail, not something specific to Program Mode) -
    confirmed live that checking only for its presence (an earlier version
    of this function) is not enough to tell which of the two cases above
    applies; its TEXT must be inspected instead.

    Either way, waits for `btnConfig` to actually be present before
    returning - confirmed live that `UserInterfaceSeleniumAPI`'s
    `clickConfigButton()`/`clickSystemButton()`/etc. do a bare
    `find_element()` with NO wait of their own, so calling them immediately
    after a breadcrumb/menu-entry click (which triggers a jQuery Mobile page
    transition that isn't instant) can raise NoSuchElementException even
    though the button appears moments later - this wait is what makes every
    get_* helper below reliable regardless of that transition's timing.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver = ui.driver

    if password is None:
        password = os.environ.get("ACCULOAD_PROGRAM_MODE_PASSWORD")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "breadCrumb1")))
    crumb_text = driver.find_element(By.ID, "breadCrumb1").text.strip()

    if crumb_text == "Main":
        # Outside Program Mode entirely - enter it first.
        _js_click(ui, "btnProgramMode")
        if password is not None:
            _submit_program_mode_password_if_prompted(ui, password)
    else:
        # Already inside Program Mode somewhere - jump back to its top menu.
        _js_click(ui, "breadCrumb1")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "btnConfig")))


def read_field(ui, field_id):
    """
    Generic read of a single field's displayed value by element ID. Most
    read-only/numeric-display fields on this UI render as a shadow display
    div named "<field_id>-H" (e.g. "ip_addr-H") holding the visible text,
    with a same-named hidden <input> holding the raw value/attributes used
    for editing - this reads the "-H" display div if present, falling back
    to the plain element's own text (covers dropdown/button-style fields
    like "arm1_config" or "permissive_1_type", which have no "-H" variant
    and show their current value directly as the button's text).
    """
    driver = ui.driver
    try:
        return driver.find_element(By.ID, field_id + "-H").text.strip()
    except Exception:
        return driver.find_element(By.ID, field_id).text.strip()


def get_number_of_load_arms(ui):
    """Program Mode -> Config -> System Layout ("001 Number of Load Arms")."""
    reset_to_program_mode(ui)
    ui.clickConfigButton()
    _js_click(ui, "Config-1")
    return read_field(ui, "num_physical_arms")


def get_pulse_input_tag(ui, pulse_in_number):
    """
    Program Mode -> Config -> Pulse Inputs -> Pulse In <N> ("1100 Pulse
    Input Tag"). `pulse_in_number` is 1-based, matching the device's own
    "Pulse In 1"/"Pulse In 2"/... numbering.
    """
    reset_to_program_mode(ui)
    ui.clickConfigButton()
    _js_click(ui, "btnPulseIn")
    _js_click(ui, "btnPulseIn" + str(pulse_in_number))
    return read_field(ui, "pulse_in_tag")


def get_digital_input_tag(ui, digital_in_number):
    """
    Program Mode -> Config -> Digital Inputs -> Dig In <N> ("1300 Digital
    Input Tag"). `digital_in_number` is 1-based.
    """
    reset_to_program_mode(ui)
    ui.clickConfigButton()
    _js_click(ui, "btnDigIn")
    _js_click(ui, "btnDigIn" + str(digital_in_number))
    return read_field(ui, "dig_in_tag")


def get_arm_permissive_sense(ui, arm_number, permissive_number=1):
    """
    Program Mode -> Arms -> Arm <N> -> General Purpose ("101 Permissive 1
    Sense" for permissive_number=1, "104 Permissive 2 Sense" for 2, etc).
    Both `arm_number` and `permissive_number` are 1-based.
    """
    reset_to_program_mode(ui)
    ui.clickArmsButton()
    _js_click(ui, "btnArm" + str(arm_number))
    _js_click(ui, "Arm-40")  # "100 General Purpose" category tile
    return read_field(ui, "permissive_" + str(permissive_number) + "_type")


def get_ip_netmask_gateway(ui):
    """
    Program Mode -> System -> Communications -> Host Interface ("735 IP
    Address"/"736 Netmask"/"737 Gateway"). Returns a (ip, netmask, gateway)
    tuple of strings. Scrolls the field list down first since Gateway sits
    below the initial fold on this screen.
    """
    reset_to_program_mode(ui)
    ui.clickSystemButton()
    _js_click(ui, "btnComm")
    _js_click(ui, "Comm-18")  # "700 Host Interface" category tile

    # Gateway is below the visible fold - scroll the field list down a few
    # times (each click advances one row) before reading any of these three
    # fields, so all three are guaranteed to be rendered/attached.
    driver = ui.driver
    for _ in range(4):
        try:
            btn = driver.find_element(By.ID, "SelComm-scrollbtnDown")
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.5)
        except Exception:
            break

    return (
        read_field(ui, "ip_addr"),
        read_field(ui, "netmask"),
        read_field(ui, "gateway"),
    )

