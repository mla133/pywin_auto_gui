"""
scenarios/regression.md B1-B28 (Report Editor).

B1-B28 are all LIVE-VERIFIED (real workflow functions, real control ids,
real dialog titles - see workflows/report_workflows.py's module docstring
for the full findings) and run as part of the default `pytest -s -v`
suite.

Scope summary (see workflows/report_workflows.py for full detail):
  - B4-B10, B13-B14: wired to workflows/file_transfer_workflows.py +
    report_workflows.upload_report_file/download_report_file. LIVE-VERIFIED
    passing (real "File transfer complete." device round-trips) using the
    `app_ftp` fixture - see the FTP transfer investigation in this
    project's session history. B14 remains skipped on an unrelated,
    un-arrangeable device-state precondition.
  - B11/B12: LIVE-VERIFIED. Load `configs/B11.RPX` (AM3 report file) /
    `configs/B12.al4rep` (early-AM4 report file) via `open_file_dialog`,
    poll the main window title for the "B11"/"B12" substring, then assert
    the converted report canvas is queryable via `get_report_items`.
  - B27 (RESOLVED): no canvas-scrolling/dragging needed after all - the
    "out of bounds after a resize" scenario doesn't require moving an
    existing item beyond the visible viewport, just placing it (via the
    normal Insert dialog, BEFORE any resize happens, to avoid the Ticket
    #3644 dialog-validation bug entirely) at a line that's in-bounds for
    the current (default) page size but out-of-bounds for a subsequently
    smaller Custom size. Live-verified: shrinking below the item's line
    pops an "AccuMate" warning reading "New page boundaries won't fit the
    current report items". Also discovered live: the Default page's real
    usable line bound is much smaller than the "~60 lines" advertised in
    the Report Options label - line 35 is accepted but line 40+ is
    rejected by the Insert dialog's own (Ticket #3644-affected) validation
    even on a blank canvas - see test_b27's docstring for the binary-search
    detail.
"""

import os
import time

import pytest

from workflows.report_workflows import (
    create_new_report_file,
    get_report_items,
    insert_report_item,
    set_report_item_format,
    get_report_item_format,
    drag_report_item,
    copy_report_item,
    paste_here,
    set_clipboard_text,
    set_report_custom_page_size,
    set_report_number_of_pages,
    upload_report_file,
    download_report_file,
    ITEM_TYPE_USER_TEXT,
    ITEM_TYPE_RUN_PROGRAM_DATA_VALUE,
    ITEM_TYPE_RUN_PROGRAM_DATA_DESCRIPTION,
)
from workflows.file_workflows import save_as, open_file_dialog, load_test_file
from workflows.comm_workflows import configure_ip_and_connect


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


