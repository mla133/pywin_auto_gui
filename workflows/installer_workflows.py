"""
Workflows for driving the compiled AccuMate Inno Setup installer
(scenarios/regression.md G1-G5). This is a SEPARATE application/process from
AccuMate.exe itself (app/application.py) - the installer is built from
`AccuMateIVInstallerScript.iss` (Inno Setup 6) in a sibling dev repo:
    C:\\Users\\allenma\\SoftwareDevelopment\\acculoadiv.AccuMate\\
Compiled via `ISCC.exe AccuMateIVInstallerScript.iss` -> produces
`install\\Installer for AccuMate for AccuLoad IV <version>.exe`.

Installing/uninstalling via this compiled installer does NOT touch the
Release\\AccuMate.exe build that app/application.py's APP_EXE points at (that
is the raw build output the rest of this repo's tests drive directly) - the
installer's [Files] section copies that exe into Program Files/AppData, a
separate location. So exercising real install/uninstall cycles here is safe
and does not risk breaking any other regression test in this repo.

Wizard flow confirmed via live probe (see tests/unit_test_installer_probe.py)
for a regular (non-admin) user - "Install for current user" path:
    Welcome -> License -> Select Components -> Select Destination
    (a custom [Code] dirSelectionPage) -> Ready to Install -> Install -> Finish
As a regular user, the Tasks page (desktop icon) is skipped entirely, since
that Task's Check: CheckTask requires IsAdmin - matches regression.md G3's
"[NA] - needs admin rights" note on the desktop-icon step. The admin/
"all users" flow (G4/G5) additionally shows an elevation prompt and the
Tasks page, and offers a choice between "main\\all"/"main\\current" components
- not yet live-verified in this environment (needs an elevated Python/pytest
session), see module docstring TODO below.

Key controls (Inno Setup's own "New" wizard UI skin, class prefix TNew*):
    - Wizard window: title "Setup - AccuMate for AccuLoad IV", class "TWizardForm"
    - Nav buttons: "&Back" / "&Next" / "Cancel" (class "TNewButton") on every
      page except Ready to Install, where the affirmative button is instead
      labeled "&Install" (also "TNewButton").
    - License page: license text is a read-only "TRichEditViewer"; acceptance
      is two mutually-exclusive "TNewRadioButton"s titled
      "I &accept the agreement" / "I &do not accept the agreement" - Next
      stays disabled until "I accept..." is selected.
    - Select Components page: "TNewComboBox" (Setup Type - "Compact
      installation" is the regular-user default) + "TNewCheckListBox"
      (component checkboxes, corresponds 1:1 to the .iss [Components]
      section: main/main\\all/main\\current/sample/associate/associateAM3).
    - Select Destination page: a custom page added by the script's own
      [Code] section (InitializeWizard's CreateInputDirPage) - a plain
      "TEdit" + "B&rowse..." button, NOT Inno's built-in wpSelectDir page
      (DisableDirPage=yes in [Setup]).
    - Ready to Install page: a read-only "TNewMemo" summarizing the chosen
      setup type/components/Start Menu folder, plus the "&Install" button.

The installer relaunches itself as a "<name>.tmp" child process that owns
the real wizard window - Application(...).start(INSTALLER_EXE) attaches to
the launcher, not the wizard, so window lookup must scan the Desktop for the
real "Setup - ..." window rather than assuming the started process owns it
(see find_installer_window below - this was the key gotcha discovered while
building this module and is the reason a naive Application(...).window(...)
lookup against the launched process times out).

TODO (not yet automated/live-verified):
    - Admin/"all users" install flow (G4/G5): elevation prompt, Tasks page
      (desktop icon), "main\\all" vs "main\\current" component choice.
    - Uninstall flow (G1/G3/G4/G5 step 5) - locating/launching
      "{uninstallexe}" and its own confirmation dialogs.
    - G1's "block while running" (IsAppRunning() MsgBox) - needs AccuMate.exe
      running from the SAME installed location the installer would upgrade,
      which isn't the case for a fresh install-to-a-clean-directory test.
"""
import time

from pywinauto import Application, Desktop

INSTALLER_EXE = (
    r"C:\Users\allenma\SoftwareDevelopment\acculoadiv.AccuMate\install"
    r"\Installer for AccuMate for AccuLoad IV 1.12.exe"
)

_WIZARD_CLASS = "TWizardForm"
_BUTTON_CLASS = "TNewButton"
_NEXT_TITLE = "&Next"
_BACK_TITLE = "&Back"
_INSTALL_TITLE = "&Install"
_CANCEL_TITLE = "Cancel"
_ACCEPT_RADIO_TITLE = "I &accept the agreement"
_DECLINE_RADIO_TITLE = "I &do not accept the agreement"


