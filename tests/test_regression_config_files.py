"""
Automated coverage for scenarios/regression.md sections A1, A2, A3, A4, A5,
A6, and A15 (config-file creation/editing/saving/loading) - the
config-file-handling subset of the broader regression suite that's fully
automatable with this project's existing app/controls/workflows/pages
layers, without needing a live AccuLoad device connection or a second
application (AccuMate III, older AccuMate 4, or the AccuLoad's own device
UI, all used by later regression sections but out of scope for this
pywinauto-based framework).

A4/A5/A6 only automate the "load the provided old-format file into the
current AccuMate version and verify it converts/loads successfully"
half of each scenario (regression.md's own steps 10-13 for A4, 7-9 for
A5, 1/15-27 for A6) - the "create the file with the actual older AccuMate
III/IV application" half (steps 2-9 for A4, 2-6 for A5, 2-14 for A6) is
out of scope since those older application versions aren't installed/
available in this environment. configs/0-10.AL4, configs/11-25.A3X, and
configs/1-11.AL4 are the provided old-format files for A4/A5/A6
respectively.
"""

import os
import re
import time

import pytest

from controls.common_controls import get_tree, get_list, get_list_row_texts
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
A6_OLD_AL4_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "configs", "1-11.AL4")
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


def _list_rows(app):
    """
    Read all rows of the currently-displayed SysListView32 as
    (item_code, name, value, extra, level) tuples, as returned by
    get_list_row_texts.
    """
    lst = get_list(app)
    return [tuple(get_list_row_texts(lst, i)) for i in range(lst.item_count())]


def _field(rows, field_name):
    """Return the (code, value) for the row whose name column == field_name."""
    for row in rows:
        if row[1] == field_name:
            return row[0], row[2]
    raise AssertionError(f"Field {field_name!r} not found in rows: {rows}")


def _split_blocks(rows):
    """
    Split a single list view's rows into named blocks, for sections like
    "Serial Port" and "Recipe Injectors" that show several offsets
    ("Serial Port - 1", "Injector - 1", ...) as header rows (blank item
    code) within one flat list, rather than as separate tree nodes.
    """
    blocks = {}
    current = None

    for row in rows:
        code, name = row[0], row[1]
        if code == "" and name:
            current = name
            blocks[current] = []
        elif current is not None:
            blocks[current].append(row)

    return blocks


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


def test_a4_loading_old_al4_config_files(app, record_step):
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
    step_screenshot_dir = os.path.join("screenshots", "test_a4_loading_old_al4_config_files", "migration_dialogs")
    try:
        migration_result = load_and_migrate_old_config_file(app, A4_OLD_AL4_FILE, screenshot_dir=step_screenshot_dir)
    except Exception as exc:
        record_step(10, "failed", app=app, screenshot=True, note=f"Open/migration did not complete: {exc}")
        record_step(11, "skipped", note="Not reached - step 10 failed")
        record_step(12, "skipped", note="Not reached - step 10 failed")
        record_step(13, "skipped", note="Out of scope - not verified by this test")
        raise
    else:
        migrated_path = migration_result.migrated_path
        record_step(10, "passed", app=app, note="Old-format file opened without error")
        # Use the progress dialog's own screenshot (captured live, while
        # migrating) rather than app=app/screenshot=True here - by this
        # point in the test the migration dialogs have already been
        # dismissed, so a screenshot of the main window now would miss
        # the actual migration-in-progress evidence entirely.
        record_step(11, "passed",
                    screenshot_path=migration_result.progress_screenshot or migration_result.notice_screenshot,
                    note=f"Migration completed: {os.path.basename(migrated_path)}")

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
    except Exception as exc:
        record_step(12, "failed", app=app, screenshot=True, note=f"Migrated config verification failed: {exc}")
        record_step(13, "skipped", note="Out of scope - not verified by this test")
        raise
    else:
        record_step(12, "passed", app=app, screenshot=True, note=f"Directory tree intact: {roots}")
        record_step(13, "skipped",
                    note="Out of scope - the provided file's baked-in IP/Comm values weren't set by this test")
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


