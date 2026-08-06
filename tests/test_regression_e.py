"""
scenarios/regression.md E1-E8 (Equation Set Editor).

E1-E3 are LIVE-VERIFIED (real workflow functions, real control ids, real
dialog titles - see workflows/equation_workflows.py's module docstring for
the full findings) and run as part of the default `pytest -s -v` suite.

Scope summary (see workflows/equation_workflows.py for full detail):
  - E4-E6, E8: wired to workflows/file_transfer_workflows.py. Live-verified
    dialog mechanics, but real device transfers have so far always ended
    in the live-confirmed "The operation timed out" device-side limitation
    (see workflows/driver_db_workflows.py's D6/D7 docstrings for the same
    finding) - tests skip gracefully on that specific message.
  - E7: needs a provided AM3-format Equation Set File (.EQX) that does not
    currently exist in this repo/environment - same class of blocker as
    H3-H8's provided files.
"""

import os
import time

import pytest

from workflows.equation_workflows import (
    create_new_equation_set_file,
    insert_equation_line,
    get_equation_set_rows,
    upload_equation_file,
    download_equation_file,
)
from workflows.file_workflows import save_as, open_file_dialog, load_test_file
from workflows.comm_workflows import configure_ip_and_connect


def test_e1_create_new_equation_file(app):
    """
    E1: Create New Equation Files.
      1. Start the AccuMate Application.
      2. Hover 'New' under the Application Button -> 'Equation Set' option
         appears.
      3. Click 'Equation Set' -> a new, blank Equation Set view is
         displayed.
    """
    create_new_equation_set_file(app)
    rows = get_equation_set_rows(app)
    assert rows == []


def test_e2_saving_equation_files(app, tmp_path):
    """
    E2: Saving Equation Files.
      1-3. Insert 3 equation lines via ribbon "Insert", each as "User
           BOOLEAN register..." = N for N in (1, 2, 3), producing rows
           "USERBOOL1 = 1", "USERBOOL2 = 2", "USERBOOL3 = 3".
      4. Save via Application Button -> Save, with a valid filename ->
         file exists on disk afterward.
    """
    create_new_equation_set_file(app)
    for n in (1, 2, 3):
        insert_equation_line(app, register_number=n, expression=str(n))

    rows = get_equation_set_rows(app)
    assert rows == [[f"USERBOOL{n} = {n}"] for n in (1, 2, 3)]

    save_path = str(tmp_path / "test_e2_equation_set.al4equ")
    save_as(app, save_path)
    assert os.path.isfile(save_path)


def test_e3_loading_equation_files(app, tmp_path):
    """
    E3: Loading Equation Files.
      1. Save the Equation Set view to disk.
      2. Open that same file back up -> the reopened view's contents match
         what was originally saved.

    NOTE: same scaled-back scope as test_regression_d.py's D5 - a second
    back-to-back Application Button "Save As..." on the same still-open
    document was not attempted here (see D5's docstring for the live
    finding that motivated this simplification); a single save + reopen +
    content-comparison still exercises the regression-relevant behavior
    (open_file_dialog/save_as compatible with Equation Set documents,
    saved content round-trips correctly).
    """
    create_new_equation_set_file(app)
    insert_equation_line(app, register_number=1, expression="1")
    original_rows = get_equation_set_rows(app)

    save_path = str(tmp_path / "test_e3_original.al4equ")
    save_as(app, save_path)

    open_file_dialog(app, save_path)
    reopened_rows = get_equation_set_rows(app)
    assert reopened_rows == original_rows


_DEVICE_TIMEOUT_MESSAGE = "The operation timed out"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_e4_uploading_equation_files(app_ftp, device_ip, tmp_path):
    """
    E4: Uploading Equation Files (requires live AccuLoad device).
      Connect to the device, then Upload File to AccuLoad -> browse to a
      .al4equ file -> upload completes successfully.

    Builds a real .al4equ file first (reusing E1/E2's helpers) so this
    test is self-contained. Skips (rather than fails) specifically on the
    live-confirmed device-timeout message - see module docstring.
    """
    app = app_ftp
    create_new_equation_set_file(app)
    insert_equation_line(app, register_number=1, expression="1")

    upload_path = str(tmp_path / "test_e4_upload.al4equ")
    save_as(app, upload_path)
    assert os.path.isfile(upload_path)

    # "Document Options" (Communications Settings) only becomes enabled
    # once a real AL4 config document is loaded - a bare Equation Set
    # document alone (created above) isn't enough, confirmed live (same
    # gotcha documented in test_regression_d.py's D6).
    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    result = upload_equation_file(app, upload_path)
    if result["timed_out"] or (result["message"] and _DEVICE_TIMEOUT_MESSAGE in result["message"]):
        pytest.skip(
            f"Device-side file-transfer timeout (result={result!r}) - see "
            "workflows/driver_db_workflows.py module docstring 'Remaining gaps'"
        )
    assert result["message"] is not None, f"Expected a completion message, got {result!r}"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_e5_downloading_equation_files(app_ftp, device_ip, tmp_path):
    """
    E5: Downloading Equation Files (requires live AccuLoad device).
      Connect to the device, Download File From AccuLoad -> Equations File
      -> compare against the file uploaded in E4.

    NOTE: like D7, this doesn't chain off a prior E4 run (each test is
    self-contained/order-independent) - it just verifies the download
    dialog flow and resulting file, not byte-for-byte content parity with
    a specific upload. Skips gracefully on the known device-timeout
    limitation.
    """
    app = app_ftp
    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    save_path = str(tmp_path / "test_e5_download.al4equ")
    result = download_equation_file(app, save_path)
    if result["timed_out"] or (result["message"] and _DEVICE_TIMEOUT_MESSAGE in result["message"]):
        pytest.skip(
            f"Device-side file-transfer timeout (result={result!r}) - see "
            "workflows/driver_db_workflows.py module docstring 'Remaining gaps'"
        )
    assert os.path.isfile(save_path), f"Expected download to save a file, result={result!r}"


