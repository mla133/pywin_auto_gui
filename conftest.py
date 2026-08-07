import pytest
import subprocess
import os
from datetime import datetime
from app.application import AccuMateApp, APP_EXE_INSTALLED
from workflows.accuload_web import AccuLoadWebSession
from reporting.pdf_report import StepResult, TestResult, build_pdf_report

# Fallback AccuMate config used when --accumate-config-file isn't passed. This
# is the app's own DefaultAL4.dat, installed alongside the executable (also
# the file loaded when AccuMate starts up / when clicking "New" config), so
# it's a reasonable default for exercising device connectivity without
# requiring every test invocation to pass an explicit path.
DEFAULT_ACCUMATE_CONFIG_FILE = os.path.normpath(
    r"C:\Users\allenma\SoftwareDevelopment\acculoadiv.AccuMate\Release\DefaultAL4.dat"
)

# Fallback device IP used when --accumate-device-ip isn't passed. This is a
# real AccuLoad IV device on the local network, used to validate live device
# connectivity (Communications Settings -> IP Address -> Retry Comm) rather
# than just config-file loading.
DEFAULT_ACCUMATE_DEVICE_IP = "10.55.66.70"

# Default per-arm Communications Addresses (Arm 1..6) that match the real
# AccuLoad device at DEFAULT_ACCUMATE_DEVICE_IP right now. NOTE: this was
# previously [11, 22, 33, 44, 5, 6], but a later disruptive "Push All to
# AccuLoad" run reset the device's own arm addressing back to the plain
# defaults (confirmed live: DefaultAL4.dat, which bakes in 1, 2, 3, 4, 5, 6,
# now connects successfully, while the old [11, 22, 33, 44, 5, 6] values no
# longer match and cause every blank/new-config connection attempt to
# fail/time out even though the IP itself is reachable). Same root class of
# bug as the IP/Netmask/Gateway reset documented on test_a19_terminal_push_
# command and test_a10 - if a future disruptive push changes these again,
# update this list to match whatever DefaultAL4.dat's own addresses connect
# with.
DEFAULT_ACCUMATE_ARM_ADDRESSES = [1, 2, 3, 4, 5, 6]



def pytest_addoption(parser):
    parser.addoption(
        "--accumate-config-file",
        action="store",
        default=None,
        help=(
            "Path to a previously-saved AccuMate config file (e.g. DefaultAL4.dat or a "
            "specific .AL4 file) that already has real device connection settings. Used "
            "by device-connectivity tests to verify AccuMate can reach a physical "
            f"AccuLoad IV device. Defaults to {DEFAULT_ACCUMATE_CONFIG_FILE} if not passed "
            "and that file exists."
        ),
    )
    parser.addoption(
        "--accumate-device-ip",
        action="store",
        default=None,
        help=(
            "IP address of a physical AccuLoad device to configure/connect to for "
            f"device-connectivity tests. Defaults to {DEFAULT_ACCUMATE_DEVICE_IP} if not "
            "passed."
        ),
    )
    parser.addoption(
        "--accumate-arm-addresses",
        action="store",
        default=None,
        metavar="N,N,...",
        help=(
            "Comma-separated per-arm Communications Addresses matching the physical "
            "AccuLoad device at --accumate-device-ip (e.g. '1' for a single-arm device, "
            "'1,2,3' for three arms) - a real device can validly have anywhere from 1 to "
            "6 arms configured, and the Communications Settings arm addresses must match "
            f"whatever the loaded config's own arm count declares. Defaults to "
            f"{DEFAULT_ACCUMATE_ARM_ADDRESSES} if not passed."
        ),
    )
    parser.addoption(
        "--pdf-report",
        action="store",
        default=None,
        metavar="PATH",
        help=(
            "Opt-in: path to write a single PDF regression report summarizing this run "
            "(pass/fail/skip counts + a full per-test breakdown with docstring, markers, "
            "duration, failure text, and any screenshots/<test_name>/ captured during the "
            "test). Not generated unless this flag is passed. See reporting/pdf_report.py "
            "and docs/running-tests.md."
        ),
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_device: marks tests that require a live, reachable AccuLoad device "
        "connection (auto-skipped at runtime if the configured device isn't reachable).",
    )
    config.addinivalue_line(
        "markers",
        "disruptive: marks tests that mutate live device state in a way that can break "
        "subsequent test runs (e.g. A19's PUSH command, confirmed live to reset the "
        "AccuLoad's IP/netmask/gateway to defaults) - excluded by default addopts, run "
        "explicitly with `-m disruptive` as part of a deliberate full regression pass.",
    )
    config.addinivalue_line(
        "markers",
        "requires_device_web: marks tests that drive the AccuLoad device's own embedded "
        "web HMI (via the internal Selenium API bridge in workflows/accuload_web.py), "
        "as opposed to AccuMate's desktop app - needs both a reachable device and the "
        "internal tools repo checked out (see ACCULOAD_TOOLS_REPO).",
    )
    config.addinivalue_line(
        "markers",
        "requires_ftp: auto-applied (see pytest_collection_modifyitems below) to any test "
        "that requests the `app_ftp` fixture - i.e. anything that performs a real FTP file "
        "upload/download to/from the AccuLoad device. Not excluded by default addopts (FTP "
        "normally works fine), but useful to exclude explicitly with `-m \"not requires_ftp\"` "
        "for a run where FTP access is known to be unavailable (e.g. testing over a VPN that "
        "blocks the FTP data channel).",
    )
    # Collector for --pdf-report: populated by pytest_runtest_makereport
    # below, consumed by pytest_sessionfinish at the very end of the run.
    config._pdf_report_results = []
    config._pdf_report_run_started = datetime.now()


