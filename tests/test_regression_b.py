"""
scenarios/regression.md B1-B28 (Report Editor).

B1-B3 and B15-B16 are LIVE-VERIFIED (real workflow functions, real control
ids, real dialog titles - see workflows/report_workflows.py's module
docstring for the full findings) and run as part of the default
`pytest -s -v` suite.

Scope summary (see workflows/report_workflows.py for full detail):
  - B4-B14: need a live, reachable AccuLoad device AND a not-yet-built
    "AccuMate File Transfer" upload/download dialog workflow. B11/B12
    additionally need provided AM3 (.RPX)/early-AM4 report files not
    present in this repo/environment.
  - B17-B28: canvas-level interactions (item offsets, Advanced format
    dialog/validation, drag/drop moving, copy/paste, out-of-bounds,
    document size/page count) not yet probed/implemented - each is marked
    `needs_live_verification` below with a note on what's still unknown.
"""

import os

import pytest

from workflows.report_workflows import (
    create_new_report_file,
    get_report_items,
    insert_report_item,
    ITEM_TYPE_USER_TEXT,
    ITEM_TYPE_RUN_PROGRAM_DATA_VALUE,
    ITEM_TYPE_RUN_PROGRAM_DATA_DESCRIPTION,
)
from workflows.file_workflows import save_as, open_file_dialog


def test_b1_creating_new_report_files(app):
    """
    B1: Creating New Report Files.
      1. Start the AccuMate Application.
      2. Hover 'New' under the Application Button -> 'Report Configuration'
         option appears.
      3. Click 'Report Configuration' -> a new, blank Report Configuration
         view is displayed.
    """
    create_new_report_file(app)
    items = get_report_items(app)
    assert items == []


def test_b2_saving_report_files(app, tmp_path):
    """
    B2: Saving Report Files.
      1-2. Insert a "User-defined Text" item -> text appears on the report.
      3. Insert a "Run/Program Data Value" item pointed at "Load Arm
         Layout" -> "Number of Load Arms" -> displays the current value
         (confirmed live: "6", matching regression.md's implied sample
         data exactly).
      4. Insert a "Run/Program Data Description" item at the same data
         register -> displays "Number of Load Arms".
      5-6. Save via Application Button -> Save, with a valid filename ->
         file exists on disk afterward.
    """
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Hi There", line=1)
    insert_report_item(
        app, item_type=ITEM_TYPE_RUN_PROGRAM_DATA_VALUE, line=2,
        tree_path=["Load Arm Layout", "Number of Load Arms"],
    )
    insert_report_item(
        app, item_type=ITEM_TYPE_RUN_PROGRAM_DATA_DESCRIPTION, line=3,
        tree_path=["Load Arm Layout", "Number of Load Arms"],
    )

    items = get_report_items(app)
    texts = [i["text"] for i in items]
    assert texts == ["Hi There", "6", "Number of Load Arms"]

    save_path = str(tmp_path / "test_b2_report.al4rep")
    save_as(app, save_path)
    assert os.path.isfile(save_path)


def test_b3_loading_report_files(app, tmp_path):
    """
    B3: Loading Report Files.
      1. Save the Report view to disk.
      2. Open that same file back up -> the reopened view's contents match
         what was originally saved.

    NOTE: same scaled-back scope as test_regression_d.py's D5/
    test_regression_e.py's E3 - a second back-to-back Application Button
    "Save As..." on the same still-open document was not attempted here
    (see D5's docstring for the live finding that motivated this
    simplification); a single save + reopen + content-comparison still
    exercises the regression-relevant behavior (open_file_dialog/save_as
    compatible with Report Configuration documents, saved content
    round-trips correctly).
    """
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Round Trip", line=1)
    original_items = get_report_items(app)

    save_path = str(tmp_path / "test_b3_original.al4rep")
    save_as(app, save_path)

    open_file_dialog(app, save_path)
    reopened_items = get_report_items(app)
    assert reopened_items == original_items


def test_b15_creating_usertext_items(app):
    """
    B15: Creating UserText Items.
      1. Create a new Report Configuration.
      2. Insert a new item (regression.md uses right-click "Insert New
         Here..." on the canvas as the entry point; the ribbon "Insert"
         button used here opens the identical "Edit Report Item" dialog,
         confirmed live - see report_workflows.insert_report_item).
      3. Set Item Value to "Testing User Text" and OK -> the new item
         displays the chosen text.
    """
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Testing User Text")

    items = get_report_items(app)
    assert items[0]["text"] == "Testing User Text"


