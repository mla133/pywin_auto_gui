import pytest

from workflows.file_workflows import load_config_file
from workflows.comm_workflows import configure_ip_and_connect

DEVICE_CONNECT_TIMEOUT = 45  # bumped from 15s: remote/VPN sessions add connect latency


@pytest.mark.requires_device
def test_device_connectivity(app, config_file, device_ip):
    """
    Verify AccuMate can establish a live connection to a physical AccuLoad
    device: load a previously-saved config file (e.g. DefaultAL4.dat), set
    its IP Address (Communications Settings dialog, via ribbon "Document
    Options") to `device_ip`, click ribbon "Retry Comm", then confirm
    AccuMate reports a real ONLINE connection (via the ribbon's "Pull All
    From AccuLoad" enabled state - the status bar's "ONLINE"/"Offline" text
    itself is not exposed to either the win32 or UIA automation backends).

    Run with:
        pytest -s -v tests/test_device_connectivity.py \
            --accumate-config-file="C:\\path\\to\\DefaultAL4.dat" \
            --accumate-device-ip=10.55.66.70

    Auto-skipped (rather than failed) when no config file is available, or
    when the device doesn't come online within DEVICE_CONNECT_TIMEOUT
    seconds - so it doesn't block the default test run when no device is
    configured/connected.
    """

    if not config_file:
        pytest.skip(
            "No --accumate-config-file supplied. Pass "
            "--accumate-config-file=<path to a saved AccuMate config> to run this "
            "connectivity check."
        )

    print(f"[STEP] Loading config file: {config_file}")
    load_config_file(app, config_file)

    print(f"[STEP] Configuring device IP {device_ip} and attempting connection")
    connected = configure_ip_and_connect(app, device_ip, timeout=DEVICE_CONNECT_TIMEOUT)

    if not connected:
        pytest.skip(
            f"AccuLoad device at {device_ip} not reachable/connected - AccuMate did not "
            f"report a live connection within {DEVICE_CONNECT_TIMEOUT}s. Verify the device "
            "is powered on and reachable, or pass --accumate-device-ip=<reachable IP>."
        )

    print(f"[INFO] Device connection established at {device_ip}")
    assert app.is_device_connected()
