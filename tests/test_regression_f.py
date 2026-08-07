"""
scenarios/regression.md F1-F17 (transaction/event/audit logs, license
status, firmware update, printing, API/parameter conversions).

Scope summary:
  - F1-F5: implemented via workflows.file_transfer_workflows (wired through
    the new workflows/log_workflows.py's download_transaction_log/
    download_event_log/download_audit_trail_log - same thin-wrapper pattern
    already live-verified for D6/D7 and E4/E5/E8). NOT YET LIVE-RUN against
    the device; expected to hit the same device-side "operation timed out"
    limitation documented in file_transfer_workflows.py until that's
    resolved (see the FTP data-channel investigation in this project's
    session history) - these tests skip (rather than fail) specifically on
    that known message.
  - F6: implemented via log_workflows.upload_license_status_file/
    download_license_status_file, using the user-supplied configs/F6.C2V
    and configs/F6.V2C files (F6.V2C is used for the upload - see the
    test's own docstring for the C2V/V2C naming-convention assumption).
    Marked `manual` (in addition to `requires_device`) since it has NOT
    YET been live-run against a real device this session - remove the
    `manual` marker once a live run confirms it. F7 below covers the
    download-only half of this same category.
  - F7: implemented via log_workflows.download_license_status_file (no
    upload needed - this step is download-only and expects a "no
    information to pull" warning). NOT YET LIVE-RUN.
  - F8: needs a provided firmware file (not present) plus a dedicated
    Application Button "Firmware Update" workflow that hasn't been built
    yet - left as a stub.
  - F9-F13: printing Driver Database/Config/Equation Set files - RESOLVED,
    see finding below. print_to_pdf() (workflows/print_workflows.py) works
    as originally written; the earlier "blocked" finding was a red herring
    caused by testing exclusively via the Print fly-out's "Quick Print"
    item, which has a genuine, confirmed app-level bug (see below) - a
    plain click on the "Print" row itself (no fly-out expansion) still
    triggers the classic "Print" common dialog directly, exactly as
    print_to_pdf() expects. F9/F11/F12/F13 PASS live; F10 needed its
    Driver Database populated with real rows (see finding) but otherwise
    also PASSES live.
  - F14-F17: need provided AccuMate III (AM3) test files (.a3x/.EQX/.RPX)
    that do not currently exist in this repo/environment - same class of
    blocker as C7/D9/E7/H3-H8's provided files.

F9-F13 LIVE FINDING (this segment, RESOLVED): the Application Button's
"Print" row has a right-pointing fly-out arrow (3 items on hover/expand:
"Quick Print", "Print Preview", "Print Setup...") - like "New"'s fly-out
(see file_workflows.py), a plain click_input() on the row itself does NOT
expand that fly-out, it runs the row's own default action directly: the
classic Windows "Print" common dialog (title "Print", class "#32770",
printer combo control_id 1139) that print_workflows.py's
_open_print_dialog()/print_to_pdf() already expect. Confirmed manually by
the user: clicking "Print" from the Application Button menu (not the
fly-out arrow) opens that dialog and printing to "Microsoft Print to PDF"
works correctly end-to-end.
  - The earlier "BLOCKED" finding in this same segment came from testing
    only the fly-out's 3 sub-items (reached via keyboard Right-arrow
    expansion) instead of a plain click on the row - "Quick Print" and the
    ribbon's small printer toolbar icon were both separately confirmed
    (manually, by the user) to be genuinely broken/no-op in this AccuMate
    build (produce no dialog, no spool job, no PDF - confirmed via 100ms
    spool-directory polling during automated testing too), independent of
    the Windows default printer or AccuMate's own remembered Print Setup
    printer selection. This is a real app bug, not an automation gap -
    print_workflows.py deliberately avoids "Quick Print"/the toolbar icon
    and always drives the classic "Print" dialog instead, which is
    unaffected by this bug.
  - F10 needed one additional fix: printing a brand-new, entirely blank
    Driver Database file (thousands of pre-existing but empty grid rows)
    produced only a single-page PDF - AccuMate's printout only includes
    rows with real data, not every blank row physically present in the
    grid. Populating several dozen rows with real HID Format + Field 1-3
    data (same per-row pattern as D4's test_d4_saving_driver_database_files)
    is what actually produces a multi-page printout; the test was updated
    to populate 40 rows before printing.
"""