def test_b16_creating_value_description_items(app):
    """
    B16: Creating Value/Description Items.
      1-4. Create a new Report Configuration, insert an item.
      5. Change Item Type to "Run/Program Data Description".
      6. Set Data Register to "Load Arm Layout"->"Number of Load Arms" and
         OK -> the item displays "Number of Load Arms".
      7. Repeat one row beneath with Item Type "Run/Program Data Value" ->
         the item displays the number 6.
    """
    create_new_report_file(app)
    insert_report_item(
        app, item_type=ITEM_TYPE_RUN_PROGRAM_DATA_DESCRIPTION, line=1,
        tree_path=["Load Arm Layout", "Number of Load Arms"],
    )
    insert_report_item(
        app, item_type=ITEM_TYPE_RUN_PROGRAM_DATA_VALUE, line=2,
        tree_path=["Load Arm Layout", "Number of Load Arms"],
    )

    items = get_report_items(app)
    texts = [i["text"] for i in items]
    assert texts == ["Number of Load Arms", "6"]


@pytest.mark.needs_live_verification
def test_b17_creating_value_description_items_with_offsets(app):
    """
    B17: Creating Value/Description Items with Offsets.
      Uses the "Select Data Item" dialog's Offset 1/2/3 fields (auto_ids
      1006/1007/1021 - see report_workflows._select_data_item's docstring)
      against "Pulse Input Config"->"Pulse Input Tag" with offset 1, then
      14 (max). NOT YET IMPLEMENTED: _select_data_item doesn't currently
      set the Offset fields - needs live verification of which of the
      three Offset edits corresponds to regression.md's single "Offset"
      value and the resulting "Pulse Input Tag (N)" Data Register text.
    """
    pytest.skip("B17: Select Data Item dialog's Offset fields not yet wired into _select_data_item")


@pytest.mark.needs_live_verification
def test_b18_changing_the_format_of_report_items(app):
    """
    B18: Changing the Format of Report Items.
      Needs a live probe of the "Advanced..." button's (auto_id 1011)
      "Advanced Report Item Options" dialog - not yet done.
    """
    pytest.skip("B18: 'Advanced...' dialog controls not yet probed")


@pytest.mark.needs_live_verification
def test_b19_using_invalid_formats_for_string_report_items(app):
    """
    B19: Using Invalid Formats for String Report Items.
      Same "Advanced..." dialog dependency as B18, plus needs to confirm
      the validation-warning popup's title/text for an incompatible format
      (e.g. "%d" on a string value).
    """
    pytest.skip("B19: 'Advanced...' dialog controls not yet probed - see B18")


@pytest.mark.needs_live_verification
def test_b20_moving_items(app):
    """
    B20: Moving Items. Needs a live-verified drag-and-drop gesture on a
    report canvas Button-control item (not yet probed - may need the same
    kind of held-mouse-button approach used for the "New" fly-out, or a
    simpler click-drag since this isn't OS menu-tracking).
    """
    pytest.skip("B20: canvas drag-and-drop not yet probed")


@pytest.mark.needs_live_verification
def test_b21_moving_items_over_other_items(app):
    """B21: Moving Items over other Items. Same drag-and-drop dependency as B20."""
    pytest.skip("B21: canvas drag-and-drop not yet probed - see B20")


@pytest.mark.needs_live_verification
def test_b22_copy_paste_items(app):
    """
    B22: Copy/Paste Items. Needs a live probe of the canvas's right-click
    context menu (Copy/Paste Here) - likely a real (UIA-visible) win32
    context menu rather than the ribbon's custom-drawn backstage menu, but
    unconfirmed.
    """
    pytest.skip("B22: canvas right-click context menu (Copy/Paste) not yet probed")


@pytest.mark.needs_live_verification
def test_b23_copy_paste_text_as_an_item(app):
    """
    B23: Copy/Paste Text as an Item. Needs a live probe of pasting
    clipboard text directly onto the canvas (via win32 clipboard API plus
    the canvas's paste handling) - not yet attempted.
    """
    pytest.skip("B23: clipboard-to-canvas paste not yet probed")