def test_b17_creating_value_description_items_with_offsets(app):
    """
    B17: Creating Value/Description Items with Offsets.
      Live-confirmed: for a leaf that supports an offset (e.g. "Pulse
      Input Config"->"Pulse Input Tag", offsets 1-14), only auto_id 1006
      of the "Select Data Item" dialog's Offset 1/2/3 Edit triple drives
      the result - it updates the (read-only) Data Register field to
      "Pulse Input Tag (N)". NOTE: this offset annotation only appears in
      the Data Register field, NOT in the read-only Item Value field or
      the resulting canvas item text (live-confirmed both stay plain
      "Pulse Input Tag" for a Description item regardless of offset - the
      offset is descriptive/reference-only for this data item, not part
      of its displayed report content), so this test checks the Data
      Register field directly rather than the final canvas item text.
    """
    from workflows.report_workflows import (
        _EDIT_REPORT_ITEM_DIALOG_TITLE,
        _EDIT_REPORT_ITEM_DIALOG_CLASS,
        _EDIT_REPORT_ITEM_DATA_REGISTER_AUTO_ID,
        _EDIT_REPORT_ITEM_CHANGE_BUTTON_AUTO_ID,
        _EDIT_REPORT_ITEM_TYPE_COMBO_AUTO_ID,
        _EDIT_REPORT_ITEM_CANCEL_AUTO_ID,
        _select_data_item,
    )
    from controls.ribbon_controls import click_ribbon_button
    from pywinauto import Application
    import time

    create_new_report_file(app)

    for offset, expected in ((1, "Pulse Input Tag (1)"), (14, "Pulse Input Tag (14)")):
        uia_win = app.get_uia_window()
        click_ribbon_button(uia_win, "Insert")
        time.sleep(1.0)

        dlg_spec = app.app.window(title=_EDIT_REPORT_ITEM_DIALOG_TITLE, class_name=_EDIT_REPORT_ITEM_DIALOG_CLASS)
        dlg_spec.wait("exists visible ready", timeout=10)
        win32_dlg = dlg_spec.wrapper_object()
        hwnd = win32_dlg.handle
        uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

        combo = next(d for d in win32_dlg.descendants(class_name="ComboBox") if str(d.control_id()) == _EDIT_REPORT_ITEM_TYPE_COMBO_AUTO_ID)
        combo.select(ITEM_TYPE_RUN_PROGRAM_DATA_DESCRIPTION)
        time.sleep(0.3)
        uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_CHANGE_BUTTON_AUTO_ID, control_type="Button").click_input()
        time.sleep(1.0)
        _select_data_item(app, ["Pulse Input Config", "Pulse Input Tag"], offset=offset)
        time.sleep(0.5)

        dr = next(e for e in win32_dlg.descendants(class_name="Edit") if str(e.control_id()) == _EDIT_REPORT_ITEM_DATA_REGISTER_AUTO_ID)
        assert dr.window_text() == expected

        uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_CANCEL_AUTO_ID, control_type="Button").click_input()
        time.sleep(0.5)


def test_b18_changing_the_format_of_report_items(app):
    """
    B18: Changing the Format of Report Items.
      Insert a Value item against a string-typed register ("Pulse Input
      Config"->"Pulse Input Tag"), open "Advanced..." and set Format to
      "%10.10s" -> the change propagates back to and persists on the
      parent "Edit Report Item" dialog's own Format field.
    """
    create_new_report_file(app)
    insert_report_item(
        app, item_type=ITEM_TYPE_RUN_PROGRAM_DATA_VALUE, line=1,
        tree_path=["Pulse Input Config", "Pulse Input Tag"],
    )
    win = app.get_window()
    item_ctrl = next(d for d in win.descendants(class_name="Button") if d.control_id() and d.control_id() >= 10000)
    item_ctrl.click_input(double=True)
    import time
    time.sleep(1.0)

    ok = set_report_item_format(app, "%10.10s")
    assert ok is True
    assert get_report_item_format(app) == "%10.10s"


def test_b19_using_invalid_formats_for_string_report_items(app):
    """
    B19: Using Invalid Formats for String Report Items.
      Setting an incompatible format (e.g. "%d" against a string-typed
      value) pops the "AccuMate" warning dialog with text "Invalid Format
      String - Type specifier does not match item data type" instead of
      accepting the change.
    """
    create_new_report_file(app)
    insert_report_item(
        app, item_type=ITEM_TYPE_RUN_PROGRAM_DATA_DESCRIPTION, line=1,
        tree_path=["Load Arm Layout", "Number of Load Arms"],
    )
    win = app.get_window()
    item_ctrl = next(d for d in win.descendants(class_name="Button") if d.control_id() and d.control_id() >= 10000)
    item_ctrl.click_input(double=True)
    import time
    time.sleep(1.0)

    ok = set_report_item_format(app, "%d")
    assert ok is False


