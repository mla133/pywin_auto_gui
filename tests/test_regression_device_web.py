import pytest

from workflows.file_workflows import new_config_file, load_config_file
from workflows.comm_workflows import (
    configure_ip_and_connect,
    open_communications_settings,
    close_communications_settings,
    set_arm_address,
    get_arm_address,
    wait_for_warning_dialog,
    dismiss_dialog,
)
from workflows.totalizers import retrieve_totalizers

DEVICE_CONNECT_TIMEOUT = 15


def _connect_new_config(app, device_ip, device_arm_addresses):
    """Shared setup: open a new blank config file and connect to the device (skip if unreachable)."""
    print("[STEP] Opening a new AccuMate Config File")
    new_config_file(app)

    print(f"[STEP] Configuring device IP {device_ip} / arm addresses {device_arm_addresses}")
    connected = configure_ip_and_connect(
        app, device_ip, timeout=DEVICE_CONNECT_TIMEOUT, arm_addresses=device_arm_addresses
    )

    if not connected:
        pytest.skip(
            f"AccuLoad device at {device_ip} not reachable/connected within "
            f"{DEVICE_CONNECT_TIMEOUT}s - verify the device is powered on and reachable."
        )


@pytest.mark.requires_device
def test_a7_manually_connecting_to_accuload(app, device_ip, device_arm_addresses):
    """
    A7: Manually Connecting to an AccuLoad - open a new blank config, use
    'Document Options' to enter the device's IP address and OK the dialog,
    and confirm AccuMate reports a live connection.
    """
    print("[STEP] Opening a new AccuMate Config File")
    new_config_file(app)

    print(f"[STEP] Configuring device IP {device_ip} / arm addresses {device_arm_addresses} via Document Options")
    connected = configure_ip_and_connect(
        app, device_ip, timeout=DEVICE_CONNECT_TIMEOUT, arm_addresses=device_arm_addresses
    )

    if not connected:
        pytest.skip(
            f"AccuLoad device at {device_ip} not reachable/connected within "
            f"{DEVICE_CONNECT_TIMEOUT}s - verify the device is powered on and reachable."
        )

    assert app.is_device_connected(), "Expected AccuMate to report a live connection after Document Options OK"


@pytest.mark.requires_device
def test_a8_automatically_connecting_to_accuload(app, config_file, device_ip):
    """
    A8: Automatically Connecting to an AccuLoad - opening a previously-saved
    .AL4 config file (which already has device connection settings baked
    in) should have AccuMate auto-connect without any further user action.
    """
    if not config_file:
        pytest.skip("No --accumate-config-file provided/available for A8's auto-connect scenario")

    print(f"[STEP] Loading saved config file: {config_file}")
    load_config_file(app, config_file)

    connected = app.wait_for_device_connection(timeout=DEVICE_CONNECT_TIMEOUT)
    if not connected:
        pytest.skip(
            f"AccuLoad device at {device_ip} not reachable/connected within "
            f"{DEVICE_CONNECT_TIMEOUT}s after loading {config_file} - verify the device is "
            "powered on/reachable and that this config's baked-in connection settings still match it."
        )

    assert app.is_device_connected(), "Expected AccuMate to auto-connect after loading a saved config file"


