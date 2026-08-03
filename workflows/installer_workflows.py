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
separate location.

*** CRITICAL, LIVE-CONFIRMED GOTCHA (do not repeat this mistake) ***
The paragraph above about install/uninstall cycles being fully isolated
from the rest of this repo's tests is only TRUE for the {app} (Program
Files/AppData\\Local\\Guidant\\AccuMate\\<version>\\AccuMate.exe) executable
itself - it is FALSE for the shared default-data directory. AccuMate.exe's
own C++/MFC code resolves its bundled default files (DefaultAL4.dat,
Default_DriverDB.dat) via a HARDCODED path formula -
SHGetFolderPath(CSIDL_LOCAL_APPDATA) + "Guidant\\AccuMate\\" + AppVersion,
i.e. "%LOCALAPPDATA%\\Guidant\\AccuMate\\<version>\\" - NOT relative to its
own exe directory, and NOT via any Windows registry "install path" key.
This is confirmed both by AccuMateIVInstallerScript.iss's own [Files]/
[Icons] sections (which deliberately copy DefaultAL4.dat/
Default_DriverDB.dat into "{******appdata}\\Guidant\\AccuMate\\{#AppVersion}\\"
and set shortcut WorkingDir there too, regardless of {app}'s actual install
location) and by live testing: EVERY copy of AccuMate.exe that shares the
same AppVersion (1.12) - whether the raw Release\\AccuMate.exe dev build
this repo's other tests drive, or a real installed copy - reads its
default config from that SAME shared AppData folder and refuses to start
at all ("Unable to find DefaultAL4.dat. AccuMate can not start.") if it's
missing.

A prior session ran `Remove-Item -Recurse -Force
"...\\AppData\\Local\\Guidant\\AccuMate\\1.12"` to clean up a broken
partial-install test artifact, not realizing this folder is ALSO the raw
dev build's own required default-data location - this broke every single
test in the entire repo that launches AccuMateApp() (not just the
installer tests) until DefaultAL4.dat/Default_DriverDB.dat were manually
restored (copied from the sibling repo's
AccuMate\\DefaultAL4.dat/Default_DriverDB.dat source files, which are the
same files the installer itself bundles).

**NEVER delete or recursively wipe
"%LOCALAPPDATA%\\Guidant\\AccuMate\\<version>\\" as part of any
install/uninstall test cleanup.** If a test needs to remove a broken
partial *install* (i.e. the {app} exe/uninstaller under Program
Files/AppData\\Local\\Guidant\\AccuMate\\<version>\\ - see
CURRENT_USER_INSTALL_ROOT below, which happens to be the exact same path
prefix), only ever remove specific known-installer-only artifacts
(AccuMate.exe, unins*.exe, the Start Menu folder) - never the whole
version directory - or better, restore DefaultAL4.dat/Default_DriverDB.dat
immediately afterward from the sibling installer repo's own AccuMate\\
source folder if a wipe is truly unavoidable.

So exercising real install/uninstall cycles here is safe for the {app}
executable location, but real uninstalls (run_uninstaller()) may remove
files from this SAME shared AppData directory - always verify
DefaultAL4.dat/Default_DriverDB.dat still exist there afterward (and
restore them immediately if not) before considering any install/uninstall
test cycle complete.

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

KNOWN INSTALLER BUG (discovered live 2026-07-23, NOT a bug in this repo):
    This dev machine carries leftover Windows "uninstall registry" entries
    from real, manual installs of OLDER AccuMate versions done outside of
    this automation (observed: 1.9, 1.11, 0.10, and the old "AccuMate III.NET"
    product) - their original uninstaller .exe files no longer exist on
    disk. AccuMateIVInstallerScript.iss's [Code] section detects ANY such
    stale entry (its "old version" check isn't scoped to the specific
    version being installed) and pops "An old version of AccuMate was
    detected. Do you want to uninstall it?" - but since the referenced
    uninstaller can't actually run, this MsgBox reappears identically
    whether Yes or No is clicked, hanging the wizard in an infinite loop
    that never reaches the Finish page. This was confirmed by clicking both
    Yes and No repeatedly with no change. This is a genuine bug in the
    installer script's own Pascal logic - not something pywinauto/this test
    suite can safely click through, and out of scope for this Python repo to
    fix (the fix would need to live in AccuMateIVInstallerScript.iss itself,
    e.g. scoping the "old version" check to the AppId being installed, or
    tolerating a missing old uninstaller gracefully).
    `find_stale_accumate_uninstall_entries()` below detects this condition
    up front so callers/tests can skip real-install tests with a clear
    explanation instead of hanging. `wait_for_finish_and_close()` also
    detects the loop defensively (bounded retries) and raises
    `OldVersionLoopBug` with the same explanation if it happens anyway.