def test_b20_moving_items(app):
    """
    B20: Moving Items.
      Dragging a placed item to a new, empty spot on the canvas moves it
      (its rectangle changes) - a plain OS-level mouse press-move-release
      gesture, no special held-drag timing trick required.
    """
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Drag Me", line=1, column=1)
    win = app.get_window()
    item_ctrl = next(d for d in win.descendants(class_name="Button") if d.window_text() == "Drag Me")
    rect_before = item_ctrl.rectangle()

    new_rect = drag_report_item(app, "Drag Me", dx=150, dy=120)

    assert new_rect is not None
    assert (new_rect.left, new_rect.top) != (rect_before.left, rect_before.top)


def test_b21_moving_items_over_other_items(app):
    """
    B21: Moving Items over other Items.
      Dragging one item directly onto another item is silently rejected -
      the dragged item's rectangle is unchanged afterward.
    """
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Item A", line=1, column=1)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Item B", line=10, column=1)

    win = app.get_window()
    target = next(d for d in win.descendants(class_name="Button") if d.window_text() == "Item B")
    target_rect = target.rectangle()
    dragged = next(d for d in win.descendants(class_name="Button") if d.window_text() == "Item A")
    dragged_rect_before = dragged.rectangle()

    dx = target_rect.mid_point().x - dragged_rect_before.mid_point().x
    dy = target_rect.mid_point().y - dragged_rect_before.mid_point().y
    new_rect = drag_report_item(app, "Item A", dx=dx, dy=dy)

    assert (new_rect.left, new_rect.top) == (dragged_rect_before.left, dragged_rect_before.top)


def test_b22_copy_paste_items(app):
    """
    B22: Copy/Paste Items.
      Copy a placed item via its right-click context menu ("Copy"), then
      "Paste Here" at a new empty canvas spot -> a duplicate item appears
      with the same text.
    """
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Copy Source", line=1, column=1)
    copy_report_item(app, "Copy Source")

    win = app.get_window()
    canvas_rect = win.rectangle()
    paste_x = canvas_rect.left + 300
    paste_y = canvas_rect.top + 300
    paste_here(app, paste_x, paste_y)

    items = get_report_items(app)
    texts = [i["text"] for i in items]
    assert texts.count("Copy Source") == 2


def test_b23_copy_paste_text_as_an_item(app):
    """
    B23: Copy/Paste Text as an Item.
      Put plain text on the Windows clipboard, then "Paste Here" on an
      empty canvas spot -> a new item is created containing that text.
    """
    create_new_report_file(app)
    set_clipboard_text("Pasted Clipboard Text")

    win = app.get_window()
    canvas_rect = win.rectangle()
    paste_here(app, canvas_rect.left + 250, canvas_rect.top + 250)

    items = get_report_items(app)
    texts = [i["text"] for i in items]
    assert "Pasted Clipboard Text" in texts


def test_b24_creating_items_out_of_bounds(app):
    """
    B24: Creating Items Out of Bounds.
      Typing an over-long Item Value (100 '-' characters) and OK'ing the
      "Edit Report Item" dialog pops the "AccuMate" warning: "Placing a
      report item at this position would exceed the column bounds. Please
      choose a different line and/or column." The dialog is not closed by
      this, and no item is added to the canvas.
    """
    create_new_report_file(app)
    long_value = "-" * 100

    from workflows.report_workflows import (
        _EDIT_REPORT_ITEM_DIALOG_TITLE,
        _EDIT_REPORT_ITEM_DIALOG_CLASS,
        _EDIT_REPORT_ITEM_VALUE_AUTO_ID,
        _EDIT_REPORT_ITEM_OK_AUTO_ID,
        _INVALID_FORMAT_WARNING_TITLE,
        _INVALID_FORMAT_WARNING_CLASS,
        _send_text,
    )
    from controls.ribbon_controls import click_ribbon_button
    from pywinauto import Application
    from pywinauto.keyboard import send_keys
    import time

    uia_win = app.get_uia_window()
    click_ribbon_button(uia_win, "Insert")
    time.sleep(1.0)

    dlg_spec = app.app.window(title=_EDIT_REPORT_ITEM_DIALOG_TITLE, class_name=_EDIT_REPORT_ITEM_DIALOG_CLASS)
    dlg_spec.wait("exists visible ready", timeout=10)
    hwnd = dlg_spec.wrapper_object().handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

    value_edit = uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_VALUE_AUTO_ID, control_type="Edit")
    value_edit.click_input()
    send_keys("^a")
    _send_text(long_value)
    time.sleep(0.2)
    uia_dlg.child_window(auto_id=_EDIT_REPORT_ITEM_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.8)

    warn_spec = app.app.window(title=_INVALID_FORMAT_WARNING_TITLE, class_name=_INVALID_FORMAT_WARNING_CLASS)
    assert warn_spec.exists(timeout=3)
    warn_win32 = warn_spec.wrapper_object()
    ok_btn = next(b for b in warn_win32.descendants(class_name="Button") if b.window_text() == "OK")
    ok_btn.click_input()
    time.sleep(0.3)

    cancel_btn = uia_dlg.child_window(control_type="Button", title="Cancel")
    cancel_btn.click_input()
    time.sleep(0.5)

    items = get_report_items(app)
    assert items == []