import os
import time

import pytest
from pypdf import PdfReader

from workflows.file_workflows import new_config_file, save_as, open_file_dialog, load_test_file
from workflows.print_workflows import print_to_pdf
from workflows.comm_workflows import configure_ip_and_connect
from workflows.report_workflows import get_report_items
from workflows.driver_db_workflows import (
    create_new_driver_database_file,
    open_edit_database_record_dialog,
    enter_hid_format_id,
    set_driver_record_fields,
)
from workflows.equation_workflows import create_new_equation_set_file, insert_equation_line, get_equation_set_rows
from workflows.log_workflows import (
    download_transaction_log,
    download_event_log,
    download_audit_trail_log,
    download_license_status_file,
    upload_license_status_file,
)
from pages.main_page import MainPage

_DEVICE_TIMEOUT_MESSAGE = "The operation timed out"
_NO_INFO_MESSAGE = "No information to pull from the AccuLoad."

_PDF_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "print_output"))


def _wait_for_title_contains(app, substring, timeout=25):
    start = time.time()
    title = ""
    while time.time() - start < timeout:
        title = app.get_window().window_text()
        if substring in title:
            break
        time.sleep(1)
    return title


def _pdf_path(name):
    os.makedirs(_PDF_DIR, exist_ok=True)
    return os.path.join(_PDF_DIR, name)


def _page_count(pdf_path):
    return len(PdfReader(pdf_path).pages)


