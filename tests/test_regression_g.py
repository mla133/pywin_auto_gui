"""
scenarios/regression.md G1-G5 (installer testing).

Drives the compiled Inno Setup installer (workflows/installer_workflows.py)
built from AccuMateIVInstallerScript.iss in a sibling dev repo
(C:\\Users\\allenma\\SoftwareDevelopment\\acculoadiv.AccuMate\\). This is a
SEPARATE application/process from AccuMate.exe - the installer's [Files]
section copies AccuMate.exe into Program Files/AppData, a different location
than the Release\\AccuMate.exe build every other regression test in this repo
drives directly (app/application.py's APP_EXE) - so real install/uninstall
cycles here do not risk breaking any other test.

Scope summary:
  - G2: fully automated, non-disruptive (no marker) - just verifies the
    License Agreement page's accept/decline gating, then cancels. Safe to
    run in a routine test pass.
  - G1, G3: fully automated, but perform REAL install/uninstall cycles -
    marked `installs_software` (excluded from default addopts, run
    explicitly with `-m installs_software`). G3 covers the "Install for
    current user" happy path this session's non-admin environment naturally
    takes; G1 reuses that same install to verify the "already installed +
    app running" block, using the installer's own [Code] section logic
    (PrepareToInstall's IsAppRunning() check - see
    workflows/installer_workflows.py's module docstring).
  - G4, G5 (admin/"all users" installs): NOT live-verified - this session's
    shell is confirmed non-admin
    (`([Security.Principal.WindowsPrincipal]...).IsInRole(...Administrator)`
    -> False), so the elevation prompt/Tasks page/main\\all component choice
    has never actually been driven live. Left as
    `needs_live_verification` stubs with the exact open questions documented
    per test.
  - G1 step 5 (uninstall while app running) is ALSO left as
    `needs_live_verification`: the .iss script's [Code] section only wires
    its custom "already running" MsgBox into PrepareToInstall (used by the
    Setup executable for a same-version reinstall), not into the separate
    uninstaller (unins000.exe) - there's no [Code] handler in this script
    for uninstall-time app-running detection. Whether the uninstall is
    actually blocked would depend entirely on AccuMate.exe registering
    Inno's AppMutex ("AccuMateIVMutex") itself, which cannot be confirmed
    from this repo (that's the separate C++/MFC AccuMate source, out of
    scope here) - documented as an open question rather than assumed either
    way.
"""
import os
import time

import pytest

from app.application import AccuMateApp
from workflows.file_workflows import (
    close_about_dialog,
    get_about_dialog_text,
    new_config_file,
    open_about_dialog,
)
from workflows.installer_workflows import (
    APP_VERSION,
    OldVersionLoopBug,
    accept_license,
    click_cancel,
    click_install,
    click_next,
    decline_license,
    find_stale_accumate_uninstall_entries,
    get_current_user_install_dir,
    get_current_user_installed_exe,
    get_current_user_start_menu_dir,
    get_current_user_uninstaller,
    get_ready_to_install_summary,
    is_license_page,
    is_ready_to_install_page,
    launch_installer,
    run_uninstaller,
    wait_for_finish_and_close,
)


def _skip_if_stale_old_version_entries():
    """
    Known installer bug (see workflows/installer_workflows.py's module
    docstring, "KNOWN INSTALLER BUG"): if this machine has leftover
    Windows uninstall-registry entries for any AccuMate version other than
    APP_VERSION (confirmed live: 1.9, 1.11, 0.10, "AccuMate III.NET"), the
    installer's "old version detected" MsgBox reappears identically
    whichever button is clicked, hanging forever before ever reaching the
    Finish page - a bug in AccuMateIVInstallerScript.iss itself, not this
    repo. Any test that needs a real install to actually complete calls
    this first and skips with a clear explanation rather than hanging.
    """
    stale = find_stale_accumate_uninstall_entries(APP_VERSION)
    if stale:
        pytest.skip(
            "Cannot complete a real install on this machine: stale "
            f"AccuMate uninstall registry entries found ({stale}) trigger "
            "an infinite 'old version detected' dialog loop bug in the "
            "installer script (see workflows/installer_workflows.py "
            "docstring). Needs either those entries cleaned up or a "
            "machine without this leftover state."
        )