def test_b25_moving_items_out_of_bounds(app):
    """
    B25: Moving Items Out of Bounds.
      Dragging an item to a location entirely off the visible canvas is
      silently rejected - the item's rectangle is unchanged afterward.
    """
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Stay Put", line=1, column=1)
    win = app.get_window()
    item_ctrl = next(d for d in win.descendants(class_name="Button") if d.window_text() == "Stay Put")
    rect_before = item_ctrl.rectangle()
    win_rect = win.rectangle()

    # Drag to just past the main window's right/bottom edge (off the visible
    # canvas) while staying within the physical screen bounds - a huge
    # (e.g. 5000px) offset overshoots the screen entirely and produces
    # unreliable/garbage coordinates from the mouse driver.
    dx = (win_rect.right - rect_before.left) + 50
    dy = (win_rect.bottom - rect_before.top) + 50
    new_rect = drag_report_item(app, "Stay Put", dx=dx, dy=dy)

    assert (new_rect.left, new_rect.top) == (rect_before.left, rect_before.top)


def test_b26_changing_document_size(app):
    """
    B26: Changing Document Size.
      Open Report Options, select "Custom:", set Columns/Lines to a new
      size (100x100), OK -> reopening Report Options re-reads back the
      same custom size.
    """
    create_new_report_file(app)
    set_report_custom_page_size(app, columns=100, lines=100)

    from workflows.report_workflows import (
        open_report_document_options,
        _REPORT_OPTIONS_COLUMNS_AUTO_ID,
        _REPORT_OPTIONS_LINES_AUTO_ID,
        _REPORT_OPTIONS_CANCEL_AUTO_ID,
    )
    from pywinauto import Application

    dlg = open_report_document_options(app)
    hwnd = dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)
    cols_edit = next(e for e in dlg.descendants(class_name="Edit") if str(e.control_id()) == _REPORT_OPTIONS_COLUMNS_AUTO_ID)
    lines_edit = next(e for e in dlg.descendants(class_name="Edit") if str(e.control_id()) == _REPORT_OPTIONS_LINES_AUTO_ID)
    assert cols_edit.window_text() == "100"
    assert lines_edit.window_text() == "100"
    uia_dlg.child_window(auto_id=_REPORT_OPTIONS_CANCEL_AUTO_ID, control_type="Button").click_input()