def pytest_collection_modifyitems(config, items):
    """
    Auto-applies the `requires_ftp` marker to any collected test that
    requests the `app_ftp` fixture (directly or via another fixture that
    itself depends on it), so a whole run can exclude real FTP-dependent
    tests with `-m "not requires_ftp"` without having to hand-annotate
    every such test - useful when testing over a VPN/network path known
    to block the FTP data channel (see conftest.py's app_ftp fixture
    docstring for the underlying FTP-vs-firewall finding this marker is
    protecting against).
    """
    for item in items:
        if "app_ftp" in item.fixturenames:
            item.add_marker(pytest.mark.requires_ftp)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Collects one TestResult per test for --pdf-report, using only the
    report phase that represents the test's real outcome: the "call"
    phase report for a test that actually ran, or a "setup"/"teardown"
    phase report instead if *that* phase itself failed/skipped (e.g. a
    fixture-level skip.skip()/failure never reaches the call phase at
    all) - this mirrors how pytest's own terminal summary decides a
    test's final status, avoiding double-counting the same test 2-3 times
    (setup/call/teardown all produce a report each).
    """
    outcome = yield
    report = outcome.get_result()

    config = item.config
    if not config.getoption("--pdf-report"):
        return

    is_real_outcome = report.when == "call" or (
        report.when in ("setup", "teardown") and report.outcome != "passed"
    )
    if not is_real_outcome:
        return

    if report.outcome == "passed":
        result_outcome = "passed"
    elif report.outcome == "skipped":
        result_outcome = "skipped"
    elif report.when == "call":
        result_outcome = "failed"
    else:
        # A setup/teardown failure (as opposed to a plain call failure)
        # is reported by pytest itself as an "error", not a "failure".
        result_outcome = "error"

    markers = [marker.name for marker in item.iter_markers()]
    docstring = (item.function.__doc__ or "").strip() if hasattr(item, "function") else ""
    longrepr = str(report.longrepr) if report.longrepr else ""

    test_name = item.name
    screenshot_dir = os.path.join("screenshots", test_name)
    # Populated (if at all) by the record_step fixture during the test's
    # own call phase - read now since call always runs before teardown.
    steps = list(getattr(item, "_recorded_steps", []))

    existing = next((r for r in config._pdf_report_results if r.nodeid == item.nodeid), None)
    if existing is not None:
        # A later phase (e.g. teardown error after a passing call) should
        # override an earlier recorded outcome rather than add a
        # duplicate row.
        existing.outcome = result_outcome
        existing.duration += report.duration
        if longrepr:
            existing.longrepr = longrepr
        if steps:
            existing.steps = steps
    else:
        config._pdf_report_results.append(TestResult(
            nodeid=item.nodeid,
            name=test_name,
            outcome=result_outcome,
            duration=report.duration,
            docstring=docstring,
            markers=markers,
            longrepr=longrepr,
            screenshot_dir=screenshot_dir,
            steps=steps,
        ))


def pytest_sessionfinish(session, exitstatus):
    pdf_report_path = session.config.getoption("--pdf-report")
    if not pdf_report_path:
        return

    results = session.config._pdf_report_results
    if not results:
        print("[WARN] --pdf-report was passed but no test results were collected - skipping PDF generation.")
        return

    output_path = build_pdf_report(
        results,
        pdf_report_path,
        run_started=session.config._pdf_report_run_started,
        run_finished=datetime.now(),
    )
    print(f"\n[INFO] PDF regression report written to: {output_path}")


@pytest.fixture
def config_file(request):
    explicit = request.config.getoption("--accumate-config-file")

    if explicit:
        return explicit

    if os.path.isfile(DEFAULT_ACCUMATE_CONFIG_FILE):
        return DEFAULT_ACCUMATE_CONFIG_FILE

    return None


@pytest.fixture
def device_ip(request):
    return request.config.getoption("--accumate-device-ip") or DEFAULT_ACCUMATE_DEVICE_IP


@pytest.fixture
def device_arm_addresses(request):
    """
    Per-arm Communications Addresses matching the physical AccuLoad device
    at `device_ip`, required for AccuMate to actually connect to it (see
    DEFAULT_ACCUMATE_ARM_ADDRESSES for why this can't just use a blank
    config's defaults). A real device can validly have anywhere from 1 to
    6 arms configured - pass --accumate-arm-addresses to match a specific
    device (e.g. '1' for a single-arm device).
    """
    raw = request.config.getoption("--accumate-arm-addresses")
    if raw:
        return [int(x.strip()) for x in raw.split(",") if x.strip()]

    return DEFAULT_ACCUMATE_ARM_ADDRESSES



@pytest.fixture
def accuload_web(device_ip):
    """
    Yields an AccuLoadWebSession connected to the AccuLoad device's own web
    HMI at `device_ip` (a real Chrome browser, driven via the internal
    Selenium API). Used for regression sections that require checking/editing
    values on the device's own UI (e.g. A7-A14), which AccuMate's desktop app
    can't reach. Closes the browser on teardown regardless of test outcome.
    """
    with AccuLoadWebSession(device_ip=device_ip) as web:
        yield web


def _capture_step_screenshot(app_instance, test_name, step_number):
    """
    Captures one screenshot for a record_step() call, saved alongside
    the test's other auto_step screenshots under screenshots/<test_name>/
    so all of a test's captures live in one place. Returns None (rather
    than raising) on failure, matching the same
    swallow-and-warn-don't-fail-the-test pattern used by
    MainPage._auto_screenshot/_teardown_app - a screenshot failure should
    never mask the real step verdict being recorded.
    """
    try:
        win = app_instance.get_window()

        test_dir = os.path.join("screenshots", test_name)
        os.makedirs(test_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"step{step_number:02d}_{timestamp}.png"
        path = os.path.join(test_dir, filename)

        win.capture_as_image().save(path)
        print(f"[INFO] Step {step_number} screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"[WARN] Step {step_number} screenshot failed: {e}")
        return None


@pytest.fixture
def record_step(request):
    """
    Gives a test an explicit, lightweight way to record a PASS/FAIL/SKIP
    verdict for one of its docstring's numbered steps, so the PDF report
    can show each step being evaluated instead of just one overall test
    outcome - and, for verification steps, a screenshot proving what was
    actually seen at that point.

    Usage inside a test (step numbers should match the docstring's own
    numbering, e.g. a docstring listing "11. Verify AccuLoad is updating
    the file..."):

        def test_a4_loading_old_al4_config_files(app, record_step):
            '''
            ...
              11. Verify AccuLoad is updating the file (progress dialog).
            '''
            ...
            notice_shown = wait_for_migration_notice(app)
            record_step(11, "passed" if notice_shown else "failed",
                        app=app, note="Migration notice text", screenshot=True)

    Pass `app=<the test's app fixture value>` and `screenshot=True` to
    capture a screenshot of the main app window at record_step()'s own
    call time (saved under screenshots/<test_name>/). IMPORTANT: if the
    thing actually being verified is a transient dialog/popup (e.g. a
    migration/progress dialog) that's already been dismissed by the time
    record_step() is called, that screenshot only shows the main window
    *after* the dialog closed, not the dialog itself - a real gap found
    live on test_a4. For that case, capture the screenshot *while the
    dialog is on screen* inside the workflow function itself (see e.g.
    workflows/file_workflows.py's load_and_migrate_old_config_file()
    `screenshot_dir` param) and pass the resulting path directly via
    `screenshot_path=<path>` instead of `screenshot=True`.

    Steps recorded this way are picked up by pytest_runtest_makereport
    below and attached to the TestResult passed to build_pdf_report();
    docstring steps with no matching recorded step number render exactly
    as before (plain, unannotated) - this is purely additive/opt-in.
    """
    steps = []
    request.node._recorded_steps = steps

    def _record(step_number, outcome="passed", note="", app=None, screenshot=False, screenshot_path=None):
        if screenshot_path is None and screenshot and app is not None:
            screenshot_path = _capture_step_screenshot(app, request.node.name, step_number)
        steps.append(StepResult(
            step_number=step_number,
            outcome=outcome,
            note=note,
            screenshot_path=screenshot_path,
        ))

    return _record


def _teardown_app(app_instance, test_name):
    """
    Shared teardown for the `app`/`app_ftp` fixtures: screenshot then
    force-kill, swallowing exceptions so a teardown failure never masks
    the real test failure/result.
    """
    print("\n[DEBUG] Taking screenshot before teardown...")

    try:
        win = app_instance.get_window()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_name}_{timestamp}.png"
        path = f"screenshots/{filename}"

        os.makedirs("screenshots", exist_ok=True)

        win.capture_as_image().save(path)

        print(f"[DEBUG] Screenshot saved: {path}")

    except Exception as e:
        print(f"[WARN] Screenshot failed: {e}")

    print("[DEBUG] Closing application...")

    try:
        pid = app_instance.get_window().process_id()

        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        print(f"[WARN] Failed to kill process: {e}")


@pytest.fixture(scope="function")
def app(request):
    app_instance = AccuMateApp()
    app_instance.test_name = request.node.name

    yield app_instance

    _teardown_app(app_instance, request.node.name)


@pytest.fixture(scope="function")
def app_ftp(request):
    """
    Like `app`, but launches AccuMate from its *installed* location
    (app.application.APP_EXE_INSTALLED) instead of the raw build output
    folder (APP_EXE) - required for any test that performs a real device
    file transfer (upload/download). Live-confirmed (2026-08-05): a
    corporate firewall/network policy blocks the actual FTP data channel
    when launched from APP_EXE, causing every transfer to hit a device-side
    "The operation timed out" ~60-90s after Start even though the control
    connection is genuinely live; the identical binary launched from
    APP_EXE_INSTALLED instead completes real transfers successfully (after
    allowing the Windows Firewall prompt for that path once). Use this
    fixture for D6-D8/E4-E6/B4-B10/B13-B14/F1-F8 style tests; keep using
    plain `app` for everything else (it's unaffected and there's no reason
    to add the installed build's dependency where it isn't needed).
    """
    app_instance = AccuMateApp(exe_path=APP_EXE_INSTALLED)
    app_instance.test_name = request.node.name

    yield app_instance

    _teardown_app(app_instance, request.node.name)