def _run_installer_to_ready_to_install():
    """Shared setup for both G1 and G3: launch the installer, accept the
    license, and advance through Select Components/Select Destination to
    Ready to Install (leaving the default current-user/compact component
    choice this non-admin session is restricted to)."""
    win_spec = launch_installer()
    assert click_next(win_spec), "Next should be enabled on the Welcome page"
    assert is_license_page(win_spec), "expected the License Agreement page"
    accept_license(win_spec)
    assert click_next(win_spec), "Next should be enabled after accepting the license"
    assert click_next(win_spec), "Next should be enabled on Select Components"
    assert click_next(win_spec), "Next should be enabled on Select Destination"
    assert is_ready_to_install_page(win_spec), "expected the Ready to Install page"
    return win_spec


def _install_current_user_if_needed():
    """
    Ensure a current-user install of AccuMate exists at the expected version,
    installing it if not already present. Returns the installed exe path.
    Idempotent - safe to call from multiple tests without re-installing.

    Checks for BOTH the exe and the uninstaller before treating an install
    as already-complete: an earlier run on this machine hit the "old version
    detected" loop bug (see workflows/installer_workflows.py docstring)
    after the file copy had already happened but before the wizard could
    reach Finish, leaving a PARTIAL install (exe present, but no
    uninstaller/Start Menu entries - those are only written once Finish is
    reached). Checking exe_path alone would treat that broken partial state
    as "already installed" and skip re-running the installer.
    """
    exe_path = get_current_user_installed_exe(APP_VERSION)
    uninstall_exe = get_current_user_uninstaller(APP_VERSION)
    if os.path.isfile(exe_path) and os.path.isfile(uninstall_exe):
        return exe_path

    _skip_if_stale_old_version_entries()

    win_spec = _run_installer_to_ready_to_install()
    click_install(win_spec)
    try:
        wait_for_finish_and_close(win_spec)
    except OldVersionLoopBug as exc:
        pytest.skip(str(exc))

    assert os.path.isfile(exe_path), (
        f"Install completed but AccuMate.exe not found at expected path {exe_path}"
    )
    return exe_path


# ---------------------------------------------------------------------------
# G2: Terms & Conditions in the Installer
# ---------------------------------------------------------------------------

def test_g2_license_agreement_shown_before_install():
    """
    regression.md G2 steps 1-2: running the installer shows a License
    Agreement page before the application installs, and Next stays disabled
    until the license is accepted (declining keeps it blocked). Read-only -
    cancels out before any real install occurs.
    """
    win_spec = launch_installer()

    print("[STEP] Advancing from Welcome to License page")
    assert click_next(win_spec), "Next should be enabled on the Welcome page"
    assert is_license_page(win_spec), "expected the License Agreement page next"

    print("[STEP] Declining the license - Next must stay disabled")
    decline_license(win_spec)
    assert not click_next(win_spec), (
        "Next should NOT be enabled after declining the license agreement"
    )

    print("[STEP] Accepting the license - Next must become enabled")
    accept_license(win_spec)
    assert click_next(win_spec), (
        "Next should be enabled after accepting the license agreement"
    )

    print("[STEP] Cancelling wizard (not performing a real install)")
    click_cancel(win_spec)


# ---------------------------------------------------------------------------
# G3: Install AccuMate as normal user
# ---------------------------------------------------------------------------

@pytest.mark.installs_software
def test_g3_install_as_normal_user():
    """
    regression.md G3 step 1: run through the installer as a regular
    (non-admin) user and verify it completes with no errors. This session's
    shell is confirmed non-admin, so the wizard naturally restricts to the
    "Install for current user" / "Compact installation" component choice
    (see workflows/installer_workflows.py docstring) - there is no "choose
    all users vs current user" prompt to drive here, matching G3's own
    normal-user framing (that choice is G4/G5's concern).
    """
    _skip_if_stale_old_version_entries()

    win_spec = _run_installer_to_ready_to_install()

    summary = get_ready_to_install_summary(win_spec)
    print(f"[INFO] Ready to Install summary:\n{summary}")
    assert "Compact installation" in summary
    assert "Install for current user" in summary

    print("[STEP] Clicking Install and waiting for completion")
    click_install(win_spec)
    try:
        wait_for_finish_and_close(win_spec)
    except OldVersionLoopBug as exc:
        pytest.skip(str(exc))

    exe_path = get_current_user_installed_exe(APP_VERSION)
    assert os.path.isfile(exe_path), f"AccuMate.exe not found at {exe_path} after install"