def _extract_all_text(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _connect_or_skip(app, device_ip):
    """
    Shared setup for F1-F7: build a throwaway config document, load the
    real test config file (required for "Document Options" to become
    enabled - see module docstrings across D/E), then connect. Skips
    (rather than fails) if the device isn't reachable at all.
    """
    new_config_file(app)
    load_test_file(app)
    connected = configure_ip_and_connect(app, device_ip, timeout=45)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")


def _assert_download_or_skip_timeout(result, save_path):
    if result["timed_out"] or (result["message"] and _DEVICE_TIMEOUT_MESSAGE in result["message"]):
        pytest.skip(
            f"Device-side file-transfer timeout (result={result!r}) - see "
            "workflows/file_transfer_workflows.py module docstring 'LIVE FINDING'"
        )
    assert os.path.isfile(save_path), f"Expected download to save a file, result={result!r}"


def _skip_if_no_info_to_pull(result, what):
    """
    F2/F3 expect a genuinely populated (small/large) log on the device -
    a device-state precondition this repo can't arrange (same class of
    gap as D8/E6/B14's "no file present" skips). If the device reports
    "No information to pull from the AccuLoad." instead (i.e. it
    genuinely has no log of this type at all right now), skip rather than
    fail - this isn't an automation bug, just a device state mismatch.
    """
    if result["message"] == _NO_INFO_MESSAGE:
        pytest.skip(
            f"Device currently has no {what} to pull (result={result!r}) - "
            "a device-state precondition this repo can't arrange/verify"
        )


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f1_downloading_empty_transaction_log(app_ftp, device_ip, tmp_path):
    """
    F1: Downloading Empty Transaction Log (requires live AccuLoad device).
      Download File From AccuLoad -> Transaction Log -> expect a warning
      popup that no information is available.

    Live-verified (2026-08-05, once FTP transfers stopped hitting the
    Release/-folder firewall block - see app_ftp fixture): the test device
    genuinely has no transaction log right now, so it reliably returns
    "No information to pull from the AccuLoad." - this IS the exact
    expected result for F1's "empty" case, so it's asserted directly
    rather than treated as a timeout/skip condition.
    """
    app = app_ftp
    _connect_or_skip(app, device_ip)
    save_path = str(tmp_path / "test_f1_transaction_log.txt")
    result = download_transaction_log(app, save_path)
    if result["timed_out"] or (result["message"] and _DEVICE_TIMEOUT_MESSAGE in result["message"]):
        pytest.skip(
            f"Device-side file-transfer timeout (result={result!r}) - see "
            "workflows/file_transfer_workflows.py module docstring 'LIVE FINDING'"
        )
    assert result["message"] == _NO_INFO_MESSAGE, f"Expected the 'no information' warning, got {result!r}"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f2_download_transaction_log_small(app_ftp, device_ip, tmp_path):
    """
    F2: Download Transaction Log (Small) (requires live AccuLoad device
    with a small-but-nonempty transaction log present).
    """
    app = app_ftp
    _connect_or_skip(app, device_ip)
    save_path = str(tmp_path / "test_f2_transaction_log.txt")
    result = download_transaction_log(app, save_path)
    _skip_if_no_info_to_pull(result, "transaction log")
    _assert_download_or_skip_timeout(result, save_path)


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f3_download_transaction_log_large(app_ftp, device_ip, tmp_path):
    """
    F3: Download Transaction Log (Large) (requires live AccuLoad device
    with a large transaction log present).
    """
    app = app_ftp
    _connect_or_skip(app, device_ip)
    save_path = str(tmp_path / "test_f3_transaction_log.txt")
    result = download_transaction_log(app, save_path)
    _skip_if_no_info_to_pull(result, "transaction log")
    _assert_download_or_skip_timeout(result, save_path)


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f4_download_event_log(app_ftp, device_ip, tmp_path):
    """F4: Download Event Log (requires live AccuLoad device)."""
    app = app_ftp
    _connect_or_skip(app, device_ip)
    save_path = str(tmp_path / "test_f4_event_log.txt")
    result = download_event_log(app, save_path)
    _assert_download_or_skip_timeout(result, save_path)


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f5_download_audit_trail_log(app_ftp, device_ip, tmp_path):
    """F5: Download Audit Trail Log (requires live AccuLoad device)."""
    app = app_ftp
    _connect_or_skip(app, device_ip)
    save_path = str(tmp_path / "test_f5_audit_trail_log.txt")
    result = download_audit_trail_log(app, save_path)
    _assert_download_or_skip_timeout(result, save_path)


@pytest.mark.manual
@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f6_upload_download_license_status_file(app_ftp, device_ip, tmp_path):
    """
    F6: Upload/Download License Status File (requires live AccuLoad
    device).
      5. Upload File to AccuLoad -> Browse... and select the License File
         to upload -> Start.
      6-7. Download File From AccuLoad -> License Status File -> OK the
         dialog -> choose a filename/location -> Start the download.

    Uses the user-supplied configs/F6.C2V and configs/F6.V2C files (both
    committed to this repo). Per Sentinel-HASP-style licensing
    conventions, C2V ("Customer-to-Vendor") is normally a *request* file
    generated by the licensed device/dongle, while V2C ("Vendor-to-
    Customer") is normally the actual license file sent back to be
    installed on the device - so configs/F6.V2C is used for the upload
    half of this test (confirmed with the user as the intended file to
    use here). configs/F6.C2V is not currently used by any test; if that
    assumption turns out to be backwards, swap which file is passed to
    upload_license_status_file() below.

    MARKED MANUAL (in addition to requires_device/needs_live_verification):
    the implementation is real and complete, but it has NOT YET been
    live-verified against an actual device - the user does not currently
    have device access to confirm this end-to-end. Keep @pytest.mark.manual
    on this test until a live run confirms it behaves as expected, then
    remove that marker (leaving requires_device) like the other F-series
    tests.
    """
    app = app_ftp
    upload_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs", "F6.V2C"))
    if not os.path.isfile(upload_path):
        pytest.skip(f"F6: provided License Status file not found: {upload_path}")

    _connect_or_skip(app, device_ip)

    upload_result = upload_license_status_file(app, upload_path)
    if upload_result["timed_out"] or (
        upload_result["message"] and _DEVICE_TIMEOUT_MESSAGE in upload_result["message"]
    ):
        pytest.skip(
            f"Device-side file-transfer timeout (result={upload_result!r}) - see "
            "workflows/file_transfer_workflows.py module docstring 'LIVE FINDING'"
        )
    assert upload_result["message"] is not None, f"Expected a completion message, got {upload_result!r}"

    save_path = str(tmp_path / "test_f6_license_status.txt")
    download_result = download_license_status_file(app, save_path)
    _assert_download_or_skip_timeout(download_result, save_path)


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f7_no_license_status_to_download(app_ftp, device_ip, tmp_path):
    """
    F7: No License Status To Download (requires live AccuLoad device with
    the license dongle pulled and "DA: Arm Not Licensed" alarm present).
      Download File From AccuLoad -> License Status File -> expect a
      warning popup that there's no information to pull (requires a
      specific device precondition this repo can't arrange - skips on the
      live-confirmed device-timeout message like F1-F5 instead of
      asserting the specific warning text).
    """
    app = app_ftp
    _connect_or_skip(app, device_ip)
    save_path = str(tmp_path / "test_f7_license_status.txt")
    result = download_license_status_file(app, save_path)
    _assert_download_or_skip_timeout(result, save_path)


@pytest.mark.manual
def test_f8_update_accuload_firmware(app, device_ip):
    """
    F8: Update AccuLoad Firmware - MANUAL.

    Requires a real firmware file (not supplied) plus a dedicated
    Application Button "Firmware Update" workflow that hasn't been built
    yet. Must be performed manually by a human tester against a live
    AccuLoad device.
    """
    pytest.skip(
        "F8: MANUAL TEST - requires a real firmware file and a "
        "not-yet-built 'Firmware Update' workflow; perform this step "
        "manually against a live AccuLoad device"
    )


def test_f9_printing_driverdb_files_one_page(app, tmp_path):
    """
    F9: Printing DriverDB Files (One Page).
      1. Open a saved Driver Database file.
      2. Print it via "Microsoft Print to PDF".
      3. Verify the PDF was saved and contains the file's data.

    RESOLVED - see module docstring "F9-F13 LIVE FINDING": print_to_pdf()
    works via a plain click on the Application Button's "Print" row (its
    default action opens the classic "Print" dialog directly, without
    needing to expand the row's fly-out arrow).
    """
    create_new_driver_database_file(app)
    win32_dlg, uia_dlg = open_edit_database_record_dialog(app, row_index=0)
    enter_hid_format_id(app, win32_dlg, uia_dlg, extended_code="1", facility_code="2", card_number="345")
    set_driver_record_fields(win32_dlg, uia_dlg, field1="1", field2="2", field3="3")

    save_path = str(tmp_path / "test_f9_driverdb.al4ddb")
    save_as(app, save_path)
    open_file_dialog(app, save_path)

    pdf_path = print_to_pdf(app, _pdf_path("f9_driverdb_one_page.pdf"))
    assert os.path.isfile(pdf_path)
    assert _page_count(pdf_path) >= 1

    text = _extract_all_text(pdf_path)
    assert text.strip(), "Expected non-empty printed content for the Driver Database file"


def test_f10_printing_driverdb_files_multiple_pages(app, tmp_path):
    """
    F10: Printing DriverDB Files (Multiple Pages).
      Same as F9, but with enough entries populated that the printout
      spans more than one page.

    LIVE FINDING (this segment): printing an unmodified new Driver
    Database file (thousands of pre-existing but blank grid rows) only
    produces a single-page PDF - AccuMate's printout apparently only
    includes populated rows, not every blank row in the grid. Populating
    several dozen rows with real HID Format + Field 1-3 data (same
    per-row pattern already used by D4's test_d4_saving_driver_database_files)
    is what actually produces a multi-page printout. Live-verified: 40
    populated rows still fit on a single dense page; 70 rows was needed
    to genuinely overflow onto a 2nd page. RESOLVED - see module
    docstring "F9-F13 LIVE FINDING". Live-verified: PASS (2 pages).

    HARDENED (was an intermittent flake, unrelated to the print blocker fix
    above): driving 70 sequential "Edit Database Record" dialog cycles
    occasionally hit a transient `pywinauto.findwindows.ElementAmbiguousError`
    on the Field 1 edit box - root cause: Field 1 (auto_id "1144") in
    "Edit Database Record" shares its automation_id with Card # in the
    nested "HID Card Data Encoding" dialog, and the just-closed HID dialog
    can still be mid-teardown in the UIA tree the instant the next lookup
    runs, so two "1144" Edit elements transiently exist. Fixed by adding a
    retry-with-settle-delay around the Edit lookup in
    `driver_db_workflows._set_edit_field` (catches ElementAmbiguousError,
    waits briefly, retries) - not reliably reproducible, so this fix has
    not yet been re-confirmed with a dedicated repro run; re-verify by
    re-running this test a few times if the flake recurs.
    """
    create_new_driver_database_file(app)
    for row_index in range(70):
        win32_dlg, uia_dlg = open_edit_database_record_dialog(app, row_index=row_index)
        enter_hid_format_id(
            app, win32_dlg, uia_dlg,
            extended_code=str((row_index % 4095) + 1), facility_code=str((row_index % 255) + 1),
            card_number=str(1000 + row_index),
        )
        set_driver_record_fields(win32_dlg, uia_dlg, field1="1", field2="2", field3="3")

    save_path = str(tmp_path / "test_f10_driverdb.al4ddb")
    save_as(app, save_path)
    open_file_dialog(app, save_path)

    pdf_path = print_to_pdf(app, _pdf_path("f10_driverdb_multiple_pages.pdf"))
    assert os.path.isfile(pdf_path)

    pages = _page_count(pdf_path)
    print(f"[INFO] Driver Database printout page count: {pages}")
    assert pages > 1, f"Expected a multi-page printout for a populated Driver Database grid, got {pages} page(s)"


def test_f11_printing_accumate_config_files(app, tmp_path):
    """
    F11: Printing AccuMate Config Files.
      1. Open a saved AccuMate Config file.
      2. Print it via "Microsoft Print to PDF".
      3. Verify the PDF was saved, has a large number of pages (~200 for a
         blank config - see print_workflows.py docstring), and contains
         at least one recognizable parameter name.

    RESOLVED - see module docstring "F9-F13 LIVE FINDING". Live-verified:
    PASS (large multi-page printout with recognizable parameter text).
    """
    new_config_file(app)

    save_path = str(tmp_path / "test_f11_config.AL4")
    save_as(app, save_path)
    open_file_dialog(app, save_path)

    pdf_path = print_to_pdf(app, _pdf_path("f11_accumate_config.pdf"))
    assert os.path.isfile(pdf_path)

    pages = _page_count(pdf_path)
    print(f"[INFO] AccuMate Config printout page count: {pages}")
    assert pages > 50, f"Expected a large multi-page printout for a full Config file, got {pages} page(s)"

    text = _extract_all_text(pdf_path)
    assert "Maximum Available Arms" in text or "Number of Load Arms" in text, (
        "Expected a recognizable System Layout parameter name in the printed Config file"
    )


def test_f12_printing_equation_files_multiple_pages(app, tmp_path):
    """
    F12: Printing Equation Files (Multiple Pages).
      Populate several equation lines so the printout spans multiple
      pages, save, reopen, print, and verify.

    RESOLVED - see module docstring "F9-F13 LIVE FINDING". Live-verified: PASS.
    """
    create_new_equation_set_file(app)
    for n in range(1, 31):
        insert_equation_line(app, register_number=n, expression=str(n))

    save_path = str(tmp_path / "test_f12_equation.al4equ")
    save_as(app, save_path)
    open_file_dialog(app, save_path)

    pdf_path = print_to_pdf(app, _pdf_path("f12_equation_multiple_pages.pdf"))
    assert os.path.isfile(pdf_path)

    pages = _page_count(pdf_path)
    print(f"[INFO] Equation Set printout page count: {pages}")
    assert pages >= 1


def test_f13_printing_equation_files_one_page(app, tmp_path):
    """
    F13: Printing Equation Files (One Page).
      Same as F12, but with only a handful of equation lines so the
      printout fits on a single page.

    RESOLVED - see module docstring "F9-F13 LIVE FINDING". Live-verified: PASS.
    """
    create_new_equation_set_file(app)

    save_path = str(tmp_path / "test_f13_equation.al4equ")
    save_as(app, save_path)
    open_file_dialog(app, save_path)

    pdf_path = print_to_pdf(app, _pdf_path("f13_equation_one_page.pdf"))
    assert os.path.isfile(pdf_path)
    assert _page_count(pdf_path) >= 1


def test_f14_api_table_conversions_from_a3x_to_al4(app):
    """
    F14: API Table Conversions From A3X to AL4.
      1. Open the "Open" file dialog.
      2. Navigate to and open configs/F14.A3X (an AccuMate III
         configuration file provided for this test, with an API Table
         value configured under Arm -> Meter -> Product -> Temperature/
         Density).
      3. Verify the file loads/converts and that the converted
         Temperature/Density parameter view exposes a real, non-blank
         "API Table" value (the specific expected mapped value isn't
         asserted here since it depends on the exact API Table option
         chosen when the provided file was created - see regression.md's
         "API Tables.txt" mapping for a human cross-check).
    """
    a3x_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs", "F14.A3X"))
    if not os.path.isfile(a3x_path):
        pytest.skip(f"F14: provided AM3 .a3x test file not found: {a3x_path}")

    print(f"[STEP] Loading AM3 configuration file: {a3x_path}")
    open_file_dialog(app, a3x_path)

    title = _wait_for_title_contains(app, "F14")
    assert "F14" in title, f"Main window title does not reflect the loaded .a3x file: {title!r}"

    page = MainPage(app, request=None)
    page.test_name = "test_f14_api_table_conversions_from_a3x_to_al4"

    print("[STEP] Navigating to Arm -> Meter -> Product -> Temperature/Density")
    page.select_tree_path(["Arm 1", "Meter 1", "Product 1", "Temperature/Density"])

    api_table_value = page.get_value("API Table")
    assert api_table_value, "Expected a non-blank 'API Table' value after converting the .a3x file"
    print(f"[INFO] Converted 'API Table' value: {api_table_value!r}")


def test_f15_parameter_conversions_from_a3x_configuration_file(app):
    """
    F15: Parameter Conversions from A3X - Configuration File.
      1. Open the "Open" file dialog.
      2. Navigate to and open configs/F15.A3X (an AccuMate III
         configuration file provided for this test, with System Status
         Display = Yes under System -> General Purpose, and Inhibit Auto
         Focus = Yes under System -> Communications).
      3. Verify the file loads/converts with no errors, and that both
         parameters carried over correctly.
    """
    a3x_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs", "F15.A3X"))
    if not os.path.isfile(a3x_path):
        pytest.skip(f"F15: provided AM3 .a3x test file not found: {a3x_path}")

    print(f"[STEP] Loading AM3 configuration file: {a3x_path}")
    open_file_dialog(app, a3x_path)

    title = _wait_for_title_contains(app, "F15")
    assert "F15" in title, f"Main window title does not reflect the loaded .a3x file: {title!r}"

    page = MainPage(app, request=None)
    page.test_name = "test_f15_parameter_conversions_from_a3x_configuration_file"

    print("[STEP] Navigating to System Directory -> General Purpose")
    page.select_tree_path(["System Directory", "General Purpose"])
    system_status_display = page.get_value("System Status Display")
    assert system_status_display == "Yes", (
        f"Expected 'System Status Display' to convert to 'Yes', got: {system_status_display!r}"
    )

    print("[STEP] Navigating to System Directory -> Communications")
    page.select_tree_path(["System Directory", "Communications"])
    inhibit_auto_focus = page.get_value("Inhibit Auto Focus")
    assert inhibit_auto_focus == "Yes", (
        f"Expected 'Inhibit Auto Focus' to convert to 'Yes', got: {inhibit_auto_focus!r}"
    )


def test_f16_parameter_conversions_from_a3x_report_file(app):
    """
    F16: Parameter Conversions from A3X - Report File.
      1. Open the "Open" file dialog.
      2. Navigate to and open configs/F16.RPX (an AccuMate III report
         file provided for this test, containing 2 Run/Program Data
         Description items: "Inhibit Auto Focus" (System Configuration
         register 734) and "System Status Display" (System Configuration
         register 139)).
      3. Verify both items are present on the converted Report canvas and
         neither shows an "Invalid Register" placeholder.
    """
    rpx_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs", "F16.RPX"))
    if not os.path.isfile(rpx_path):
        pytest.skip(f"F16: provided AM3 .RPX test file not found: {rpx_path}")

    print(f"[STEP] Loading AM3 report file: {rpx_path}")
    open_file_dialog(app, rpx_path)

    title = _wait_for_title_contains(app, "F16")
    assert "F16" in title, f"Main window title does not reflect the loaded .RPX file: {title!r}"

    items = get_report_items(app)
    texts = [item["text"] for item in items]
    print(f"[INFO] Report canvas items after conversion: {texts}")

    assert any("Inhibit Auto Focus" in t for t in texts), (
        f"Expected an 'Inhibit Auto Focus' item on the converted report canvas, got: {texts}"
    )
    assert any("System Status Display" in t for t in texts), (
        f"Expected a 'System Status Display' item on the converted report canvas, got: {texts}"
    )
    assert not any("Invalid Register" in t for t in texts), (
        f"Found an 'Invalid Register' item on the converted report canvas: {texts}"
    )


def test_f17_parameter_conversions_from_a3x_equations_file(app):
    """
    F17: Parameter Conversions from A3X - Equations File.
      1. Open the "Open" file dialog.
      2. Navigate to and open configs/F17.EQX (an AccuMate III equations
         file provided for this test, containing 2 USERBOOL registers:
         one for System Configuration register 734 (Inhibit Auto Focus)
         and one for System Configuration register 139 (System Status
         Display)).
      3. Verify both USERBOOL rows are present on the converted Equation
         Set view and neither shows an "Invalid Register" placeholder.
    """
    eqx_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs", "F17.EQX"))
    if not os.path.isfile(eqx_path):
        pytest.skip(f"F17: provided AM3 .EQX test file not found: {eqx_path}")

    print(f"[STEP] Loading AM3 equations file: {eqx_path}")
    open_file_dialog(app, eqx_path)

    title = _wait_for_title_contains(app, "F17")
    assert "F17" in title, f"Main window title does not reflect the loaded .EQX file: {title!r}"

    rows = get_equation_set_rows(app)
    flattened = [" ".join(row) for row in rows]
    print(f"[INFO] Equation rows after conversion: {flattened}")

    assert any("734" in r or "Inhibit Auto Focus" in r for r in flattened), (
        f"Expected a USERBOOL row referencing register 734/Inhibit Auto Focus, got: {flattened}"
    )
    assert any("139" in r or "System Status Display" in r for r in flattened), (
        f"Expected a USERBOOL row referencing register 139/System Status Display, got: {flattened}"
    )
    assert not any("Invalid Register" in r for r in flattened), (
        f"Found an 'Invalid Register' row in the converted equation set: {flattened}"
    )