@pytest.mark.requires_device
def test_a9_valid_arm_addresses(app, device_ip, device_arm_addresses):
    """
    A9: Valid Arm Addresses - connect successfully, then verify AccuMate
    guards against invalid per-arm Communications Addresses:
      - Arm Address 1 set to 0 -> a warning dialog ("cannot be 0").
      - Arm Address 2 set to 0 (with Arm 1 restored to a valid value) -> a
        warning that Arm 2 is "configured for use" and should be changed.

    NOT YET LIVE-VERIFIED: the exact wording of either warning dialog is
    unconfirmed (regression.md paraphrases them, not exact strings), so
    this only asserts that *a* new dialog appears and prints its text for
    manual confirmation, rather than matching specific wording that could
    be wrong and mask a real regression.
    """
    _connect_new_config(app, device_ip, device_arm_addresses)

    print("[STEP] Setting Arm Address 1 to 0 (expect a warning dialog)")
    dlg = open_communications_settings(app)
    set_arm_address_raw(dlg, 1, 0)
    close_communications_settings(dlg, accept=True)

    warning = wait_for_warning_dialog(app, timeout=5)
    assert warning is not None, "Expected a warning dialog after setting Arm Address 1 to 0, none appeared"
    print(f"[INFO] Arm Address 1 = 0 warning dialog text: {warning.window_text()!r}")
    dismiss_dialog(warning)

    # NOTE (confirmed live): the warning is just a notice - AccuMate does NOT
    # revert the field itself (it keeps reading back "0" until explicitly
    # changed again), so Arm 1 must be explicitly restored before continuing.
    # A short pause here avoids a real observed race where reopening the
    # dialog immediately after dismissing the warning intermittently misses.
    import time as _time
    _time.sleep(1.5)

    print("[STEP] Restoring Arm Address 1, setting Arm Address 2 to 0 (expect a second warning)")
    dlg = open_communications_settings(app, retries=3)
    set_arm_address(dlg, 1, device_arm_addresses[0])
    set_arm_address_raw(dlg, 2, 0)
    close_communications_settings(dlg, accept=True)

    warning = wait_for_warning_dialog(app, timeout=5)
    assert warning is not None, "Expected a warning dialog/message after setting Arm Address 2 to 0, none appeared"
    print(f"[INFO] Arm Address 2 = 0 warning text: {warning.window_text()!r}")
    dismiss_dialog(warning)

    print("[STEP] Restoring known-good arm addresses so later tests aren't affected")
    dlg = open_communications_settings(app)
    for arm_number, address in enumerate(device_arm_addresses, start=1):
        set_arm_address(dlg, arm_number, address)
    close_communications_settings(dlg, accept=True)


def set_arm_address_raw(dlg, arm_number, address):
    """
    Like comm_workflows.set_arm_address, but without its post-set readback
    assertion - needed here because setting an arm address to the
    deliberately-invalid value 0 is expected to be rejected/altered by
    AccuMate itself (that's the behavior under test), so asserting the
    field still reads back "0" afterward would be the wrong check.
    """
    from workflows.comm_workflows import _ARM_ADDRESS_CONTROL_IDS, _find_by_control_id

    control_id = _ARM_ADDRESS_CONTROL_IDS[arm_number]
    ctrl = _find_by_control_id(dlg, control_id)
    ctrl.click_input()
    ctrl.type_keys("^a")
    ctrl.type_keys(str(address))


@pytest.mark.requires_device
@pytest.mark.disruptive
def test_a10_pushing_full_configuration(app, config_file, device_ip, device_arm_addresses):
    """
    A10: Pushing Full Configurations.

    Automates the AccuMate-side steps: open an existing config file, edit a
    "Pulse In 01" value while offline, set the Communications parameters to
    match the device, connect, then Push All to AccuLoad and confirm it
    completes with AccuMate still connected afterward.

    KNOWN DISRUPTIVE SIDE EFFECT (confirmed live, same root cause as
    test_a19_terminal_push_command in test_regression_device.py): "Push All
    to AccuLoad" overwrites the device's IP/netmask/gateway to whatever the
    pushed config's own comm-settings section contains, which can break the
    connection for any subsequent test run against the same device/IP until
    it's manually reconfigured. Marked `disruptive` and excluded from the
    default test run - run deliberately with `-m disruptive`.

    NOT YET AUTOMATED: steps 7-10 (switching to the AccuLoad's own web UI
    to verify the pushed "Pulse In 1" value and IP/Netmask/Gateway landed
    correctly) require live element-ID discovery on the device's web pages
    (see workflows/accuload_web.py) - skipped here with a clear reason
    rather than asserted against guessed element IDs.
    """
    from workflows.terminal_emulator import wait_for_progress_dialog_to_close
    from controls.ribbon_controls import click_ribbon_button
    from pages.main_page import MainPage

    if not config_file:
        pytest.skip("No --accumate-config-file provided/available for A10")

    print(f"[STEP] Loading config file: {config_file}")
    load_config_file(app, config_file)

    page = MainPage(app, request=None)
    page.test_name = "test_a10_pushing_full_configuration"

    print("[STEP] Editing a Pulse In 01 value while offline")
    page.select_tree_path(["Config Directory", "Pulse Inputs", "Pulse In 01"])
    page.edit_program_code_data("Pulse Input Tag", "A10TEST")

    print(f"[STEP] Configuring device IP {device_ip} / arm addresses {device_arm_addresses} and connecting")
    connected = configure_ip_and_connect(
        app, device_ip, timeout=DEVICE_CONNECT_TIMEOUT, arm_addresses=device_arm_addresses
    )
    if not connected:
        pytest.skip(f"AccuLoad device at {device_ip} not reachable/connected within {DEVICE_CONNECT_TIMEOUT}s")

    print("[STEP] Clicking ribbon 'Push All to AccuLoad'")
    uia_win = app.get_uia_window()
    click_ribbon_button(uia_win, "Push All to AccuLoad")

    print("[STEP] Waiting for the PUSH progress dialog to complete")
    completed = wait_for_progress_dialog_to_close(app, timeout=450)
    assert completed, "Push All to AccuLoad did not complete within the expected timeout"
    assert app.is_device_connected(), "Expected AccuMate to still be connected after Push All completes"

    pytest.skip(
        "AccuMate-side push mechanics verified above. Web-UI verification of the pushed "
        "'Pulse In 1' value and IP/Netmask/Gateway on the AccuLoad's own web HMI (regression.md "
        "steps 7-10) needs live element-ID discovery first - see phase3-a7-a14-web-hmi todo."
    )


