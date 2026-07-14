import pytest
import subprocess
import os
from datetime import datetime
from app.application import AccuMateApp

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