"""
import os
import shutil
import tempfile
import time
import winreg

from pywinauto import Application, Desktop

INSTALLER_EXE = (
    r"C:\Users\allenma\SoftwareDevelopment\acculoadiv.AccuMate\install"
    r"\Installer for AccuMate for AccuLoad IV 1.12.exe"
)

# Matches the .iss script's `#define AppVersion GetStringFileInfo(...)` -
# read from Release\AccuMate.exe's own ProductVersion at compile time.
# Update this if the installer is ever recompiled against a newer build.
APP_VERSION = "1.12"

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


_UNINSTALL_KEY_ROOTS = [
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
]


def find_stale_accumate_uninstall_entries(current_version=APP_VERSION):
    """
    Scan the Windows uninstall registry for AccuMate entries that do NOT
    belong to current_version. See the "KNOWN INSTALLER BUG" note in this
    module's docstring - any such entry triggers an infinite "old version
    detected" dialog loop in the installer that never reaches Finish.

    Returns a list of (registry_key_path, DisplayName) tuples; empty if the
    machine is clean (only the current version, or nothing, installed).
    """
    stale = []
    for hive, path in _UNINSTALL_KEY_ROOTS:
        try:
            key = winreg.OpenKey(hive, path)
        except OSError:
            continue
        with key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                except OSError:
                    break
                i += 1
                if current_version in subkey_name:
                    continue
                try:
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                except OSError:
                    continue
                if "accumate" in display_name.lower():
                    stale.append((rf"{path}\{subkey_name}", display_name))
    return stale


class OldVersionLoopBug(RuntimeError):
    """
    Raised by wait_for_finish_and_close() when the installer's "old version
    detected" MsgBox reappears after being dismissed multiple times - a
    genuine installer script bug (see this module's docstring), not
    something safe to click through indefinitely. Callers/tests should treat
    this the same as finding entries via
    find_stale_accumate_uninstall_entries() up front: skip the real-install
    test with a clear explanation rather than hang or retry forever.
    """


def _find_old_version_prompt():
    """Return the Desktop window for the 'old version detected' MsgBox if
    currently showing, else None."""
    for w in Desktop(backend="win32").windows():
        try:
            if w.window_text() != "Setup":
                continue
            spec = Application(backend="win32").connect(handle=w.handle).window(handle=w.handle)
            for c in spec.descendants(class_name="Static"):
                if "old version" in c.window_text().lower():
                    return spec
        except Exception:
            continue
    return None


def wait_for_finish_and_close(win_spec, timeout=90):
    """
    Wait for the Installing page to finish and the wizard to reach its
    Finish page, then click '&Finish' to close it. Call only after
    click_install() - this is the real file-copy step and can take a little
    while, hence the longer default timeout.

    Defensively watches for the "old version detected" MsgBox loop bug
    (see this module's docstring) - dismisses it (clicking Yes) up to twice,
    and raises OldVersionLoopBug with a clear explanation if it reappears a
    third time rather than hanging for the full timeout.
    """
    finish_btn = win_spec.child_window(title="&Finish", class_name=_BUTTON_CLASS)
    deadline = time.time() + timeout
    old_version_prompts_seen = 0
    while time.time() < deadline:
        prompt = _find_old_version_prompt()
        if prompt is not None:
            old_version_prompts_seen += 1
            if old_version_prompts_seen > 2:
                raise OldVersionLoopBug(
                    "Installer's 'old version detected' dialog reappeared "
                    "after being dismissed - this is a known installer "
                    "script bug triggered by stale AccuMate uninstall "
                    "registry entries on this machine (see "
                    "find_stale_accumate_uninstall_entries() and this "
                    "module's docstring)."
                )
            prompt.child_window(title="&Yes", class_name="Button").click_input()
            time.sleep(1)
            continue
        if finish_btn.exists() and finish_btn.wrapper_object().is_enabled():
            break
        time.sleep(0.5)
    else:
        raise TimeoutError("timed out waiting for the installer's Finish page")

    finish_btn.click_input()
    time.sleep(1)


CURRENT_USER_INSTALL_ROOT = r"C:\Users\allenma\AppData\Local\Guidant\AccuMate"


def get_current_user_install_dir(app_version):
    """
    Return the expected install directory for an "Install for current user"
    install of the given version string (e.g. "1.12") - matches the .iss
    script's DefaultDirName for the main\\current component:
    {localappdata}\\Guidant\\AccuMate\\{#AppVersion}.
    """
    return rf"{CURRENT_USER_INSTALL_ROOT}\{app_version}"


def get_current_user_installed_exe(app_version):
    """Return the expected path to AccuMate.exe after an "Install for
    current user" install of the given version."""
    return rf"{get_current_user_install_dir(app_version)}\AccuMate.exe"


def get_current_user_uninstaller(app_version):
    """Return the expected path to the uninstaller after an "Install for
    current user" install of the given version (Inno's standard
    unins000.exe, alongside AccuMate.exe in the same install directory)."""
    return rf"{get_current_user_install_dir(app_version)}\unins000.exe"


def get_current_user_start_menu_dir(app_version):
    """Return the expected Start Menu folder for an "Install for current
    user" install - matches the .iss script's [Icons] entries using
    {userstartmenu}\\Guidant\\AccuMate\\{#AppVersion}."""
    return os.path.expandvars(
        rf"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Guidant\AccuMate\{app_version}"
    )


def run_uninstaller(uninstall_exe, timeout=60):
    """
    Launch the given uninstaller exe and drive its confirmation wizard to
    completion: "Confirm Uninstall" (Yes) -> waits for the process to exit.
    Returns once the uninstall completes. Raises if the confirmation dialog
    or its Yes button can't be found.

    SAFETY NET (see this module's "CRITICAL, LIVE-CONFIRMED GOTCHA" docstring
    section): a "current user" install's directory
    (get_current_user_install_dir()) is the SAME
    "%LOCALAPPDATA%\\Guidant\\AccuMate\\<version>\\" folder that DefaultAL4.dat/
    Default_DriverDB.dat live in for ANY copy of AccuMate.exe sharing that
    version (including the raw dev build every other regression test in this
    repo drives) - and the .iss script's [Files] entries for those two
    default-data files do NOT carry `uninsneveruninstall`, so a real
    uninstall WILL delete them, breaking every other test in the repo until
    they're restored. This function backs both files up before uninstalling
    and restores them afterward (success or failure) automatically, so
    callers never have to remember to do this themselves.
    """
    install_dir = os.path.dirname(uninstall_exe)
    _backed_up = _backup_shared_default_files(install_dir)
    try:
        return _run_uninstaller_impl(uninstall_exe, timeout=timeout)
    finally:
        _restore_shared_default_files(install_dir, _backed_up)


# The two default-data files AccuMate.exe (any copy, any version-matching
# install) requires at startup - see this module's "CRITICAL,
# LIVE-CONFIRMED GOTCHA" docstring section. Sourced from the installer's
# own source tree if missing/deleted, since those are the same files the
# installer itself bundles.
_SHARED_DEFAULT_DATA_FILES = ["DefaultAL4.dat", "Default_DriverDB.dat"]
_INSTALLER_SOURCE_DEFAULT_DATA_DIR = (
    r"C:\Users\allenma\SoftwareDevelopment\acculoadiv.AccuMate\AccuMate"
)


def _backup_shared_default_files(install_dir):
    """Copy DefaultAL4.dat/Default_DriverDB.dat out of install_dir to a
    temp backup location before an uninstall runs, so they can be restored
    afterward regardless of whether the uninstaller deletes them. Returns a
    dict of {filename: backup_path} for files that existed and were backed
    up."""
    backups = {}
    backup_dir = tempfile.mkdtemp(prefix="accumate_default_data_backup_")
    for filename in _SHARED_DEFAULT_DATA_FILES:
        src = os.path.join(install_dir, filename)
        if os.path.isfile(src):
            dst = os.path.join(backup_dir, filename)
            shutil.copy2(src, dst)
            backups[filename] = dst
    return backups


def _restore_shared_default_files(install_dir, backups):
    """
    Ensure DefaultAL4.dat/Default_DriverDB.dat exist in install_dir after an
    uninstall, restoring from (in priority order) the pre-uninstall backup
    taken by _backup_shared_default_files(), or the installer's own source
    tree as a last resort. Never raises - prints a warning if a file can't
    be restored by either means, since a missing default file breaks every
    AccuMateApp() launch in the repo, not just installer tests.
    """
    os.makedirs(install_dir, exist_ok=True)
    for filename in _SHARED_DEFAULT_DATA_FILES:
        dst = os.path.join(install_dir, filename)
        if os.path.isfile(dst):
            continue
        src = backups.get(filename)
        if src is None or not os.path.isfile(src):
            src = os.path.join(_INSTALLER_SOURCE_DEFAULT_DATA_DIR, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"[INFO] Restored shared default-data file {dst} (from {src})")
        else:
            print(
                f"[WARN] Could not restore {dst} - no backup and no source "
                f"file found at {src}. Every AccuMateApp() launch that "
                "shares this version's AppData folder will fail to start "
                "until this file is restored manually."
            )


def _run_uninstaller_impl(uninstall_exe, timeout=60):
    Application(backend="win32").start(uninstall_exe)

    win = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in Desktop(backend="win32").windows():
            try:
                title = w.window_text()
            except Exception:
                continue
            if "Uninstall" in title or "Confirm" in title:
                win = w
                break
        if win:
            break
        time.sleep(0.5)

    if win is None:
        raise RuntimeError("Uninstaller confirmation window did not appear")

    app = Application(backend="win32").connect(handle=win.handle)
    win_spec = app.window(handle=win.handle)
    win_spec.wait("exists enabled visible ready", timeout=10)

    yes_btn = win_spec.child_window(title="&Yes", class_name="Button")
    yes_btn.wait("enabled visible", timeout=10)
    yes_btn.click_input()

    # Wait for the uninstaller process itself to exit (it removes its own
    # exe/log on completion, so polling the window disappearing is the
    # simplest completion signal).
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not win_spec.exists():
            return
        time.sleep(0.5)
    raise RuntimeError("Uninstaller did not finish within timeout")