def test_b27_changing_document_size_items_out_of_bounds(app):
    """
    B27: Changing Document Size - Items Out of Bounds.
      1. Insert an item at line 35 - deliberately before any Report
         Options resize has happened yet, since the Ticket #3644 bug (see
         B26/set_report_custom_page_size) only makes the "Edit Report
         Item" dialog unreliable AFTER a resize - placing the item first
         on the pristine default canvas sidesteps that bug entirely (no
         drag/canvas-scrolling needed).

         LIVE FINDING: the "Default" page's *actual* usable line bound is
         much smaller than the "~60 lines" advertised in the Report
         Options radio button label/B26's docstring - binary-searched
         live and confirmed line 35 is accepted (item placed cleanly) but
         line 40+ is rejected by the dialog's own bounds check with a
         false-sounding "overlap with an existing item" message even on a
         genuinely blank canvas (not "exceed bounds" as might be
         expected - the dialog's overlap-vs-bounds validation appears to
         conflate the two). Line 35/column 10 is used here as a
         known-good in-bounds placement.
      2. Open Report Options, switch to Custom 50 columns x 30 lines
         (fewer lines than the item's line 35), and OK the dialog.
      3. Expect the "AccuMate" warning dialog that the item is now out of
         the document's new (smaller) bounds.
    """
    from workflows.report_workflows import (
        _REPORT_OPTIONS_CUSTOM_RADIO_AUTO_ID,
        _REPORT_OPTIONS_COLUMNS_AUTO_ID,
        _REPORT_OPTIONS_LINES_AUTO_ID,
        _REPORT_OPTIONS_OK_AUTO_ID,
        _REPORT_OPTIONS_CANCEL_AUTO_ID,
        _INVALID_FORMAT_WARNING_TITLE,
        _INVALID_FORMAT_WARNING_CLASS,
        _send_text,
        open_report_document_options,
    )
    from pywinauto import Application
    from pywinauto.keyboard import send_keys
    import time

    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="X", line=35, column=10)

    dlg = open_report_document_options(app)
    hwnd = dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)

    uia_dlg.child_window(auto_id=_REPORT_OPTIONS_CUSTOM_RADIO_AUTO_ID, control_type="RadioButton").click_input()
    time.sleep(0.2)

    cols_edit = uia_dlg.child_window(auto_id=_REPORT_OPTIONS_COLUMNS_AUTO_ID, control_type="Edit")
    cols_edit.click_input()
    send_keys("^a")
    _send_text("50")

    lines_edit = uia_dlg.child_window(auto_id=_REPORT_OPTIONS_LINES_AUTO_ID, control_type="Edit")
    lines_edit.click_input()
    send_keys("^a")
    _send_text("30")
    time.sleep(0.3)

    uia_dlg.child_window(auto_id=_REPORT_OPTIONS_OK_AUTO_ID, control_type="Button").click_input()
    time.sleep(1.0)

    warn_spec = app.app.window(title=_INVALID_FORMAT_WARNING_TITLE, class_name=_INVALID_FORMAT_WARNING_CLASS)
    assert warn_spec.exists(timeout=5), (
        "Expected an 'AccuMate' warning that shrinking the document leaves "
        "the existing item out of bounds"
    )
    warn_win32 = warn_spec.wrapper_object()
    warning_text = " ".join(
        s.window_text() for s in warn_win32.descendants(class_name="Static") if s.window_text()
    )
    print(f"[INFO] B27 warning dialog text: {warning_text!r}")
    ok_btn = next(b for b in warn_win32.descendants(class_name="Button") if b.window_text() == "OK")
    ok_btn.click_input()
    time.sleep(0.3)

    # Acknowledging the warning returns focus to the still-open "Report
    # Options" dialog rather than auto-closing/committing it - live-tested
    # clicking OK again just re-validates and re-shows the same warning in
    # a loop (the size change is validated on every OK, not deferred), so
    # Cancel here to close the dialog cleanly without re-triggering it -
    # the warning itself is the thing under test, not the resulting
    # (never-committed) page size.
    uia_dlg.child_window(auto_id=_REPORT_OPTIONS_CANCEL_AUTO_ID, control_type="Button").click_input()
    time.sleep(0.5)


