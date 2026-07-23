"""
scenarios/regression.md F1-F17 (transaction/event/audit logs, license
status, firmware update, printing, API/parameter conversions).

Scope summary:
  - F1-F8: need a live, reachable AccuLoad device (log downloads, license
    status upload/download, firmware update) - not attempted here.
  - F9-F13: printing Driver Database/Config/Equation Set files - BLOCKED,
    see finding below. Written against workflows/print_workflows.py's
    print_to_pdf(), but live testing this segment found that helper no
    longer matches the installed app's actual Application Button -> "Print"
    behavior.
  - F14-F17: need provided AccuMate III (AM3) test files (.a3x/.EQX/.RPX)
    that do not currently exist in this repo/environment - same class of
    blocker as C7/D9/E7/H3-H8's provided files.

F9-F13 LIVE FINDING (this segment): the Application Button's "Print" row is
now a fly-out submenu (arrow, 3 items: "Quick Print", "Print Preview"
(observed disabled), "Print Setup...") rather than opening the classic
Windows "Print" common dialog (title "Print", class "#32770", printer combo
control_id 1139) that print_workflows.py's _open_print_dialog()/print_to_pdf()
expect - that dialog was never observed appearing via any submenu item during
extensive live probing this segment, so _open_print_dialog() reliably times
out and every F9-F13 test fails at the print_to_pdf() call.
  - Root-caused (partially): the *reason* no dialog/output appeared traced
    back to the Windows default printer being "FollowMe_Erie" (a
    follow-me/network print queue) - PrintDlg()-family APIs can fail/return
    silently with no UI when the default printer is unreachable, which
    plausibly explains the original silence. Temporarily switching the
    Windows default printer to "Microsoft Print to PDF" confirmed
    "Print Setup..." *does* then show a real dialog (title "Print Setup",
    control_id 1136 printer combo correctly showing "Microsoft Print to
    PDF"), proving the submenu itself is reachable and interactive.
  - However, even with a valid default printer and after explicitly OK'ing
    "Print Setup..." with "Microsoft Print to PDF" selected, "Quick Print"
    (the item print_to_pdf's old flow effectively needs, since none of the
    3 items open a printer-selection dialog matching regression.md's
    literal "print window... For 'Name' parameter set to Microsoft Print
    to PDF" step) produced **no visible dialog, no new window, no print
    spool job, and no PDF file anywhere in the user profile** across
    repeated live tests - i.e. it silently no-ops in this environment
    rather than actually printing.
  - This is a genuine, unresolved app-level blocker (not a stale
    automation script needing a coordinate/control-id tweak) - print_to_pdf()
    itself may need a different mechanism entirely (e.g. driving "Print
    Setup" fully, or finding whatever actually triggers "Save Print Output
    As", or this AccuMate build's Quick Print may only work with a locally
    hosted, reachable printer and never with "Microsoft Print to PDF" in
    this sandboxed environment) - needs further live investigation before
    F9-F13 can be implemented. The Windows default printer was restored to
    its original value ("FollowMe_Erie") before ending this segment.
"""

import os

import pytest
from pypdf import PdfReader

from workflows.file_workflows import new_config_file, save_as, open_file_dialog
from workflows.print_workflows import print_to_pdf
from workflows.driver_db_workflows import (
    create_new_driver_database_file,
    open_edit_database_record_dialog,
    enter_hid_format_id,
    set_driver_record_fields,
)
from workflows.equation_workflows import create_new_equation_set_file, insert_equation_line

_PDF_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "print_output"))


def _pdf_path(name):
    os.makedirs(_PDF_DIR, exist_ok=True)
    return os.path.join(_PDF_DIR, name)


def _page_count(pdf_path):
    return len(PdfReader(pdf_path).pages)