def launch_installer(installer_exe=INSTALLER_EXE, timeout=15):
    """
    Launch the compiled Inno Setup installer and return a pywinauto
    WindowSpecification for its real wizard window.

    The installer exe relaunches itself as a "<name>.tmp" child process that
    owns the actual "Setup - ..." wizard window - the process
    Application(...).start() attaches to is just the launcher and never
    shows this window itself, so we scan the Desktop for a window whose
    title starts with "Setup" instead of relying on the started process
    handle. This mirrors app/application.py's own title-based window lookup
    pattern (get_window()/get_uia_window()), adapted for a process that
    re-execs itself.
    """
    Application(backend="win32").start(installer_exe)

    win = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in Desktop(backend="win32").windows():
            try:
                title = w.window_text()
            except Exception:
                continue
            if title.startswith("Setup"):
                win = w
                break
        if win:
            break
        time.sleep(0.5)

    if win is None:
        raise RuntimeError(
            f"Installer wizard window did not appear within {timeout}s "
            f"(looked for a window titled 'Setup...')"
        )

    app = Application(backend="win32").connect(handle=win.handle)
    win_spec = app.window(handle=win.handle)
    win_spec.wait("exists enabled visible ready", timeout=timeout)
    return win_spec


def click_next(win_spec, timeout=5):
    """Click the wizard's '&Next' button. Returns False (does not raise) if
    the button isn't found/enabled - e.g. on the License page before
    accepting, or on Ready to Install where the button is '&Install' instead.
    """
    try:
        btn = win_spec.child_window(title=_NEXT_TITLE, class_name=_BUTTON_CLASS)
        btn.wait("enabled visible", timeout=timeout)
        btn.click_input()
        time.sleep(1)
        return True
    except Exception:
        return False


def click_back(win_spec, timeout=5):
    """Click the wizard's '&Back' button."""
    btn = win_spec.child_window(title=_BACK_TITLE, class_name=_BUTTON_CLASS)
    btn.wait("enabled visible", timeout=timeout)
    btn.click_input()
    time.sleep(1)


def click_install(win_spec, timeout=5):
    """Click the '&Install' button on the Ready to Install page - begins the
    real file-copy/install. Only call this once you've verified the Ready to
    Install summary (see is_ready_to_install_page) matches what the test
    expects (setup type/components), since this is not easily reversible.
    """
    btn = win_spec.child_window(title=_INSTALL_TITLE, class_name=_BUTTON_CLASS)
    btn.wait("enabled visible", timeout=timeout)
    btn.click_input()
    time.sleep(1)


def click_cancel(win_spec, timeout=5):
    """Click 'Cancel' and confirm the resulting 'Exit Setup?' MsgBox (Yes)."""
    btn = win_spec.child_window(title=_CANCEL_TITLE, class_name=_BUTTON_CLASS)
    btn.wait("enabled visible", timeout=timeout)
    btn.click_input()
    time.sleep(1)
    try:
        confirm_app = Application(backend="win32").connect(title_re=".*Setup$")
        confirm_app.top_window().child_window(
            title="&Yes", class_name="Button"
        ).click_input()
    except Exception:
        # Some Cancel points (e.g. before any real state change) may exit
        # immediately without a confirmation prompt.
        pass


def is_license_page(win_spec):
    """True if the wizard's current page is the License Agreement page."""
    return win_spec.child_window(
        title=_ACCEPT_RADIO_TITLE, class_name="TNewRadioButton"
    ).exists()


def accept_license(win_spec):
    """Select 'I accept the agreement' on the License page."""
    radio = win_spec.child_window(
        title=_ACCEPT_RADIO_TITLE, class_name="TNewRadioButton"
    )
    radio.wait("enabled visible", timeout=5)
    radio.click_input()
    time.sleep(0.5)


def decline_license(win_spec):
    """Select 'I do not accept the agreement' on the License page (used to
    verify Next/Install stays disabled/blocked when declined)."""
    radio = win_spec.child_window(
        title=_DECLINE_RADIO_TITLE, class_name="TNewRadioButton"
    )
    radio.wait("enabled visible", timeout=5)
    radio.click_input()
    time.sleep(0.5)


def is_ready_to_install_page(win_spec):
    """True if the wizard's current page is Ready to Install (has the
    '&Install' button instead of '&Next')."""
    return win_spec.child_window(
        title=_INSTALL_TITLE, class_name=_BUTTON_CLASS
    ).exists()


def get_ready_to_install_summary(win_spec):
    """Return the Ready to Install page's read-only summary text (setup
    type, selected components, Start Menu folder) as a single string, for
    asserting the wizard captured the expected choices before committing to
    a real install."""
    memo = win_spec.child_window(class_name="TNewMemo")
    return memo.wrapper_object().window_text()