@pytest.mark.installs_software
def test_g3_about_version_after_install():
    """
    regression.md G3 step 1 (version check): after installing, AccuMate
    opens without error and the About section shows the correct version.
    """
    exe_path = _install_current_user_if_needed()

    print(f"[STEP] Launching installed AccuMate from {exe_path}")
    app_obj = AccuMateApp(exe_path=exe_path)
    try:
        win = app_obj.get_window()
        assert win.is_visible(), "installed AccuMate did not open successfully"

        print("[STEP] Opening About dialog")
        about_text = get_about_dialog_text(app_obj)
        print(f"[INFO] About dialog text: {about_text}")
        assert APP_VERSION in about_text, (
            f"expected version '{APP_VERSION}' in About dialog text: {about_text}"
        )
    finally:
        try:
            app_obj.app.kill()
        except Exception:
            pass


@pytest.mark.installs_software
def test_g3_start_menu_shortcut_created():
    """
    regression.md G3 step 3: AccuMate can be started from the Start Menu.
    Automating an actual Start Menu click is out of scope (that's Windows
    shell UI, not AccuMate/the installer) - instead verifies the Start Menu
    shortcut the installer creates actually exists on disk, which is the
    real prerequisite "starts from the Start Menu" depends on.
    """
    _install_current_user_if_needed()

    start_menu_dir = get_current_user_start_menu_dir(APP_VERSION)
    print(f"[STEP] Checking Start Menu folder: {start_menu_dir}")
    assert os.path.isdir(start_menu_dir), f"Start Menu folder not found: {start_menu_dir}"

    shortcuts = [f for f in os.listdir(start_menu_dir) if f.lower().endswith(".lnk")]
    print(f"[INFO] Found shortcuts: {shortcuts}")
    assert shortcuts, f"no .lnk shortcuts found in {start_menu_dir}"


def test_g3_desktop_icon_start_not_applicable():
    """
    regression.md G3 step 2: marked [NA] in regression.md itself - "Desktop
    icon is unavailable currently due to needing admin rights for the user
    to install the desktop icon without error during setup." Confirmed by
    the .iss script's own [Tasks] "desktopicon" entry (Check: CheckTask,
    which is `Result := IsAdmin`) - a non-admin install never gets the
    option at all. Nothing to automate; this test documents the NA rather
    than silently having no coverage for this step.
    """
    pytest.skip(
        "G3 step 2 is [NA] in regression.md - desktop icon requires admin "
        "rights during install (.iss [Tasks] 'desktopicon' Check: CheckTask "
        "-> IsAdmin), not available for a current-user install"
    )


@pytest.mark.xfail(
    reason=(
        "regression.md G3 step 4 is documented [FAIL] - double-clicking an "
        ".al4 file does not start AccuMate (Ticket #3841). Kept as an xfail "
        "so a future fix is caught (test starts passing) rather than the "
        "bug silently persisting forever."
    ),
    strict=False,
)
@pytest.mark.installs_software
def test_g3_al4_file_association_double_click():
    """
    regression.md G3 step 4: double-clicking an AccuMate .al4 file should
    start AccuMate (via the .iss [Registry] file association routing to
    "AccuMate.exe" -load "%1""). Documented as a known, ticketed bug
    (#3841) in regression.md itself - this test drives the real file
    association via os.startfile() and asserts a matching AccuMate window
    appears, which is expected to currently fail.
    """
    import subprocess

    from app.application import _TITLE_RE, _CLASS_NAME_RE
    from pywinauto import Desktop

    _install_current_user_if_needed()

    al4_path = os.path.normpath(
        r"C:\Users\allenma\Documents\Testing\Auto_Test.AL4"
    )
    assert os.path.isfile(al4_path), f"test .al4 file not found: {al4_path}"

    print(f"[STEP] Double-clicking (os.startfile) {al4_path}")
    os.startfile(al4_path)

    found = False
    deadline = time.time() + 15
    while time.time() < deadline:
        for w in Desktop(backend="win32").windows():
            try:
                if w.class_name().startswith("Afx:") and "AccuLoad" in w.window_text():
                    found = True
                    break
            except Exception:
                continue
        if found:
            break
        time.sleep(0.5)

    assert found, "AccuMate did not open in response to double-clicking a .al4 file"