def test_a6_conversion_of_old_al4_offsets(app):
    """
    regression.md A6: Conversion Of Old AccuMate 4 Offsets.

    Automates steps 1, 15-16 (migration) plus the core intent of steps
    17-27 (verify the 2nd offset of each multi-offset section did NOT get
    cloned from the 1st offset during migration) using the provided
    configs/1-11.AL4 - a real, previously-configured old-format file - in
    place of a file purpose-built via steps 2-14 with the actual older
    AccuMate IV application (out of scope here, that older app version
    isn't available in this environment).

    Since this is a real device config rather than one built with the
    exact test values from steps 2-14, some fields legitimately match
    between offset 1 and 2 (e.g. both Arm 1/Arm 2 General Purpose sections
    have blank/default Permissive messages) - that's expected real data,
    not a regression. What steps 17-27 are actually guarding against is
    offset 2 silently aliasing/cloning offset 1's data during migration,
    so this test asserts, per section, that offset 1 and offset 2:
      - have distinct underlying item codes (AccuMate's own per-offset
        parameter IDs - these are assigned by the app itself and would
        collide/duplicate if migration merged two offsets together), and
      - have a different value for at least one naturally-unique field
        (Tag, Recipe Name/Used, Load Arm ID, Serial Port Function) that
        this specific file's real values are confirmed (live) to differ
        on - a stronger, real assertion than the item-code check alone.
    """
    if not os.path.isfile(A6_OLD_AL4_FILE):
        pytest.skip(f"Old-format A6 config file not found: {A6_OLD_AL4_FILE}")

    print(f"[STEP] Loading and migrating old-format config file: {A6_OLD_AL4_FILE}")
    migrated_path = load_and_migrate_old_config_file(app, A6_OLD_AL4_FILE)

    try:
        assert os.path.isfile(migrated_path), (
            f"Migration reported success but migrated file not found on disk: {migrated_path}"
        )

        print(f"[STEP] Opening migrated file to verify offsets: {migrated_path}")
        load_config_file(app, migrated_path, close_existing=False)

        expected_name = os.path.splitext(os.path.basename(migrated_path))[0]
        ok, title = _wait_for_title_contains(app, expected_name)
        assert ok, f"Main window title does not reflect the migrated config file: {title!r}"

        roots = _root_texts(app)
        for expected_root in ("Config Directory", "System Directory", "Recipe Directory"):
            assert expected_root in roots, (
                f"Migrated config file is missing expected '{expected_root}' - possible data loss: {roots}"
            )

        page = MainPage(app, request=None)
        page.test_name = "test_a6_conversion_of_old_al4_offsets"

        def assert_offsets_differ(section_label, tree_path_1, tree_path_2, unique_field, check_codes=True):
            print(f"[STEP] Comparing {section_label} offset 1 vs offset 2")
            page.select_tree_path(tree_path_1)
            rows_1 = _list_rows(app)
            page.select_tree_path(tree_path_2)
            rows_2 = _list_rows(app)

            code_1, value_1 = _field(rows_1, unique_field)
            code_2, value_2 = _field(rows_2, unique_field)

            if check_codes:
                assert code_1 != code_2, (
                    f"{section_label}: offset 1 and offset 2 share the same underlying "
                    f"item code ({code_1!r}) for {unique_field!r} - migration may have "
                    f"aliased/cloned the offsets instead of keeping them distinct"
                )
            assert value_1 != value_2, (
                f"{section_label}: offset 2's {unique_field!r} ({value_2!r}) matches "
                f"offset 1's ({value_1!r}) - migration may have cloned offset 1's data "
                f"into offset 2"
            )
            print(f"[INFO] {section_label}: offset 1 {unique_field}={value_1!r}, "
                  f"offset 2 {unique_field}={value_2!r}")

        assert_offsets_differ(
            "Pulse Inputs",
            ["Config Directory", "100 - Pulse Inputs", "Pulse In 01"],
            ["Config Directory", "100 - Pulse Inputs", "Pulse In 02"],
            "Pulse Input Tag",
        )
        assert_offsets_differ(
            "Pulse Outputs",
            ["Config Directory", "200 - Pulse Outputs", "Pulse Out 01"],
            ["Config Directory", "200 - Pulse Outputs", "Pulse Out 02"],
            "Pulse Output Tag",
        )
        assert_offsets_differ(
            "Digital Inputs",
            ["Config Directory", "300 - Digital Inputs", "Dig In 01"],
            ["Config Directory", "300 - Digital Inputs", "Dig In 02"],
            "Digital Input Tag",
        )
        assert_offsets_differ(
            "Digital Outputs",
            ["Config Directory", "500 - Digital Outputs", "Dig Out 01"],
            ["Config Directory", "500 - Digital Outputs", "Dig Out 02"],
            "Digital Output Tag",
        )
        assert_offsets_differ(
            "Analog I/O",
            ["Config Directory", "900 - Analog I/O", "Analog I/O 01"],
            ["Config Directory", "900 - Analog I/O", "Analog I/O 02"],
            "Analog I/O Tag",
        )
        assert_offsets_differ(
            "Arm General Purpose",
            ["Arm 1", "100 - General Purpose"],
            ["Arm 2", "100 - General Purpose"],
            "Load Arm ID",
            # Arm 1/Arm 2 are separate top-level tree branches (not
            # sequential offsets within one flat list like Pulse
            # Inputs/Outputs), so AccuMate legitimately reuses the same
            # relative item code per arm - only compare values here.
            check_codes=False,
        )
        assert_offsets_differ(
            "Recipes",
            ["Recipe Directory", "Recipe 01"],
            ["Recipe Directory", "Recipe 02"],
            "Recipe Name",
            # Recipe 01/Recipe 02 are also separate top-level tree
            # branches (same reasoning as Arms above) - item codes
            # legitimately repeat per recipe.
            check_codes=False,
        )

        print("[STEP] Comparing Serial Port offset 1 vs offset 2 (single list, multiple offsets)")
        page.select_tree_path(["System Directory", "700 - Communications", "Serial Port"])
        serial_blocks = _split_blocks(_list_rows(app))
        assert "Serial Port - 1" in serial_blocks and "Serial Port - 2" in serial_blocks, (
            f"Expected 'Serial Port - 1'/'Serial Port - 2' blocks, got: {list(serial_blocks)}"
        )
        sp1_code, sp1_function = _field(serial_blocks["Serial Port - 1"], "Function")
        sp2_code, sp2_function = _field(serial_blocks["Serial Port - 2"], "Function")
        assert sp1_code != sp2_code, "Serial Port offsets 1/2 share the same underlying item code for Function"
        assert sp1_function != sp2_function, (
            f"Serial Port offset 2's Function ({sp2_function!r}) matches offset 1's "
            f"({sp1_function!r}) - migration may have cloned offset 1 into offset 2"
        )
        print(f"[INFO] Serial Port: offset 1 Function={sp1_function!r}, offset 2 Function={sp2_function!r}")

        print("[STEP] Comparing Recipe Injectors offset 1 vs offset 2 item codes (Recipe 01)")
        page.select_tree_path(["Recipe Directory", "Recipe 01", "Recipe Injectors"])
        injector_blocks = _split_blocks(_list_rows(app))
        assert "Injector - 1" in injector_blocks and "Injector - 2" in injector_blocks, (
            f"Expected 'Injector - 1'/'Injector - 2' blocks, got: {list(injector_blocks)}"
        )
        inj1_codes = {row[0] for row in injector_blocks["Injector - 1"]}
        inj2_codes = {row[0] for row in injector_blocks["Injector - 2"]}
        assert not (inj1_codes & inj2_codes), (
            f"Recipe Injectors offset 1 and offset 2 share item codes "
            f"({inj1_codes & inj2_codes}) - migration may have aliased the offsets"
        )
        print(f"[INFO] Recipe Injectors: offset 1 codes={sorted(inj1_codes)}, offset 2 codes={sorted(inj2_codes)}")
    finally:
        if os.path.isfile(migrated_path):
            os.remove(migrated_path)


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