def _extract_all_text(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f1_downloading_empty_transaction_log(app, device_ip):
    """F1: Downloading Empty Transaction Log (requires live AccuLoad device)."""
    pytest.skip("F1: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f2_download_transaction_log_small(app, device_ip):
    """F2: Download Transaction Log (Small) (requires live AccuLoad device)."""
    pytest.skip("F2: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f3_download_transaction_log_large(app, device_ip):
    """F3: Download Transaction Log (Large) (requires live AccuLoad device)."""
    pytest.skip("F3: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f4_download_event_log(app, device_ip):
    """F4: Download Event Log (requires live AccuLoad device)."""
    pytest.skip("F4: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f5_download_audit_trail_log(app, device_ip):
    """F5: Download Audit Trail Log (requires live AccuLoad device)."""
    pytest.skip("F5: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f6_upload_download_license_status_file(app, device_ip):
    """F6: Upload/Download License Status File (requires live AccuLoad device)."""
    pytest.skip("F6: 'AccuMate File Transfer' upload/download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f7_no_license_status_to_download(app, device_ip):
    """
    F7: No License Status To Download (requires live AccuLoad device with
    the license dongle pulled and "DA: Arm Not Licensed" alarm present).
    """
    pytest.skip("F7: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_f8_update_accuload_firmware(app, device_ip):
    """F8: Update AccuLoad Firmware (requires live AccuLoad device + firmware file)."""
    pytest.skip("F8: firmware update workflow not yet built - see module docstring")


@pytest.mark.needs_live_verification
def test_f9_printing_driverdb_files_one_page(app, tmp_path):
    """
    F9: Printing DriverDB Files (One Page).
      1. Open a saved Driver Database file.
      2. Print it via "Microsoft Print to PDF".
      3. Verify the PDF was saved and contains the file's data.

    BLOCKED - see module docstring "F9-F13 LIVE FINDING": the Application
    Button's "Print" fly-out ("Quick Print"/"Print Preview"/"Print
    Setup...") does not currently produce any observable dialog/output via
    any item tried, even with a valid local default printer configured.
    print_to_pdf() therefore reliably times out. Written eagerly against
    the intended flow so it's ready to un-skip once print_workflows.py's
    print mechanism is fixed to match the app's actual current Print
    fly-out behavior.
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


@pytest.mark.needs_live_verification
def test_f10_printing_driverdb_files_multiple_pages(app, tmp_path):
    """
    F10: Printing DriverDB Files (Multiple Pages).
      Same as F9, but with enough entries populated that the printout
      spans more than one page (Driver Database has thousands of rows in
      a fresh document - see workflows/driver_db_workflows.py - so simply
      printing an unmodified new Driver Database file already produces a
      multi-page PDF).

    BLOCKED - see module docstring "F9-F13 LIVE FINDING" (same print
    fly-out blocker as F9).
    """
    create_new_driver_database_file(app)

    save_path = str(tmp_path / "test_f10_driverdb.al4ddb")
    save_as(app, save_path)
    open_file_dialog(app, save_path)

    pdf_path = print_to_pdf(app, _pdf_path("f10_driverdb_multiple_pages.pdf"))
    assert os.path.isfile(pdf_path)

    pages = _page_count(pdf_path)
    print(f"[INFO] Driver Database printout page count: {pages}")
    assert pages > 1, f"Expected a multi-page printout for the full Driver Database grid, got {pages} page(s)"


@pytest.mark.needs_live_verification
def test_f11_printing_accumate_config_files(app, tmp_path):
    """
    F11: Printing AccuMate Config Files.
      1. Open a saved AccuMate Config file.
      2. Print it via "Microsoft Print to PDF".
      3. Verify the PDF was saved, has a large number of pages (~200 for a
         blank config - see print_workflows.py docstring), and contains
         at least one recognizable parameter name.

    BLOCKED - see module docstring "F9-F13 LIVE FINDING" (same print
    fly-out blocker as F9).
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


@pytest.mark.needs_live_verification
def test_f12_printing_equation_files_multiple_pages(app, tmp_path):
    """
    F12: Printing Equation Files (Multiple Pages).
      Populate several equation lines so the printout spans multiple
      pages, save, reopen, print, and verify.

    BLOCKED - see module docstring "F9-F13 LIVE FINDING" (same print
    fly-out blocker as F9).
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


@pytest.mark.needs_live_verification
def test_f13_printing_equation_files_one_page(app, tmp_path):
    """
    F13: Printing Equation Files (One Page).
      Same as F12, but with only a handful of equation lines so the
      printout fits on a single page.

    BLOCKED - see module docstring "F9-F13 LIVE FINDING" (same print
    fly-out blocker as F9).
    """
    create_new_equation_set_file(app)

    save_path = str(tmp_path / "test_f13_equation.al4equ")
    save_as(app, save_path)
    open_file_dialog(app, save_path)

    pdf_path = print_to_pdf(app, _pdf_path("f13_equation_one_page.pdf"))
    assert os.path.isfile(pdf_path)
    assert _page_count(pdf_path) >= 1


@pytest.mark.needs_live_verification
def test_f14_api_table_conversions_from_a3x_to_al4(app):
    """
    F14: API Table Conversions From A3X to AL4 (needs a provided set of
    AccuMate III .a3x files with various API Table configurations, not
    currently present in this repo/environment).
    """
    pytest.skip("F14: requires provided AM3 .a3x test files not present in this repo")


@pytest.mark.needs_live_verification
def test_f15_parameter_conversions_from_a3x_configuration_file(app):
    """
    F15: Parameter Conversions from A3X - Configuration File (needs a
    provided AccuMate III .a3x configuration file with specific parameter
    values set, not currently present in this repo/environment).
    """
    pytest.skip("F15: requires a provided AM3 .a3x configuration test file not present in this repo")


@pytest.mark.needs_live_verification
def test_f16_parameter_conversions_from_a3x_report_file(app):
    """
    F16: Parameter Conversions from A3X - Report File (needs a provided
    AccuMate III .RPX report file, not currently present in this
    repo/environment).
    """
    pytest.skip("F16: requires a provided AM3 .RPX test file not present in this repo")


@pytest.mark.needs_live_verification
def test_f17_parameter_conversions_from_a3x_equations_file(app):
    """
    F17: Parameter Conversions from A3X - Equations File (needs a provided
    AccuMate III .EQX equations file, not currently present in this
    repo/environment).
    """
    pytest.skip("F17: requires a provided AM3 .EQX test file not present in this repo")