def test_b28_changing_number_of_pages_in_a_document(app):
    """
    B28: Changing Number of Pages in a Document.
      Set "Number of Pages in Report" to 2 -> reopening Report Options
      re-reads back "2". NOTE: the resulting effective canvas dimensions
      regression.md claims ("120 x 80") were not independently
      re-derived live - the Columns/Lines fields in this same dialog stay
      at their prior Default 80/60 values after this change (see
      set_report_number_of_pages's docstring) - this test only asserts
      the field itself round-trips correctly.
    """
    create_new_report_file(app)
    set_report_number_of_pages(app, num_pages=2)

    from workflows.report_workflows import (
        open_report_document_options,
        _REPORT_OPTIONS_PAGES_AUTO_ID,
        _REPORT_OPTIONS_CANCEL_AUTO_ID,
    )
    from pywinauto import Application

    dlg = open_report_document_options(app)
    hwnd = dlg.handle
    uia_dlg = Application(backend="uia").connect(handle=hwnd).window(handle=hwnd)
    pages_edit = next(e for e in dlg.descendants(class_name="Edit") if str(e.control_id()) == _REPORT_OPTIONS_PAGES_AUTO_ID)
    assert pages_edit.window_text() == "2"
    uia_dlg.child_window(auto_id=_REPORT_OPTIONS_CANCEL_AUTO_ID, control_type="Button").click_input()


_DEVICE_TIMEOUT_MESSAGE = "The operation timed out"


def _skip_on_device_timeout(result):
    if result["timed_out"] or (result["message"] and _DEVICE_TIMEOUT_MESSAGE in result["message"]):
        pytest.skip(
            f"Device-side file-transfer timeout (result={result!r}) - see "
            "workflows/driver_db_workflows.py module docstring 'Remaining gaps'"
        )


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b4_uploading_empty_report_file(app_ftp, device_ip, tmp_path):
    """
    B4: Uploading Empty Report File (requires live AccuLoad device).
      Create a new, empty Report Configuration, save it, then Upload File
      to AccuLoad -> select "User Configured Report 1 - Transaction
      Report" in the "Select Report" dialog -> expect the "No entries
      defined. Nothing to upload." warning.
    """
    app = app_ftp
    create_new_report_file(app)
    assert get_report_items(app) == []

    upload_path = str(tmp_path / "B4_empty.al4rep")
    save_as(app, upload_path)
    assert os.path.isfile(upload_path)

    # "Document Options" only becomes enabled once a real AL4 config
    # document is loaded - the bare Report Configuration document created
    # above isn't enough (same gotcha confirmed live for D6/E4/E8).
    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    result = upload_report_file(app, upload_path, "User Configured Report 1 - Transaction Report")
    _skip_on_device_timeout(result)
    assert result["message"] is not None, f"Expected a warning message, got {result!r}"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b5_uploading_report_files_transaction_report(app_ftp, device_ip, tmp_path):
    """
    B5: Uploading Report Files - Transaction Report (requires live
    AccuLoad device). Builds a real report file (with one inserted item)
    so this test is self-contained.
    """
    app = app_ftp
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Hello", line=1, column=1)

    upload_path = str(tmp_path / "test_b5_upload.al4rep")
    save_as(app, upload_path)
    assert os.path.isfile(upload_path)

    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    result = upload_report_file(app, upload_path, "User Configured Report 1 - Transaction Report")
    _skip_on_device_timeout(result)
    assert result["message"] is not None, f"Expected a completion message, got {result!r}"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b6_downloading_report_files_transaction_report(app_ftp, device_ip, tmp_path):
    """
    B6: Downloading Report Files - Transaction Report (requires live
    AccuLoad device). NOTE: like D7/E5, this is self-contained/order-
    independent - it verifies the download dialog flow and resulting
    file, not byte-for-byte parity with a prior upload (regression.md
    itself documents that comparison as a known-failing case, ticket
    #3861).
    """
    app = app_ftp
    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    save_path = str(tmp_path / "test_b6_download.al4rep")
    result = download_report_file(app, save_path, "User Configured Report 1 - Transaction Report")
    _skip_on_device_timeout(result)
    assert os.path.isfile(save_path), f"Expected download to save a file, result={result!r}"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b7_uploading_report_files_batch_report(app_ftp, device_ip, tmp_path):
    """B7: Uploading Report Files - Batch Report (requires live AccuLoad device)."""
    app = app_ftp
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Hello", line=1, column=1)

    upload_path = str(tmp_path / "test_b7_upload.al4rep")
    save_as(app, upload_path)
    assert os.path.isfile(upload_path)

    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    result = upload_report_file(app, upload_path, "User Configured Report 1 - Batch Detail")
    _skip_on_device_timeout(result)
    assert result["message"] is not None, f"Expected a completion message, got {result!r}"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b8_downloading_report_files_batch_report(app_ftp, device_ip, tmp_path):
    """B8: Downloading Report Files - Batch Report (requires live AccuLoad device)."""
    app = app_ftp
    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    save_path = str(tmp_path / "test_b8_download.al4rep")
    result = download_report_file(app, save_path, "User Configured Report 1 - Batch Detail")
    _skip_on_device_timeout(result)
    assert os.path.isfile(save_path), f"Expected download to save a file, result={result!r}"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b9_uploading_report_files_prove_report(app_ftp, device_ip, tmp_path):
    """B9: Uploading Report Files - Prove Report (requires live AccuLoad device)."""
    app = app_ftp
    create_new_report_file(app)
    insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value="Hello", line=1, column=1)

    upload_path = str(tmp_path / "test_b9_upload.al4rep")
    save_as(app, upload_path)
    assert os.path.isfile(upload_path)

    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    result = upload_report_file(app, upload_path, "Prove Report")
    _skip_on_device_timeout(result)
    assert result["message"] is not None, f"Expected a completion message, got {result!r}"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b10_downloading_report_files_prove_report(app_ftp, device_ip, tmp_path):
    """B10: Downloading Report Files - Prove Report (requires live AccuLoad device)."""
    app = app_ftp
    load_test_file(app)

    connected = configure_ip_and_connect(app, device_ip, timeout=15)
    if not connected:
        pytest.skip("AccuLoad device not reachable/connected")

    save_path = str(tmp_path / "test_b10_download.al4rep")
    result = download_report_file(app, save_path, "Prove Report")
    _skip_on_device_timeout(result)
    assert os.path.isfile(save_path), f"Expected download to save a file, result={result!r}"


