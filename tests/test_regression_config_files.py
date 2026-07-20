"""
Automated coverage for scenarios/regression.md sections A1, A2, A3, A4, A5,
and A15 (config-file creation/editing/saving/loading) - the
config-file-handling subset of the broader regression suite that's fully
automatable with this project's existing app/controls/workflows/pages
layers, without needing a live AccuLoad device connection or a second
application (AccuMate III, older AccuMate 4, or the AccuLoad's own device
UI, all used by later regression sections but out of scope for this
pywinauto-based framework).

A4/A5 only automate the "load the provided old-format file into the
current AccuMate version and verify it converts/loads successfully"
half of each scenario (regression.md's own steps 10-13 for A4, 7-9 for
A5) - the "create the file with the actual older AccuMate III/IV
application" half (steps 2-9 for A4, 2-6 for A5) is out of scope since
those older application versions aren't installed/available in this
environment. configs/0-10.AL4 and configs/11-25.A3X are the provided
old-format files for A4/A5 respectively.
"""

import os
import re
import time

import pytest

from controls.common_controls import get_tree
from pages.main_page import MainPage
from workflows.file_workflows import (
    new_config_file,
    load_config_file,
    load_and_migrate_old_config_file,
    save_as,
)

SAVE_AS_OUTPUT_FILE = os.path.normpath(
    r"C:\Users\allenma\Documents\Testing\regression_a2_save_output.al4"
)

A4_OLD_AL4_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "configs", "0-10.AL4")
)
A5_OLD_A3X_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "configs", "11-25.A3X")
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


def test_a4_loading_old_al4_config_files(app):
    """
    regression.md A4: Loading Old AL4 Config Files.

    Automates steps 10-13 using the provided configs/0-10.AL4 (an
    old-format config from an earlier AccuMate version) in place of a file
    freshly created with the old application itself (steps 2-9, out of
    scope - that older app version isn't available here):
      10. Open the old-format file in the current AccuMate version.
      11. Verify AccuMate is updating the file (the real, confirmed-live
          migration flow: an "old version" notice dialog, a "Migrating
          AccuMate Configuration... [NN%]" progress window, then a
          completion dialog naming the newly-created migrated file).
      12. Navigate the migrated config and verify no information was lost
          (Config/System/Recipe Directory tree structure intact).
      13. (Document Options IP/Comm Address verification is skipped here -
          the provided file's baked-in values weren't set by this test, so
          there's nothing known to assert against; this step still needs a
          file created via steps 2-9 with the old app to be verifiable.)

    Live-confirmed migrated-file naming convention: "<original>-1_12.AL4"
    is created by AccuMate in the same directory as the original file.
    """
    if not os.path.isfile(A4_OLD_AL4_FILE):
        pytest.skip(f"Old-format A4 config file not found: {A4_OLD_AL4_FILE}")

    print(f"[STEP] Loading old-format config file: {A4_OLD_AL4_FILE}")
    migrated_path = load_and_migrate_old_config_file(app, A4_OLD_AL4_FILE)

    try:
        assert os.path.isfile(migrated_path), (
            f"Migration reported success but migrated file not found on disk: {migrated_path}"
        )

        print(f"[STEP] Opening migrated file to verify no information was lost: {migrated_path}")
        load_config_file(app, migrated_path, close_existing=False)

        expected_name = os.path.splitext(os.path.basename(migrated_path))[0]
        ok, title = _wait_for_title_contains(app, expected_name)
        assert ok, f"Main window title does not reflect the migrated config file: {title!r}"

        roots = _root_texts(app)
        for expected_root in ("Config Directory", "System Directory", "Recipe Directory"):
            assert expected_root in roots, (
                f"Migrated config file is missing expected '{expected_root}' - possible data loss: {roots}"
            )
    finally:
        if os.path.isfile(migrated_path):
            os.remove(migrated_path)


def test_a5_loading_a3x_config_files(app):
    """
    regression.md A5: Loading A3X Config Files.

    Automates steps 7-9 using the provided configs/11-25.A3X (an AccuMate
    III / AccuLoad III.NET config file) in place of a file freshly created
    with the AccuMate III application itself (steps 2-6, out of scope -
    that older app isn't available here):
      7/8. Open the .A3X file in the current AccuMate (IV) version.
      9. Verify "Number of Load Arms" is displayed (compared to the
         AccuMate III view in the original scenario - here just confirmed
         to have loaded as a real, non-blank numeric value, since there's
         no independent AccuMate III view available to compare against).
    """
    if not os.path.isfile(A5_OLD_A3X_FILE):
        pytest.skip(f"Old-format A5 config file not found: {A5_OLD_A3X_FILE}")

    print(f"[STEP] Loading .A3X config file: {A5_OLD_A3X_FILE}")
    load_config_file(app, A5_OLD_A3X_FILE)

    expected_name = os.path.splitext(os.path.basename(A5_OLD_A3X_FILE))[0]
    ok, title = _wait_for_title_contains(app, expected_name)
    assert ok, f"Main window title does not reflect the loaded .A3X file: {title!r}"

    roots = _root_texts(app)
    assert "Config Directory" in roots, (
        f"Loaded .A3X file did not display the expected Config Directory tree: {roots}"
    )

    page = MainPage(app, request=None)
    page.test_name = "test_a5_loading_a3x_config_files"
    page.select_tree_path(["Config Directory", "System Layout"])

    load_arms = page.get_value("Number of Load Arms")
    assert re.fullmatch(r"\d+", load_arms), (
        f"Expected 'Number of Load Arms' to be a plain numeric value, got: {load_arms!r}"
    )
    print(f"[INFO] 'Number of Load Arms' loaded from .A3X file: {load_arms}")


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
