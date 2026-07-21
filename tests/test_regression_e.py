"""
scenarios/regression.md E1-E8 (Equation Set Editor).

E1-E3 are LIVE-VERIFIED (real workflow functions, real control ids, real
dialog titles - see workflows/equation_workflows.py's module docstring for
the full findings) and run as part of the default `pytest -s -v` suite.

Scope summary (see workflows/equation_workflows.py for full detail):
  - E4-E6, E8: need a live, reachable AccuLoad device AND a not-yet-built
    "AccuMate File Transfer" upload/download dialog workflow.
  - E7: needs a provided AM3-format Equation Set File (.EQX) that does not
    currently exist in this repo/environment - same class of blocker as
    H3-H8's provided files.
"""

import os

import pytest

from workflows.equation_workflows import (
    create_new_equation_set_file,
    insert_equation_line,
    get_equation_set_rows,
)
from workflows.file_workflows import save_as, open_file_dialog


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


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_e4_uploading_equation_files(app, device_ip):
    """
    E4: Uploading Equation Files (requires live AccuLoad device).
      Connect to the device, then Upload File to AccuLoad -> browse to a
      .al4equ file -> upload completes successfully.
    """
    pytest.skip("E4: 'AccuMate File Transfer' upload workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_e5_downloading_equation_files(app, device_ip):
    """
    E5: Downloading Equation Files (requires live AccuLoad device).
      Connect to the device, Download File From AccuLoad -> Equations File
      -> compare against the file uploaded in E4.
    """
    pytest.skip("E5: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_e6_no_equation_file_to_download(app, device_ip):
    """
    E6: No Equation File To Download (requires live AccuLoad device with
    Equation.cfg deleted from /media/data/database, or a fresh AccuLoad
    image).
      Download File From AccuLoad -> Equations File -> a warning popup
      notifies the user there is nothing to pull.
    """
    pytest.skip("E6: 'AccuMate File Transfer' download workflow not yet built - see module docstring")


@pytest.mark.needs_live_verification
def test_e7_loading_am3_equation_files(app):
    """
    E7: Loading AM3 Equation Files (needs a provided .EQX test file, not
    currently present in this repo/environment - same class of blocker as
    H3-H8's provided files).
    """
    pytest.skip("E7: requires a provided AM3 .EQX test file not present in this repo")


@pytest.mark.requires_device
@pytest.mark.needs_live_verification
def test_e8_uploading_empty_equation_file(app, device_ip):
    """
    E8: Uploading Empty Equation File (requires live AccuLoad device).
      Connect to the device, Upload File to AccuLoad -> browse to an empty
      equations file -> a popup warns "No entries defined. Nothing to
      upload."
    """
    pytest.skip("E8: 'AccuMate File Transfer' upload workflow not yet built - see module docstring; also needs a provided empty equations file")
