import os

import pytest

from workflows.file_workflows import load_config_file
from workflows.comm_workflows import configure_ip_and_connect
from workflows.terminal_emulator import wait_for_push_pull_with_stall_detection
from controls.ribbon_controls import click_ribbon_button

DEVICE_CONNECT_TIMEOUT = 45  # bumped from 15s: remote/VPN sessions add connect latency
# A full PUSH of the config under investigation can legitimately run several
# minutes (a blank/default config was clocked at ~300-350s live) - this is
# the overall budget, separate from the stall-detection threshold below,
# which is what actually distinguishes "slow" from "stuck".
PUSH_TIMEOUT = 900
STALL_THRESHOLD_SECONDS = 60


@pytest.mark.requires_device
@pytest.mark.disruptive
@pytest.mark.manual_investigation
def test_field_push_all_hang_diagnostic(app, record_step, config_file, device_ip, device_arm_addresses):
    """
    Field diagnostic: "Push All to AccuLoad" appears to hang partway through
    transferring a full configuration on the latest build.

    This is NOT a regression.md scenario and NOT a repeatable pass/fail
    regression check - it's a one-off, purpose-built investigation of a
    specific field-reported bug. It is intentionally excluded from the
    default test run and from `-m disruptive` regression passes (see the
    `manual_investigation` marker in pytest.ini); run it explicitly by node
    id or `-m manual_investigation` while investigating this issue, with
    the problem configuration file passed via --accumate-config-file:

        pytest -s -v tests/test_field_push_hang_diagnostic.py \\
            --accumate-config-file="C:\\path\\to\\the\\provided\\config.AL4" \\
            --accumate-device-ip=10.55.66.70

    Steps:
    1. Load the provided (problem) configuration file.
    2. Configure the device IP/arm addresses and connect.
    3. Click ribbon "Push All to AccuLoad".
    4. Monitor the transfer's live [NN%] progress. A genuine STALL (no
       percentage change for STALL_THRESHOLD_SECONDS) is treated as
       distinct from the transfer simply being slow/large - see
       workflows.terminal_emulator.wait_for_push_pull_with_stall_detection
       for the detection mechanism and why a plain timeout can't make this
       distinction on its own.

    KNOWN DISRUPTIVE SIDE EFFECT (same root cause as test_a10/test_a19):
    a completed "Push All to AccuLoad" overwrites the device's IP/netmask/
    gateway with the pushed config's own comm-settings section, which can
    break the connection for subsequent test runs against the same
    device/IP until it's manually reconfigured.
    """
    if not config_file:
        pytest.skip(
            "No --accumate-config-file provided - pass the problem configuration "
            "file that reproduces the Push All hang via --accumate-config-file"
        )

    test_name = "test_field_push_all_hang_diagnostic"
    screenshot_dir = os.path.join("screenshots", test_name, "push_diagnostics")

    print(f"[STEP] Loading config file: {config_file}")
    try:
        load_config_file(app, config_file)
    except Exception as exc:
        record_step(1, "failed", app=app, screenshot=True, note=f"Failed to load config file: {exc}")
        record_step(2, "skipped", note="Not reached - step 1 failed")
        record_step(3, "skipped", note="Not reached - step 1 failed")
        record_step(4, "skipped", note="Not reached - step 1 failed")
        raise
    else:
        record_step(1, "passed", note=f"Loaded {os.path.basename(config_file)}")

    print(f"[STEP] Configuring device IP {device_ip} / arm addresses {device_arm_addresses} and connecting")
    connected = configure_ip_and_connect(
        app, device_ip, timeout=DEVICE_CONNECT_TIMEOUT, arm_addresses=device_arm_addresses
    )
    if not connected:
        record_step(2, "failed", app=app, screenshot=True,
                    note=f"Device at {device_ip} not reachable/connected within {DEVICE_CONNECT_TIMEOUT}s")
        record_step(3, "skipped", note="Not reached - step 2 failed")
        record_step(4, "skipped", note="Not reached - step 2 failed")
        pytest.skip(f"AccuLoad device at {device_ip} not reachable/connected within {DEVICE_CONNECT_TIMEOUT}s")
    record_step(2, "passed", note=f"Connected to {device_ip}")

    print("[STEP] Clicking ribbon 'Push All to AccuLoad'")
    uia_win = app.get_uia_window()
    click_ribbon_button(uia_win, "Push All to AccuLoad")
    record_step(3, "passed", note="Push All to AccuLoad clicked")

    print("[STEP] Monitoring transfer progress for a stall")
    diagnostics = wait_for_push_pull_with_stall_detection(
        app,
        timeout=PUSH_TIMEOUT,
        stall_threshold=STALL_THRESHOLD_SECONDS,
        screenshot_dir=screenshot_dir,
    )

    history_summary = ", ".join(f"{pct}%@{t:.0f}s" for t, pct in diagnostics.percent_history) or "(none observed)"
    print(f"[INFO] Percent history: {history_summary}")

    if diagnostics.stalled:
        note = (
            f"STALLED at {diagnostics.last_percent}% for {diagnostics.stall_duration:.1f}s "
            f"(>= {STALL_THRESHOLD_SECONDS}s threshold). AccuMate main window responsive: "
            f"{diagnostics.app_responsive}. Final title: {diagnostics.final_title!r}. "
            f"History: {history_summary}"
        )
        record_step(4, "failed", note=note, screenshot_path=diagnostics.progress_screenshot)
        pytest.fail(
            "Push All to AccuLoad appears STALLED, not just slow: "
            f"no progress change for {diagnostics.stall_duration:.1f}s "
            f"(last observed {diagnostics.last_percent}%, threshold {STALL_THRESHOLD_SECONDS}s). "
            f"AccuMate main window responsive to messages: {diagnostics.app_responsive} "
            f"(False/None suggests AccuMate itself may be hung, not just the device transfer). "
            f"Progress screenshot: {diagnostics.progress_screenshot!r}. "
            f"Full percent/time history: {history_summary}"
        )

    if not diagnostics.completed:
        record_step(4, "failed",
                    note=f"Did not complete within {PUSH_TIMEOUT}s (no stall detected - still progressing). "
                         f"Last observed {diagnostics.last_percent}%. History: {history_summary}")
        pytest.fail(
            f"Push All to AccuLoad did not complete within the {PUSH_TIMEOUT}s overall budget "
            f"(last observed {diagnostics.last_percent}%, no single stall detected - "
            "the transfer may simply need a longer overall timeout). "
            f"Full percent/time history: {history_summary}"
        )

    record_step(4, "passed", note=f"Transfer completed without stalling. History: {history_summary}")

    print("[STEP] Verifying AccuMate is still connected after Push All completes")
    assert app.wait_for_device_connection(timeout=30), (
        "Expected AccuMate to still be connected after Push All completes"
    )
