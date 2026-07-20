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
"""

import os
import sys

# Local checkout of the internal Selenium API repo. Override via the
# ACCULOAD_TOOLS_REPO env var if checked out elsewhere.
INTERNAL_TOOLS_REPO = os.environ.get(
    "ACCULOAD_TOOLS_REPO",
    r"C:\Users\allenma\SoftwareDevelopment\Internal-Software-Tools.automated_testing",
)
INTERNAL_TOOLS_MODULES_DIR = os.path.join(INTERNAL_TOOLS_REPO, "python", "modules")


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
    """

    def __init__(self, device_ip, secret="HMI", browser_mode="local"):
        self.device_ip = device_ip
        self.url = f"http://{device_ip}/?secret={secret}"
        self.browser_mode = browser_mode
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

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ui is not None:
            try:
                self.ui.driver.quit()
            except Exception as e:
                print(f"[WARN] Failed to close AccuLoad web session: {e}")

        return False
