"""
DRAFT / NOT YET LIVE-VERIFIED - scenarios/regression.md D1-D9 (Driver
Database Editor). Every test below is marked `needs_live_verification` (see
pytest.ini) and is excluded from the default `pytest -s -v` run - they were
scoped/drafted without any live AccuMate window interaction (see
workflows/driver_db_workflows.py's module docstring for the open questions
that must be resolved first), to avoid stealing screen focus during a
scoping-only pass.

Scope summary (see workflows/driver_db_workflows.py for full detail):
  - D1-D5: offline, app-only - the same class of test as H9, should become
    fully automatable once the open questions in driver_db_workflows.py are
    resolved (no device/external files needed).
  - D6-D8: additionally need a live, reachable AccuLoad device.
  - D9: additionally needs a provided AM3-format Database Driver File
    (.3DB) that does not currently exist in this repo/environment - same
    class of blocker as H3-H8's provided files.
"""

import pytest

from workflows.driver_db_workflows import (
    create_new_driver_database_file,
    get_driver_database_rows,
    open_edit_database_record_dialog,
    enter_hid_format_id,
    set_driver_record_fields,
)


@pytest.mark.needs_live_verification
def test_d1_create_new_driver_database_file(app):
    """
    D1: Create New Driver Database Files.
      1. Start the AccuMate Application.
      2. Hover 'New' under the Application Button -> 'Driver Database'
         option appears.
      3. Click 'Driver Database' -> a new, blank Driver Database view is
         displayed.
    """
    create_new_driver_database_file(app)
    rows = get_driver_database_rows(app)
    assert rows is not None


@pytest.mark.needs_live_verification
def test_d2_creating_driver_database_entries(app):
    """
    D2: Creating Driver Database Entries.
      1. Create a new Driver Database file.
      2. Double-click the topmost entry -> "Edit Database Record" dialog
         appears.
      3. Click "< Enter in HID Format..." -> a nested dialog for a
         formatted ID appears.
      4. Enter a valid ID and OK it -> "Edit Database Record" converts the
         formatted ID to a single number.
      5. OK the "Edit Database Record" dialog.
    """
    create_new_driver_database_file(app)
    dlg = open_edit_database_record_dialog(app, row_index=0)
    enter_hid_format_id(dlg, formatted_id="TODO-verify-live-valid-id-format")
    set_driver_record_fields(dlg)


@pytest.mark.needs_live_verification
def test_d3_editing_a_driver_database_entry(app):
    """
    D3: Editing a Driver Database Entry.
      1. Double-click the D2 entry -> dialog re-opens loaded with current
         values.
      2. Change Card Data via HID Format tool.
      3. Set PIN # = 777, Field 1/2/3 = 1/2/3. OK the dialog.
      4. Re-open the dialog -> values persisted correctly.
    """
    create_new_driver_database_file(app)
    dlg = open_edit_database_record_dialog(app, row_index=0)
    enter_hid_format_id(dlg, formatted_id="TODO-verify-live-valid-id-format")
    set_driver_record_fields(dlg, pin="777", field1="1", field2="2", field3="3")

    dlg2 = open_edit_database_record_dialog(app, row_index=0)
    assert dlg2 is not None


@pytest.mark.needs_live_verification
def test_d4_saving_driver_database_files(app, tmp_path):
    """
    D4: Saving Driver Database Files.
      1-4. Populate 3 rows via the "Edit Database Record" dialog (HID
           Format + Field 1-3 each time).
      5. Save via Application Button -> Save, with a valid filename ->
         file exists on disk afterward.
    """
    create_new_driver_database_file(app)
    for row_index in range(3):
        dlg = open_edit_database_record_dialog(app, row_index=row_index)
        enter_hid_format_id(dlg, formatted_id=f"TODO-verify-live-id-{row_index}")
        set_driver_record_fields(dlg, field1="1", field2="2", field3="3")

    save_path = tmp_path / "test_d4_driver_database.al4ddb"
    # TODO: verify live - reuse workflows.file_workflows.save_as() once
    # confirmed it works unchanged for non-Config document types.
    raise NotImplementedError("D4: save_as() not yet confirmed for Driver Database documents")


@pytest.mark.needs_live_verification
def test_d5_loading_driver_database_files(app, tmp_path):
    """
    D5: Loading Driver Database Files.
      1. From D4's still-open view, Save As... under a new name.
      2. Open the old file -> both old and new views open simultaneously.
      3. Verify both views' contents are identical.
    """
    pytest.skip("D5 depends on D4's save_as() support - see docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_d6_uploading_driver_database_files(app, device_ip):
    """
    D6: Uploading Driver Database Files (requires live AccuLoad device).
      Connect to the device, then Upload File to AccuLoad -> browse to a
      .al4ddb file -> upload completes successfully.
    """
    pytest.skip("D6: 'AccuMate File Transfer' upload workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_d7_downloading_driver_database_files(app, device_ip):
    """
    D7: Downloading Driver Database Files (requires live AccuLoad device).
      Connect to the device, Download File From AccuLoad -> Driver Database
      File -> compare against the device's own /ftp/driver.txt via
      SSH/checksum.
    """
    pytest.skip("D7: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_d8_no_driver_database_file_to_download(app, device_ip):
    """
    D8: No Driver Database File To Download (requires live AccuLoad
    device with no driver.txt present, e.g. after a Factory Init).
      Download File From AccuLoad -> Driver Database File -> a warning
      popup notifies the user there is nothing to pull.
    """
    pytest.skip("D8: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.needs_live_verification
def test_d9_loading_am3_driver_database_files(app):
    """
    D9: Loading AM3 Driver Database Files (needs a provided .3DB test
    file, not currently present in this repo/environment - same class of
    blocker as H3-H8's provided files).
    """
    pytest.skip("D9: requires a provided AM3 .3DB test file not present in this repo")
