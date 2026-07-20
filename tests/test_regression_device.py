import pytest

from workflows.file_workflows import new_config_file
from workflows.comm_workflows import (
    configure_ip_and_connect,
    open_communications_settings,
    close_communications_settings,
    get_configured_ip,
    get_arm_address,
)
from workflows.terminal_emulator import (
    open_terminal_emulator,
    send_command,
    get_output_text,
    switch_to_home_ribbon_tab,
    wait_for_progress_dialog_to_close,
)
from controls.ribbon_controls import click_ribbon_button, is_ribbon_button_enabled

DEVICE_CONNECT_TIMEOUT = 15
# PUSH/PULL transfer the full config to/from the device section by section
# over the network and can legitimately take a while - live monitoring of a
# real PUSH (blank/default config) clocked a full 0%->100% transfer at
# roughly 300-350 seconds (~3s per percentage point), so this needs a much
# bigger budget than a typical UI-wait timeout to avoid a real in-progress
# transfer being mistaken for "stuck".
PUSH_PULL_TIMEOUT = 450


def _connect_new_config(app, device_ip, device_arm_addresses):
    """
    Shared setup for A18-A22: open a new blank config file, configure its
    Communications Addresses to match the physical device (see
    conftest.DEFAULT_ACCUMATE_ARM_ADDRESSES), and connect. Skips the test
    (rather than failing) if the device isn't reachable, matching the
    existing test_device_connectivity.py pattern.
    """
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
def test_a18_terminal_emulator_hi_command(app, device_ip, device_arm_addresses):
    """
    A18: Smithcomm "HI" - open the Terminal Emulator and confirm the
    AccuLoad responds with identifying information to the "HI" command.
    """
    _connect_new_config(app, device_ip, device_arm_addresses)

    win = open_terminal_emulator(app)
    send_command(win, "HI")

    output = get_output_text(win)
    print(f"[INFO] Terminal Emulator output: {output!r}")
    assert "AccuLoad" in output, f"Expected AccuLoad identification response, got: {output!r}"


@pytest.mark.requires_device
@pytest.mark.disruptive
def test_a19_terminal_push_command(app, device_ip, device_arm_addresses):
    """
    A19: Terminal PUSH Command - push the open config's settings to the
    AccuLoad device.

    Safety guard: PUSH writes the currently-open config's values to the
    real device, so this only proceeds if the config's IP Address and Arm
    Communications Addresses match the known-safe values already verified
    against the physical device (device_ip / device_arm_addresses fixtures).
    If a caller passes different --accumate-device-ip/--accumate-arm
    values, or the dialog doesn't reflect what was just set, the PUSH step
    is skipped rather than risking pushing unintended settings.

    KNOWN DISRUPTIVE SIDE EFFECT (confirmed live): PUSH overwrites the
    device's IP address/netmask/gateway with the blank/default config's
    (unset) network parameters, breaking the device's real network
    configuration and causing the *next* connection attempt (this test or
    any other) to fail until the device is manually reconfigured. The
    IP/arm-address safety guard above does NOT protect against this - it
    only checks AccuMate's own "which IP to connect to" client setting, not
    the config document's separate device-network-parameters section that
    actually gets written to the device. Because of this, the test is
    marked `disruptive` and excluded from the default test run (see
    pytest.ini's addopts) - run it deliberately with `-m disruptive` as
    part of a full regression pass, and be prepared to manually restore the
    device's network settings afterward.
    """
    _connect_new_config(app, device_ip, device_arm_addresses)

    print("[STEP] Verifying configured IP/arm addresses match expected safe values before PUSH")
    dlg = open_communications_settings(app)
    actual_ip = get_configured_ip(dlg)
    actual_arms = [get_arm_address(dlg, arm) for arm in range(1, 7)]
    close_communications_settings(dlg, accept=False)

    expected_arms = [str(a) for a in device_arm_addresses]
    if actual_ip != device_ip or actual_arms != expected_arms:
        pytest.skip(
            "Configured IP/arm addresses do not match the expected safe values - "
            f"expected IP={device_ip} arms={expected_arms}, got IP={actual_ip} arms={actual_arms}. "
            "Skipping PUSH to avoid pushing unintended settings to the live device."
        )

    win = open_terminal_emulator(app)
    send_command(win, "PUSH", settle_time=1.5)

    print("[STEP] Waiting for the PUSH progress dialog to complete (may take a while over the network)")
    completed = wait_for_progress_dialog_to_close(app, timeout=PUSH_PULL_TIMEOUT)
    assert completed, (
        f"PUSH did not complete within {PUSH_PULL_TIMEOUT}s - progress dialog still open"
    )

    output = get_output_text(win)
    print(f"[INFO] Terminal Emulator output after PUSH: {output!r}")

    print("[STEP] Switching back to Home ribbon tab and verifying device is still connected")
    switch_to_home_ribbon_tab(app)
    assert app.is_device_connected(), "Expected AccuMate to still be connected after PUSH completes"


@pytest.mark.requires_device
def test_a20_terminal_pull_command(app, device_ip, device_arm_addresses):
    """
    A20: Terminal PULL Command - pull the AccuLoad's current configuration
    settings (read-only, doesn't modify the device).
    """
    _connect_new_config(app, device_ip, device_arm_addresses)

    win = open_terminal_emulator(app)
    send_command(win, "PULL", settle_time=1.5)

    print("[STEP] Waiting for the PULL progress dialog to complete (may take a while over the network)")
    completed = wait_for_progress_dialog_to_close(app, timeout=PUSH_PULL_TIMEOUT)
    assert completed, (
        f"PULL did not complete within {PUSH_PULL_TIMEOUT}s - progress dialog still open"
    )

    print("[STEP] Switching back to Home ribbon tab and verifying device is still connected")
    switch_to_home_ribbon_tab(app)
    assert app.is_device_connected(), "Expected AccuMate to still be connected after PULL completes"


@pytest.mark.requires_device
def test_a21_going_offline(app, device_ip, device_arm_addresses):
    """
    A21: Going Offline - clicking the ribbon "Go Offline" button
    disconnects AccuMate from the AccuLoad.
    """
    _connect_new_config(app, device_ip, device_arm_addresses)
    assert app.is_device_connected(), "Expected to be connected before testing Go Offline"

    print("[STEP] Clicking ribbon 'Go Offline'")
    uia_win = app.get_uia_window()
    click_ribbon_button(uia_win, "Go Offline")

    assert not app.wait_for_device_connection(timeout=5), (
        "Expected AccuMate to report disconnected after clicking 'Go Offline'"
    )


@pytest.mark.requires_device
def test_a22_retrying_communication(app, device_ip, device_arm_addresses):
    """
    A22: Retrying Communication - after going offline, clicking 'Retry
    Comm' re-establishes the connection to the AccuLoad.
    """
    _connect_new_config(app, device_ip, device_arm_addresses)
    assert app.is_device_connected(), "Expected to be connected before testing Go Offline/Retry Comm"

    print("[STEP] Clicking ribbon 'Go Offline'")
    uia_win = app.get_uia_window()
    click_ribbon_button(uia_win, "Go Offline")
    assert not app.wait_for_device_connection(timeout=5)

    print("[STEP] Clicking ribbon 'Retry Comm'")
    uia_win = app.get_uia_window()
    click_ribbon_button(uia_win, "Retry Comm")

    assert app.wait_for_device_connection(timeout=DEVICE_CONNECT_TIMEOUT), (
        "Expected AccuMate to reconnect after clicking 'Retry Comm'"
    )