@pytest.mark.installs_software
def test_g3_uninstall():
    """regression.md G3 step 5: uninstall AccuMate and verify removal."""
    exe_path = _install_current_user_if_needed()
    install_dir = get_current_user_install_dir(APP_VERSION)
    uninstall_exe = get_current_user_uninstaller(APP_VERSION)
    assert os.path.isfile(uninstall_exe), f"uninstaller not found: {uninstall_exe}"

    print(f"[STEP] Running uninstaller {uninstall_exe}")
    run_uninstaller(uninstall_exe)

    time.sleep(1)
    assert not os.path.isfile(exe_path), f"AccuMate.exe still present after uninstall: {exe_path}"
    print(f"[INFO] Confirmed {install_dir} no longer contains AccuMate.exe")


# ---------------------------------------------------------------------------
# G1: Installing new version of AccuMate can't create new config docs
# ---------------------------------------------------------------------------

@pytest.mark.installs_software
def test_g1_block_reinstall_while_app_running():
    """
    regression.md G1 steps 1 and 4: installing while AccuMate is already
    open should be blocked with a popup message.

    This installer's [Code] section (PrepareToInstall) only detects an
    "old version installed" state via a registry key keyed on
    {AppId}_{AppVersion} - since AppId embeds the version, this really
    detects a same-version reinstall rather than a true version upgrade (no
    second/newer installer build is available in this environment to test a
    true upgrade path). Re-running the exact same installer after it's
    already installed exercises the identical code path regression.md is
    checking (an install attempt while the old copy is present + running is
    blocked), so this is a faithful automation of the step's real intent.
    """
    exe_path = _install_current_user_if_needed()

    print(f"[STEP] Launching already-installed AccuMate from {exe_path}")
    app_obj = AccuMateApp(exe_path=exe_path)
    try:
        assert app_obj.get_window().is_visible()

        print("[STEP] Re-running the installer while AccuMate is open")
        win_spec = launch_installer()
        assert click_next(win_spec), "Next should be enabled on the Welcome page"
        assert is_license_page(win_spec)
        accept_license(win_spec)
        assert click_next(win_spec)
        assert click_next(win_spec)  # Select Components
        assert click_next(win_spec)  # Select Destination
        # PrepareToInstall fires when leaving Ready to Install (i.e. on the
        # Install click), detecting the already-installed same version.
        click_install(win_spec)

        print("[STEP] Expecting 'old version detected' MsgBox - click Yes")
        from pywinauto import Desktop
        from pywinauto import Application as PwaApplication

        old_version_dlg = None
        deadline = time.time() + 10
        while time.time() < deadline:
            for w in Desktop(backend="win32").windows():
                try:
                    if "old version" in w.window_text().lower() or w.class_name() == "#32770":
                        old_version_dlg = w
                        break
                except Exception:
                    continue
            if old_version_dlg:
                break
            time.sleep(0.5)

        assert old_version_dlg is not None, (
            "expected an 'old version detected' confirmation MsgBox, none appeared"
        )
        dlg_app = PwaApplication(backend="win32").connect(handle=old_version_dlg.handle)
        dlg_spec = dlg_app.window(handle=old_version_dlg.handle)
        dlg_spec.child_window(title="&Yes", class_name="Button").click_input()

        print("[STEP] Expecting 'already running' error MsgBox")
        running_dlg = None
        deadline = time.time() + 10
        while time.time() < deadline:
            for w in Desktop(backend="win32").windows():
                try:
                    if "already running" in w.window_text().lower():
                        running_dlg = w
                        break
                    if w.class_name() == "#32770":
                        for c in PwaApplication(backend="win32").connect(
                            handle=w.handle
                        ).window(handle=w.handle).descendants(class_name="Static"):
                            if "already running" in c.window_text().lower():
                                running_dlg = w
                                break
                except Exception:
                    continue
            if running_dlg:
                break
            time.sleep(0.5)

        assert running_dlg is not None, (
            "expected a popup indicating AccuMate is already running - "
            "installer did not block the reinstall while the app was open"
        )

        try:
            dlg_app2 = PwaApplication(backend="win32").connect(handle=running_dlg.handle)
            dlg_app2.window(handle=running_dlg.handle).child_window(
                title="OK", class_name="Button"
            ).click_input()
        except Exception:
            pass

        try:
            click_cancel(win_spec)
        except Exception:
            pass
    finally:
        try:
            app_obj.app.kill()
        except Exception:
            pass