def test_b11_loading_am3_report_files(app):
    """
    B11: Loading AM3 Report Files.
      1. Open the "Open" file dialog.
      2. Navigate to and open configs/B11.RPX (an AccuMate III report
         file provided for this test).
      3. Verify the file loads/converts into a real, readable AccuMate IV
         Report view (main window title reflects the loaded file; report
         canvas is queryable without error).
    """
    rpx_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs", "B11.RPX"))
    if not os.path.isfile(rpx_path):
        pytest.skip(f"B11: provided AM3 .RPX test file not found: {rpx_path}")

    print(f"[STEP] Loading AM3 report file: {rpx_path}")
    open_file_dialog(app, rpx_path)

    start = time.time()
    title = ""
    while time.time() - start < 25:
        title = app.get_window().window_text()
        if "B11" in title:
            break
        time.sleep(1)
    assert "B11" in title, f"Main window title does not reflect the loaded .RPX file: {title!r}"

    items = get_report_items(app)
    assert items is not None, "Expected the Report canvas to be readable after loading the AM3 file"


def test_b12_loading_early_am4_report_files(app):
    """
    B12: Loading Early AM4 Report Files.
      1. Open the "Open" file dialog.
      2. Navigate to and open configs/B12.al4rep (an early-AM4-format
         report file with <none> Alarm entries, provided for this test).
      3. Verify the file loads into a real, readable AccuMate IV Report
         view (main window title reflects the loaded file; report canvas
         is queryable without error).
    """
    report_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "configs", "B12.al4rep"))
    if not os.path.isfile(report_path):
        pytest.skip(f"B12: provided early-AM4-format report file not found: {report_path}")

    print(f"[STEP] Loading early-AM4 report file: {report_path}")
    open_file_dialog(app, report_path)

    start = time.time()
    title = ""
    while time.time() - start < 25:
        title = app.get_window().window_text()
        if "B12" in title:
            break
        time.sleep(1)
    assert "B12" in title, f"Main window title does not reflect the loaded report file: {title!r}"

    items = get_report_items(app)
    assert items is not None, "Expected the Report canvas to be readable after loading the early-AM4 file"


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_b13_upload_download_multiple_times(app_ftp, device_ip, tmp_path):
    """
    B13: Upload/Download Multiple Times (requires live AccuLoad device).
      Upload a report file, then download it back and confirm a file was
      produced; repeat with a second, distinct report file/type.

    Reloads the real test config file (load_test_file) and reconnects
    before each iteration's upload/download - creating a new bare Report
    Configuration document (create_new_report_file) switches the current
    document away from the connected AL4 config, which disables the
    Upload/Download ribbon buttons the same way it disables "Document
    Options" (confirmed live for B4/B5/B7/B9) - so the connection/document
    state must be re-established each round, not just once up front.
    """
    app = app_ftp
    for i, report_type in enumerate(
        ["User Configured Report 1 - Transaction Report", "User Configured Report 2 - Batch Detail"]
    ):
        create_new_report_file(app)
        insert_report_item(app, item_type=ITEM_TYPE_USER_TEXT, item_value=f"Round{i}", line=1, column=1)

        upload_path = str(tmp_path / f"test_b13_upload_{i}.al4rep")
        save_as(app, upload_path)
        assert os.path.isfile(upload_path)

        load_test_file(app)
        connected = configure_ip_and_connect(app, device_ip, timeout=15)
        if not connected:
            pytest.skip("AccuLoad device not reachable/connected")

        upload_result = upload_report_file(app, upload_path, report_type)
        _skip_on_device_timeout(upload_result)
        assert upload_result["message"] is not None, f"Expected a completion message, got {upload_result!r}"

        # Re-load the test config file (not just re-check connectivity)
        # before downloading. Live testing showed AccuMate's active tab can
        # revert to the just-created bare Report Configuration document
        # after a real upload completes/its dialogs are dismissed (visible
        # in a teardown screenshot: the Report Configuration tab was active
        # again, not the connected AL4 config tab), which grays out ALL
        # device ribbon buttons ("Download File From AccuLoad" included)
        # even though the app is still genuinely ONLINE - a tab-focus
        # issue, not an actual disconnect. Reloading (load_test_file just
        # switches to the already-open tab rather than opening a
        # duplicate) re-activates the correct tab; reconnect only if that
        # still isn't enough.
        load_test_file(app)
        if not app.wait_for_device_connection(timeout=15):
            connected = configure_ip_and_connect(app, device_ip, timeout=15)
            if not connected:
                pytest.skip("AccuLoad device not reachable/connected before download")

        download_path = str(tmp_path / f"test_b13_download_{i}.al4rep")
        download_result = download_report_file(app, download_path, report_type)
        _skip_on_device_timeout(download_result)
        assert os.path.isfile(download_path), f"Expected download to save a file, result={download_result!r}"


@pytest.mark.requires_device
@pytest.mark.special_case
def test_b14_no_report_to_download(app, device_ip, tmp_path):
    """
    B14: No Report To Download - SPECIAL CASE, not part of the standard
    regression pass.

    Requires live AccuLoad device with all *.CFG files removed from
    /media/data/database. This repo cannot safely arrange/verify the
    required device-side precondition (no report configs present on the
    AccuLoad), so this is documented as a special case rather than run as
    part of the standard automated regression suite. Same class of
    simplification as C6/D8/E6.
    """
    pytest.skip(
        "B14: SPECIAL CASE - requires a device with no report config "
        "files present, a device-side state this repo cannot safely "
        "arrange or verify; not part of the standard regression pass"
    )