@pytest.mark.requires_device
def test_a11_pulling_full_configuration(app, device_ip, device_arm_addresses):
    """
    A11: Pulling Full Configurations.

    This scenario's precondition (change several values on the AccuLoad's
    OWN web UI first) requires the same not-yet-discovered web element IDs
    as A10's verification, so it can't be set up automatically yet. This
    test instead exercises the AccuMate-side "Pull All from AccuLoad"
    mechanics against whatever the device's current configuration already
    is, confirming the pull completes and AccuMate stays connected - it
    does not (yet) assert that any specific value change was pulled down.
    """
    from workflows.terminal_emulator import wait_for_progress_dialog_to_close
    from controls.ribbon_controls import click_ribbon_button

    _connect_new_config(app, device_ip, device_arm_addresses)

    print("[STEP] Clicking ribbon 'Pull All from AccuLoad'")
    uia_win = app.get_uia_window()
    click_ribbon_button(uia_win, "Pull All from AccuLoad")

    print("[STEP] Waiting for the PULL progress dialog to complete")
    completed = wait_for_progress_dialog_to_close(app, timeout=450)
    assert completed, "Pull All from AccuLoad did not complete within the expected timeout"
    assert app.is_device_connected(), "Expected AccuMate to still be connected after Pull All completes"

    pytest.skip(
        "AccuMate-side pull mechanics verified above. Setting up/verifying the specific "
        "'Arm 1 Configuration', 'Pulse Input Tag', and 'Permissive 1 Sense' value changes on "
        "the AccuLoad's own web HMI (regression.md steps 3-13, 16-18) needs live element-ID "
        "discovery first - see phase3-a7-a14-web-hmi todo."
    )