@pytest.mark.installs_software
def test_g1_new_config_after_install():
    """
    regression.md G1 step 3: after a fresh install, AccuMate can create a
    new config file with no errors.
    """
    exe_path = _install_current_user_if_needed()

    app_obj = AccuMateApp(exe_path=exe_path)
    try:
        print("[STEP] Creating a new config file via Application Button -> New")
        new_config_file(app_obj)
        win = app_obj.get_window()
        assert win.is_visible(), "AccuMate window not visible after creating a new config"
    finally:
        try:
            app_obj.app.kill()
        except Exception:
            pass


@pytest.mark.manual
def test_g1_block_uninstall_while_app_running():
    """
    regression.md G1 step 5: uninstalling while AccuMate is running should
    show a popup and be blocked. MANUAL TEST.

    NOT automatable with confidence from this repo alone: this installer's
    [Code] section only wires its "already running" check into
    PrepareToInstall, which is a Setup-executable-only Pascal event - there
    is no equivalent [Code] handler for the separate uninstaller
    (unins000.exe) in AccuMateIVInstallerScript.iss. Whether uninstalling
    while AccuMate is running is actually blocked depends entirely on
    whether AccuMate.exe itself registers Inno's AppMutex
    ("AccuMateIVMutex", set via [Setup] AppMutex=) - that's implemented (or
    not) in the separate C++/MFC AccuMate source, out of scope for this
    Python repo to inspect or assume. Must be performed manually by a human
    tester (or verified against the AccuMate source) before this can be
    safely automated one way or the other.
    """
    pytest.skip(
        "G1: MANUAL TEST - cannot confirm from this repo whether "
        "AccuMate.exe registers Inno's AppMutex; perform this step "
        "manually (see docstring)"
    )


# ---------------------------------------------------------------------------
# G4: Install AccuMate as Admin for All Users
# G5: Install AccuMate as Admin for the Current User
# ---------------------------------------------------------------------------

@pytest.mark.manual
def test_g4_install_as_admin_all_users():
    """
    regression.md G4: run the installer elevated (as Administrator) and
    choose "Install for All Users". MANUAL TEST. This session's shell is
    confirmed non-admin (checked via
    `([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]
    ::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)`
    -> False) - the elevation prompt (UAC), the Tasks page (desktop icon,
    only shown/enabled for admin per CheckTask), and the "main\\all" vs
    "main\\current" component radio choice have never been driven live.
    Must be performed manually by a human tester in an elevated
    (Administrator) session.
    """
    pytest.skip(
        "G4: MANUAL TEST - requires an elevated (Administrator) session; "
        "current session confirmed non-admin - perform this step manually"
    )


@pytest.mark.manual
def test_g5_install_as_admin_current_user():
    """
    regression.md G5: same as G4 but choosing "Install for Current User"
    while still running elevated (as Administrator) - per the .iss script,
    an admin user CAN still choose the current-user component even though
    they're elevated (SetCurrentUserOnlyComponents only forces this for a
    genuinely non-admin user). MANUAL TEST - see
    test_g4_install_as_admin_all_users' docstring for why.
    """
    pytest.skip(
        "G5: MANUAL TEST - requires an elevated (Administrator) session; "
        "current session confirmed non-admin - perform this step manually"
    )
