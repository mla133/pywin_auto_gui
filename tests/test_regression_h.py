"""
Automated coverage for scenarios/regression.md section H9 (HMI B Failure
parameter removed from System Directory Listing) - fully automatable using
only the AccuMate app itself, no live AccuLoad device connection and no
other application required.

NOTE: H1/H2 (Help file content vs. the Smith Manual) and H3-H8 (updated max
values for parameters, requiring provided H3-H3.AL4/.al4equ/.al4rep files,
PuTTY access to the AccuLoad's /dev/shm, batch runs, and PDF report
comparisons) are NOT covered here - deliberately out of scope for this
lightweight, app-only automation approach.
"""

from workflows.file_workflows import new_config_file
from controls.common_controls import get_list, get_list_row_texts

# regression.md H9: "HMI B Failure" parameter, ID 1615, previously listed
# under System Directory -> 600 - Default Alarms, has been removed.
_HMI_B_FAILURE_PARAM_ID = "1615"
_HMI_B_FAILURE_PARAM_NAME = "HMI B Failure"


def test_h9_hmi_b_failure_parameter_removed(app, page):
    """
    H9: HMI B Failure parameter removed from Systems Directory Listing.
      1. Create a new AccuMate Config File.
      2. Navigate to System Directory -> 600 - Default Alarms.
      3. Verify the "HMI B Failure" parameter (1615) is no longer listed.
    """
    print("[STEP] Creating a new AccuMate Config File")
    new_config_file(app)

    print("[STEP] Navigating to System Directory -> Default Alarms")
    page.select_tree_path(["System Directory", "Default Alarms"])

    lst = get_list(app)
    rows = [get_list_row_texts(lst, i) for i in range(lst.item_count())]

    matching_rows = [
        row for row in rows
        if any(_HMI_B_FAILURE_PARAM_ID == cell or _HMI_B_FAILURE_PARAM_NAME in cell for cell in row)
    ]

    print(f"[INFO] Default Alarms parameter list has {len(rows)} rows")
    assert not matching_rows, (
        f"Expected 'HMI B Failure' (1615) to no longer be listed under System "
        f"Directory -> 600 - Default Alarms, but found: {matching_rows}"
    )