@pytest.mark.requires_device
def test_a12_pushing_selected_configuration(app, device_ip, device_arm_addresses):
    """
    A12: Pushing Selected Configurations.

    Automates the AccuMate-side steps: open a new config, change "Number of
    Load Arms" under System Layout and a Digital Input value, select just
    the "System Layout" tree node, connect, then "Push Selected to
    AccuLoad" and confirm it completes.

    NOT YET AUTOMATED: steps 9-11 (verifying on the AccuLoad's own web UI
    that System Layout was updated but Digital Input 1 was NOT, since only
    System Layout was selected for the push) need live element-ID
    discovery - skipped here rather than asserted against guessed IDs.
    """
    from workflows.terminal_emulator import wait_for_progress_dialog_to_close
    from controls.ribbon_controls import click_ribbon_button, is_ribbon_button_enabled
    from pages.main_page import MainPage

    print("[STEP] Opening a new AccuMate Config File")
    new_config_file(app)

    page = MainPage(app, request=None)
    page.test_name = "test_a12_pushing_selected_configuration"

    print("[STEP] Changing 'Number of Load Arms' under System Layout")
    page.select_tree_path(["Config Directory", "System Layout"])
    page.edit_program_code_data("Number of Load Arms", "2")

    print("[STEP] Changing a Digital Input value under Dig In 01")
    page.select_tree_path(["Config Directory", "Digital Inputs", "Dig In 01"])
    page.edit_program_code_data("Digital Input Tag", "A12TEST")

    print("[STEP] Selecting only 'System Layout' before pushing")
    page.select_tree_path(["Config Directory", "System Layout"])

    print(f"[STEP] Configuring device IP {device_ip} / arm addresses {device_arm_addresses} and connecting")
    connected = configure_ip_and_connect(
        app, device_ip, timeout=DEVICE_CONNECT_TIMEOUT, arm_addresses=device_arm_addresses
    )
    if not connected:
        pytest.skip(f"AccuLoad device at {device_ip} not reachable/connected within {DEVICE_CONNECT_TIMEOUT}s")

    print("[STEP] Clicking ribbon 'Push Selected to AccuLoad'")
    uia_win = app.get_uia_window()
    if not is_ribbon_button_enabled(uia_win, "Push Selected to AccuLoad"):
        pytest.skip("'Push Selected to AccuLoad' ribbon button is disabled - nothing selected or not connected")
    click_ribbon_button(uia_win, "Push Selected to AccuLoad")

    print("[STEP] Waiting for the PUSH progress dialog to complete")
    completed = wait_for_progress_dialog_to_close(app, timeout=450)
    assert completed, "Push Selected to AccuLoad did not complete within the expected timeout"
    assert app.is_device_connected(), "Expected AccuMate to still be connected after Push Selected completes"

    pytest.skip(
        "AccuMate-side selective-push mechanics verified above. Web-UI verification that "
        "System Layout was updated but Digital Input 1 was NOT (regression.md steps 9-11) "
        "needs live element-ID discovery first - see phase3-a7-a14-web-hmi todo."
    )


@pytest.mark.requires_device
def test_a13_pulling_selected_configuration(app, device_ip, device_arm_addresses):
    """
    A13: Pulling Selected Configurations.

    This scenario's precondition (change Pulse Input/Output values on the
    AccuLoad's OWN web UI first) requires the same not-yet-discovered web
    element IDs as A10/A11. This test instead exercises the AccuMate-side
    "Pull Selected from AccuLoad" mechanics: open a new config, connect,
    select just "Pulse Inputs", and confirm a selective pull completes.
    """
    from workflows.terminal_emulator import wait_for_progress_dialog_to_close
    from controls.ribbon_controls import click_ribbon_button, is_ribbon_button_enabled
    from pages.main_page import MainPage

    _connect_new_config(app, device_ip, device_arm_addresses)

    page = MainPage(app, request=None)
    page.test_name = "test_a13_pulling_selected_configuration"

    print("[STEP] Selecting 'Pulse Inputs' before pulling")
    page.select_tree_path(["Config Directory", "Pulse Inputs"])

    print("[STEP] Clicking ribbon 'Pull Selected from AccuLoad'")
    uia_win = app.get_uia_window()
    if not is_ribbon_button_enabled(uia_win, "Pull Selected from AccuLoad"):
        pytest.skip("'Pull Selected from AccuLoad' ribbon button is disabled - device likely not connected")
    click_ribbon_button(uia_win, "Pull Selected from AccuLoad")

    print("[STEP] Waiting for the PULL progress dialog to complete")
    completed = wait_for_progress_dialog_to_close(app, timeout=450)
    assert completed, "Pull Selected from AccuLoad did not complete within the expected timeout"
    assert app.is_device_connected(), "Expected AccuMate to still be connected after Pull Selected completes"

    pytest.skip(
        "AccuMate-side selective-pull mechanics verified above. Setting up 'Pulse Input "
        "Function'/'Pulse Output Tag' changes on the AccuLoad's own web HMI first, and "
        "verifying only Pulse Inputs (not Outputs) were pulled (regression.md steps 3-13), "
        "needs live element-ID discovery first - see phase3-a7-a14-web-hmi todo."
    )


@pytest.mark.requires_device
def test_a14_downloading_totalizers(app, device_ip, device_arm_addresses):
    """
    A14: Downloading Totalizers - connect to the device, click 'Retrieve
    Totalizers', and confirm a new totalizers view appears (AccuMate-only,
    no AccuLoad web UI needed).
    """
    _connect_new_config(app, device_ip, device_arm_addresses)

    totalizers_view = retrieve_totalizers(app)
    print(f"[INFO] Totalizers view title: {totalizers_view.window_text()!r}")
    assert totalizers_view is not None, "Expected a Totalizers view/window to appear"
