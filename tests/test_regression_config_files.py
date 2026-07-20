"""
Automated coverage for scenarios/regression.md sections A1, A2, A3, and A15
(config-file creation/editing/saving/loading) - the config-file-handling
subset of the broader regression suite that's fully automatable with this
project's existing app/controls/workflows/pages layers, without needing a
live AccuLoad device connection or a second application (AccuMate III,
older AccuMate 4, or the AccuLoad's own device UI, all used by later
regression sections but out of scope for this pywinauto-based framework).
"""

import os
import time

import pytest

from controls.common_controls import get_tree
from workflows.file_workflows import new_config_file, load_config_file, save_as

SAVE_AS_OUTPUT_FILE = os.path.normpath(
    r"C:\Users\allenma\Documents\Testing\regression_a2_save_output.al4"
)


def _wait_for_title_contains(app, expected_substring, timeout=25):
    """
    Poll the main window's title for `expected_substring` (case-insensitive).
    AccuMate's title update lags behind the Open dialog closing while the
    app attempts a device connection using the newly-loaded config's comm
    settings (observed elsewhere in this project up to ~10-13s) - checking
    immediately/too briefly can read the *previous* title.
    """
    start = time.time()
    title = ""

    while time.time() - start < timeout:
        title = app.get_window().window_text()
        if expected_substring.lower() in title.lower():
            return True, title
        time.sleep(0.5)

    return False, title


def _root_texts(app):
    tree = get_tree(app)
    return [r.text() for r in tree.roots()]


def test_a1_creating_new_config_file(app):
    """
    regression.md A1: Creating New Config Files.
      1. Start the AccuMate Application -> blank view.
      2/3. Click the Application Button -> New -> a new AccuMate Config
           File is displayed.
    """
    print("[STEP] Creating a new AccuMate Config File")
    new_config_file(app)

    win = app.get_window()
    assert "AccuMate for AccuLoad" in win.window_text()

    roots = _root_texts(app)
    assert "Config Directory" in roots, (
        f"New AccuMate Config File did not display the expected Config Directory tree: {roots}"
    )


def test_a2_saving_config_file(app, page):
    """
    regression.md A2: Saving Config Files.
      1. Navigate to Config Directory -> System Layout.
      2/3. Double click "Number of Load Arms", change 6 -> 3 via the "Edit
           Program Code Data" dialog, OK.
      4/5. Save As to a valid location/name.
      6. Verify the file exists on disk.
    """
    if os.path.isfile(SAVE_AS_OUTPUT_FILE):
        os.remove(SAVE_AS_OUTPUT_FILE)

    print("[STEP] Creating a new AccuMate Config File")
    new_config_file(app)

    print("[STEP] Navigating to Config Directory -> System Layout")
    page.select_tree_path(["Config Directory", "System Layout"])

    print("[STEP] Changing Number of Load Arms to 3")
    page.edit_program_code_data("Number of Load Arms", "3")

    assert page.get_value("Number of Load Arms") == "3"

    print(f"[STEP] Save As -> {SAVE_AS_OUTPUT_FILE}")
    save_as(app, SAVE_AS_OUTPUT_FILE)

    assert os.path.isfile(SAVE_AS_OUTPUT_FILE), "Save As did not create the expected file"

    os.remove(SAVE_AS_OUTPUT_FILE)


def test_a3_loading_current_al4_config_file(app, config_file):
    """
    regression.md A3: Loading Current AL4 Config Files.
      1. Start the AccuMate Application -> blank view.
      2/3. Open... -> navigate to and select a .AL4 file -> the AccuMate IV
           configuration file view appears.
    """
    if not config_file:
        pytest.skip("No AccuMate config file available (pass --accumate-config-file)")

    print(f"[STEP] Loading config file: {config_file}")
    load_config_file(app, config_file)

    expected_name = os.path.splitext(os.path.basename(config_file))[0]
    ok, title = _wait_for_title_contains(app, expected_name)
    assert ok, f"Main window title does not reflect the loaded config file: {title!r}"

    roots = _root_texts(app)
    assert "Config Directory" in roots, (
        f"Loaded config file did not display the expected Config Directory tree: {roots}"
    )


def test_a15_changing_values_in_config(app, page):
    """
    regression.md A15: Changing Values in a Config.
      1. Start the AccuMate Application.
      2. Click New -> a new AccuMate Config File is displayed.
      3. Navigate to System Layout, change Number of Load Arms from 6 to 3
         -> the value changes to 3 and the tree drops Arms 4-6.
    """
    print("[STEP] Creating a new AccuMate Config File")
    new_config_file(app)

    print("[STEP] Navigating to Config Directory -> System Layout")
    page.select_tree_path(["Config Directory", "System Layout"])

    before_roots = _root_texts(app)
    assert any("Arm 6" in r for r in before_roots), f"Expected 6 arms before edit: {before_roots}"

    print("[STEP] Changing Number of Load Arms to 3")
    page.edit_program_code_data("Number of Load Arms", "3")

    assert page.get_value("Number of Load Arms") == "3"

    after_roots = _root_texts(app)
    assert any("Arm 3" in r for r in after_roots), f"Expected Arm 3 to remain: {after_roots}"
    assert not any(r in ("Arm 4", "Arm 5", "Arm 6") for r in after_roots), (
        f"Expected Arms 4-6 to be dropped from the tree: {after_roots}"
    )