@pytest.mark.needs_live_verification
def test_b24_creating_items_out_of_bounds(app):
    """
    B24: Creating Items Out of Bounds. Needs to confirm the exact
    out-of-bounds warning dialog's title/text when an over-long Item Value
    would exceed the canvas width.
    """
    pytest.skip("B24: out-of-bounds warning dialog not yet probed")


@pytest.mark.needs_live_verification
def test_b25_moving_items_out_of_bounds(app):
    """B25: Moving Items Out of Bounds. Same drag-and-drop dependency as B20."""
    pytest.skip("B25: canvas drag-and-drop not yet probed - see B20")


@pytest.mark.needs_live_verification
def test_b26_changing_document_size(app):
    """
    B26: Changing Document Size. Needs a live probe of the Report
    Configuration-specific "Document Options" dialog (distinct from the
    AccuMate Config File's IP-address Document Options already used
    elsewhere in this repo) - page size fields not yet confirmed.
    """
    pytest.skip("B26: Report Configuration's Document Options dialog not yet probed")


@pytest.mark.needs_live_verification
def test_b27_changing_document_size_items_out_of_bounds(app):
    """B27: Changing Document Size - Items Out of Bounds. Same Document Options dependency as B26."""
    pytest.skip("B27: Report Configuration's Document Options dialog not yet probed - see B26")


@pytest.mark.needs_live_verification
def test_b28_changing_number_of_pages_in_a_document(app):
    """B28: Changing Number of Pages in a Document. Same Document Options dependency as B26."""
    pytest.skip("B28: Report Configuration's Document Options dialog not yet probed - see B26")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b4_uploading_empty_report_file(app, device_ip):
    """B4: Uploading Empty Report File (requires live AccuLoad device)."""
    pytest.skip("B4: 'AccuMate File Transfer' upload workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b5_uploading_report_files_transaction_report(app, device_ip):
    """B5: Uploading Report Files - Transaction Report (requires live AccuLoad device)."""
    pytest.skip("B5: 'AccuMate File Transfer' upload workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b6_downloading_report_files_transaction_report(app, device_ip):
    """B6: Downloading Report Files - Transaction Report (requires live AccuLoad device)."""
    pytest.skip("B6: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b7_uploading_report_files_batch_report(app, device_ip):
    """B7: Uploading Report Files - Batch Report (requires live AccuLoad device)."""
    pytest.skip("B7: 'AccuMate File Transfer' upload workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b8_downloading_report_files_batch_report(app, device_ip):
    """B8: Downloading Report Files - Batch Report (requires live AccuLoad device)."""
    pytest.skip("B8: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b9_uploading_report_files_prove_report(app, device_ip):
    """B9: Uploading Report Files - Prove Report (requires live AccuLoad device)."""
    pytest.skip("B9: 'AccuMate File Transfer' upload workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b10_downloading_report_files_prove_report(app, device_ip):
    """B10: Downloading Report Files - Prove Report (requires live AccuLoad device)."""
    pytest.skip("B10: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.needs_live_verification
def test_b11_loading_am3_report_files(app):
    """
    B11: Loading AM3 Report Files (needs a provided .RPX test file, not
    currently present in this repo/environment - same class of blocker as
    H3-H8's provided files).
    """
    pytest.skip("B11: requires a provided AM3 .RPX test file not present in this repo")


@pytest.mark.needs_live_verification
def test_b12_loading_early_am4_report_files(app):
    """
    B12: Loading Early AM4 Report Files (needs a provided early-AM4-format
    report file with <none> Alarm entries, not currently present in this
    repo/environment).
    """
    pytest.skip("B12: requires a provided early-AM4-format report file not present in this repo")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b13_upload_download_multiple_times(app, device_ip):
    """B13: Upload/Download Multiple Times (requires live AccuLoad device)."""
    pytest.skip("B13: 'AccuMate File Transfer' upload/download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b14_no_report_to_download(app, device_ip):
    """
    B14: No Report To Download (requires live AccuLoad device with all
    *.CFG files removed from /media/data/database).
    """
    pytest.skip("B14: 'AccuMate File Transfer' download workflow not yet built - see module docstring")