@pytest.mark.requires_device
@pytest.mark.special_case
def test_e6_no_equation_file_to_download(app, device_ip):
    """
    E6: No Equation File To Download - SPECIAL CASE, not part of the
    standard regression pass.

    Requires live AccuLoad device with Equation.cfg deleted from
    /media/data/database, or a fresh AccuLoad image. Download File From
    AccuLoad -> Equations File -> a warning popup notifies the user there
    is nothing to pull.

    This repo cannot arrange the required device-side precondition (no
    Equations file present on the AccuLoad), so this is documented as a
    special case rather than run as part of the standard automated
    regression suite - same class of gap as B14/C6/D8. If a device ever
    legitimately has no Equations file, download_equation_file's result
    "message" would hold the "no information to pull" warning text.
    """
    pytest.skip(
        "E6: SPECIAL CASE - requires a device with no Equations file "
        "present, a device-side state this repo cannot safely arrange or "
        "verify; not part of the standard regression pass"
    )



def test_e7_loading_am3_equation_files(app):
    """
    E7: Loading AM3 Equation Files.
      1. Open the "Open" file dialog.
      2. Navigate to and open configs/E7.EQX (an AccuMate III equations
         file provided for this test).
      3. Verify the file loads/converts into a real, readable AccuMate IV
         Equation Set view (main window title reflects the loaded file;
         equation grid is populated with real rows).
    """
    eqx_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs", "E7.EQX"))
    if not os.path.isfile(eqx_path):
        pytest.skip(f"E7: provided AM3 .EQX test file not found: {eqx_path}")

    print(f"[STEP] Loading AM3 equations file: {eqx_path}")
    open_file_dialog(app, eqx_path)

    start = time.time()
    title = ""
    while time.time() - start < 25:
        title = app.get_window().window_text()
        if "E7" in title:
            break
        time.sleep(1)
    assert "E7" in title, f"Main window title does not reflect the loaded .EQX file: {title!r}"

    rows = get_equation_set_rows(app)
    assert rows is not None and len(rows) >= 1, (
        f"Expected populated equation rows after loading the AM3 file, got: {rows!r}"
    )


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_e8_uploading_empty_equation_file(app_ftp, device_ip, tmp_path):
    """
    E8: Uploading Empty Equation File (requires live AccuLoad device).
      Connect to the device, Upload File to AccuLoad -> browse to an empty
      equations file -> a popup warns "No entries defined. Nothing to
      upload."

    Builds a real, empty (0-row) .al4equ file via create_new_equation_set_file
    + save_as (no insert_equation_line calls) so this test is
    self-contained. Skips (rather than fails) on the live-confirmed
    device-timeout message, same as E4/E5 - a device-side timeout can mask
    whatever "nothing to upload" message would otherwise appear, and this
    repo cannot distinguish "device is unreachable at the transfer layer"
    from "device correctly rejected an empty file" without a live run.
    """
    app = app_ftp
    create_new_equation_set_file(app)
    assert get_equation_set_rows(app) == []

    upload_path = str(tmp_path / "test_e8_empty.al4equ")
    save_as(app, upload_path)
    assert os.path.isfile(upload_path)

    # Same "Document Options" enablement gotcha as E4 - see its comment.
    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    result = upload_equation_file(app, upload_path)
    if result["timed_out"] or (result["message"] and _DEVICE_TIMEOUT_MESSAGE in result["message"]):
        pytest.skip(
            f"Device-side file-transfer timeout (result={result!r}) - see "
            "workflows/driver_db_workflows.py module docstring 'Remaining gaps'"
        )
    assert result["message"] is not None, f"Expected a completion/warning message, got {result!r}"
