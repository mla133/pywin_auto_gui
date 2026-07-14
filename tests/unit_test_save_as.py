import os

import pytest

from workflows.file_workflows import load_test_file, save_as

SAVE_AS_TEST_FILE = os.path.normpath(
    r"C:\Users\allenma\Documents\Testing\unit_test_save_as_output.al4"
)


def test_save_as(app):
    """
    Verifies workflows.file_workflows.save_as():
      1. Loads the default test file.
      2. Saves it to a new path via the ribbon Application Button -> "Save
         As..." menu item.
      3. Confirms the new file exists and the main window's title bar
         reflects the new filename.
      4. Calls save_as() again on the SAME path to verify the "Confirm Save
         As" overwrite prompt is handled automatically (save_as() must be
         safe to call repeatedly against an existing file).
    """
    if os.path.isfile(SAVE_AS_TEST_FILE):
        os.remove(SAVE_AS_TEST_FILE)

    print("[STEP] Loading test file")
    load_test_file(app)

    print(f"[STEP] Save As -> {SAVE_AS_TEST_FILE}")
    save_as(app, SAVE_AS_TEST_FILE)

    assert os.path.isfile(SAVE_AS_TEST_FILE), "save_as() did not create the expected file"

    win = app.get_window()
    expected_name = os.path.basename(SAVE_AS_TEST_FILE)
    assert expected_name in win.window_text(), (
        f"Main window title does not reflect the saved filename: {win.window_text()!r}"
    )

    print("[STEP] Save As again (same path) - verifying overwrite prompt is handled")
    save_as(app, SAVE_AS_TEST_FILE)

    assert os.path.isfile(SAVE_AS_TEST_FILE)

    # Guard against the exact bug class this test caught previously: a
    # mis-clicked overwrite confirmation can silently leave a modal dialog
    # open, masked by SAVE_AS_TEST_FILE already existing from the first
    # save. Explicitly assert no stray "Save As"/"Confirm..." dialogs remain.
    for w in app.app.windows():
        try:
            title = w.window_text()
        except Exception:
            continue
        assert "Save As" not in title and "onfirm" not in title, (
            f"Unexpected dialog left open after save_as(): {title!r}"
        )

    print(f"[INFO] save_as() verified for: {SAVE_AS_TEST_FILE}")

    os.remove(SAVE_AS_TEST_FILE)
