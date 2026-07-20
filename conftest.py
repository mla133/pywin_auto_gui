import pytest
import subprocess
import os
from datetime import datetime
from app.application import AccuMateApp
from workflows.accuload_web import AccuLoadWebSession

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
    config's defaults).
    """
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


@pytest.fixture(scope="function")
def app(request):
    app_instance = AccuMateApp()
    app_instance.test_name = request.node.name

    yield app_instance

    print("\n[DEBUG] Taking screenshot before teardown...")

    try:
        win = app_instance.get_window()

        # Generate a timestamped filename
        test_name = request.node.name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_name}_{timestamp}.png"
        path = f"screenshots/{filename}"

        # Ensure folder exists
        os.makedirs("screenshots", exist_ok=True)

        # Capture screenshot
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
