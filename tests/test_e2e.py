import pytest

from app.application import AccuMateApp
from workflows.file_workflows import load_test_file, load_config_file
from workflows.comm_workflows import configure_ip_and_connect
from workflows.security_workflows import enter_passcode
from pages.main_page import MainPage

DEVICE_CONNECT_TIMEOUT = 45  # bumped from 10s: remote/VPN sessions add connect latency


@pytest.mark.requires_device
def test_full_user_workflow(app, request, device_ip):
    # NOTE: intentionally reads the raw --accumate-config-file CLI option here
    # (not the `config_file` fixture), since that fixture falls back to
    # AccuMate's own DefaultAL4.dat by default (useful for the dedicated
    # device-connectivity test). This workflow's downstream steps (tree path,
    # dropdown value, passcode dialog) are tuned against Auto_Test.AL4's
    # specific data, so it should only switch files when the user explicitly
    # asks for a different one.
    explicit_config_file = request.config.getoption("--accumate-config-file")

    if explicit_config_file:
        print(f"[STEP] Loading provided config file: {explicit_config_file}")
        load_config_file(app, explicit_config_file)

        print(f"[STEP] Configuring device IP {device_ip} and attempting connection")
        connected = configure_ip_and_connect(app, device_ip, timeout=DEVICE_CONNECT_TIMEOUT)
    else:
        print("[STEP] Loading test file")
        load_test_file(app)

        print("[STEP] Checking AccuLoad IV device connectivity")
        connected = app.wait_for_device_connection(timeout=DEVICE_CONNECT_TIMEOUT)

    if not connected:
        pytest.skip(
            "AccuLoad device not reachable/connected - AccuMate did not report a live "
            f"connection within {DEVICE_CONNECT_TIMEOUT}s. Connect a physical AccuLoad "
            "device (or pass --accumate-config-file/--accumate-device-ip) to run this "
            "end-to-end workflow."
        )

    page = MainPage(app, request=request)

    print("[STEP] Navigating to Security Directory")
    page.select_tree_path(["System Directory", "Security Directory"])

    print("[STEP] Selecting Ethernet Host Security Level")
    row_index = page.select_list_item("Ethernet Host Security Level")

    print("[STEP] Editing dropdown value")
    page.edit_dropdown_value("Ethernet Host Security Level", "Security Level 2")

    print("[STEP] Handling passcode dialog (bad passcode)")
    success = enter_passcode(app, "1234")
    assert success is False

    print("[STEP] Verifying dropdown value is NOT updated")
    selected_value = page.get_value("Ethernet Host Security Level")
    assert selected_value != "Security Level 2"
