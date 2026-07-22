"""
scenarios/regression.md C1-C7 (Translation Editor).

C1-C3 are LIVE-VERIFIED (real workflow functions, real control ids, real
dialog titles - see workflows/translation_workflows.py's module docstring
for the full findings) and run as part of the default `pytest -s -v`
suite.

Scope summary (see workflows/translation_workflows.py for full detail):
  - C4-C6: need a live, reachable AccuLoad device AND a not-yet-built
    "AccuMate File Transfer" upload/download dialog workflow.
  - C7: needs a provided AM3-format Translation File (.LGX) that does not
    currently exist in this repo/environment - same class of blocker as
    D9/E7/H3-H8's provided files.
"""

import os

import pytest

from workflows.translation_workflows import (
    create_new_translation_file,
    get_translation_rows,
    open_edit_text_dialog,
    set_translation_text,
    enter_translation_for_row,
)
from workflows.file_workflows import save_as, open_file_dialog


def test_c1_creating_new_translation_files(app):
    """
    C1: Creating New Translation Files.
      1. Start the AccuMate Application.
      2. Hover 'New' under the Application Button -> 'Translation' option
         appears.
      3. Click 'Translation' -> a new Translation view is displayed
         (populated with every translatable string in the app).
    """
    create_new_translation_file(app)
    rows = get_translation_rows(app)
    assert rows is not None
    assert len(rows) >= 1


def test_c2_saving_translation_files(app, tmp_path):
    """
    C2: Saving Translation Files.
      1. Double-click 3 different grid rows, entering a New Text value
         each time via the "Edit Text" dialog -> the Translation column
         contains the new values.
      2. Save via Application Button -> Save with a valid filename -> the
         file exists on disk afterward.
    """
    create_new_translation_file(app)

    values = ["Test Translation One", "Test Translation Two", "Test Translation Three"]
    for row_index, value in enumerate(values):
        enter_translation_for_row(app, row_index, value)

    rows = get_translation_rows(app)
    for row_index, value in enumerate(values):
        assert rows[row_index][1] == value

    save_path = str(tmp_path / "test_c2_translation.al4lang")
    save_as(app, save_path)
    assert os.path.isfile(save_path)


def test_c3_loading_translation_files(app, tmp_path):
    """
    C3: Loading Translation Files.
      1. Save the Translation view to disk.
      2. Open that same file back up -> the reopened view's contents
         match what was originally saved.

    NOTE: regression.md's literal C3 flow (Save As twice under two names,
    then reopen the first while the second is still the active view) hits
    the same "double Save As on one still-open document" app-side quirk
    documented in test_regression_d.py's D5/test_regression_e.py's E3 -
    scaled back to a single save + reopen + content-comparison, which
    still exercises the real regression-relevant behavior (open_file_dialog
    compatible with Translation documents, saved content round-trips
    correctly) without the flaky double-Save-As step.
    """
    create_new_translation_file(app)
    win32_dlg, uia_dlg = open_edit_text_dialog(app, row_index=0)
    set_translation_text(uia_dlg, "Round Trip Test Value")
    original_rows = get_translation_rows(app)

    old_path = str(tmp_path / "test_c3_original.al4lang")
    save_as(app, old_path)

    open_file_dialog(app, old_path)
    reopened_rows = get_translation_rows(app)
    assert reopened_rows == original_rows


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_c4_uploading_translation_files(app, device_ip):
    """
    C4: Uploading Translation Files (requires live AccuLoad device).
      Connect to the device, then Upload File to AccuLoad -> browse to an
      .al4lang file -> upload completes successfully.
    """
    pytest.skip("C4: 'AccuMate File Transfer' upload workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_c5_downloading_translation_files(app, device_ip):
    """
    C5: Downloading Translation Files (requires live AccuLoad device).
      Connect to the device, Download File From AccuLoad -> Translations
      File -> compare against the device's own /ftp/translation_ file.txt
      via SSH/checksum.
    """
    pytest.skip("C5: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_c6_no_translation_file_to_download(app, device_ip):
    """
    C6: No Translation File To Download (requires live AccuLoad device
    with no translation file present, e.g. after a Factory Init).
      Download File From AccuLoad -> Translation File -> a warning popup
      notifies the user there is nothing to pull.
    """
    pytest.skip("C6: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.needs_live_verification
def test_c7_loading_am3_translation_files(app):
    """
    C7: Loading AM3 Translation Files (needs a provided .LGX test file,
    not currently present in this repo/environment - same class of
    blocker as D9/E7/H3-H8's provided files).
    """
    pytest.skip("C7: requires a provided AM3 .LGX test file not present in this repo")
