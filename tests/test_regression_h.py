"""
Automated coverage for scenarios/regression.md section H:
  - H1/H2: AccuMate's own Help file (AccuMate.CHM) content for injectors
    1-44, verified by decompiling the CHM directly (see
    workflows/help_content.py) rather than driving the live Help viewer -
    no AccuMate window is launched/focused for these two tests.
  - H9: HMI B Failure parameter removed from System Directory Listing -
    fully automatable using only the AccuMate app itself, no live AccuLoad
    device connection and no other application required.

NOTE on H1/H2 scope: regression.md's original intent was to compare against
the "Smith Manual" (an external reference document). Per user clarification,
that manual only documents injectors 1-24 - the extra 20 injectors (25-44)
were added later as a feature and the manual was never updated to cover them
- so a manual-vs-AccuMate comparison for the 25-44 range is not meaningful.
These tests instead verify AccuMate's own Help content directly shows
injectors 1-44 for the specific items regression.md calls out (this is
still a real, valuable regression check: it would catch the Help content
itself regressing/losing the injector 25-44 entries, independent of the
Smith Manual's own scope gap).

NOTE: H3-H8 (updated max values for parameters, requiring provided
H3-H3.AL4/.al4equ/.al4rep files, PuTTY access to the AccuLoad's /dev/shm,
batch runs, and PDF report comparisons) are NOT covered here - deliberately
out of scope for this lightweight, app-only automation approach.
"""

from workflows.file_workflows import new_config_file
from workflows.help_content import decompiled_chm, read_help_page
from controls.common_controls import get_list, get_list_row_texts


def test_h1_dy_help_shows_injectors_1_to_44():
    """
    H1: DY - Dynamic Displays help topic covers Injectors 1-44.
      Verifies the Help topic's "Injector Dynamic Displays", "Batch Dynamic
      Displays", and "Transaction Dynamic Displays" sections (which hold the
      "Injector Current/Programmed Pulse Rate" and "Additive Batch/
      Transaction Volume" entries) are present and reference their expected
      image tables.

      NOTE: the actual per-injector rows in those tables are rendered as PNG
      images (CmdDY_IV1/IV2.PNG, CmdDY_BV1/2.PNG, CmdDY_TV1/2.PNG), not HTML
      text, so their specific injector 1-44 numbering can't be grepped here.
      That numbering was manually visually verified (confirmed live: Current/
      Programmed Pulse Rate entries run Injector 1-44 across
      CmdDY_IV1.PNG/CmdDY_IV2.PNG; Additive Batch/Transaction Volume entries
      run Additive #1-44 across CmdDY_BV1/2.PNG and CmdDY_TV1/2.PNG). This
      test automates the structural part: that the DY topic still has these
      three sections and their expected image references, so a future
      Help-content regression (e.g. a renamed/removed image, or a missing
      section) would be caught.
    """
    with decompiled_chm() as chm_dir:
        dy_html = read_help_page(chm_dir, "command_DY.htm")

    assert "Injector Dynamic Displays" in dy_html
    assert "Batch Dynamic Displays" in dy_html
    assert "Transaction Dynamic Displays" in dy_html

    for expected_image in (
        "CmdDY_IV1.PNG", "CmdDY_IV2.PNG",
        "CmdDY_BV1.PNG", "CmdDY_BV2.PNG",
        "CmdDY_TV1.PNG", "CmdDY_TV2.PNG",
    ):
        assert expected_image in dy_html, (
            f"Expected DY help topic to reference '{expected_image}' "
            f"(manually confirmed to contain Injector/Additive #1-44 rows)"
        )


def test_h2_ea_help_shows_injectors_25_to_44():
    """
    H2: EA - Enquire Alarms help topic covers Injectors 25-44 (I2 command
    code, added as part of the additive expansion feature beyond the
    original 1-24 injectors).
      1. The EA command's qualifier description text explicitly documents
         "I2 = Injectors 25-44" (alongside "IN = Injectors 1-24").
      2. The "Injector Group 2" alarm mnemonic listing (the I2 results
         section) enumerates entries for Injector 25 through Injector 44.
    """
    with decompiled_chm() as chm_dir:
        ea_html = read_help_page(chm_dir, "command_EA.htm")

    assert "I2 = Injectors 25-44" in ea_html, (
        "Expected EA help topic to document 'I2 = Injectors 25-44' qualifier"
    )
    assert "Injector Group 2" in ea_html, (
        "Expected EA help topic to have an 'Injector Group 2' alarm section"
    )

    # Spot-check the boundary injectors (25 and 44) actually appear within
    # text content (not just the qualifier description above).
    for injector_num in (25, 44):
        marker = f"Injector {injector_num} "
        assert marker in ea_html, (
            f"Expected '{marker}' to appear in the EA help topic's Injector "
            f"Group 2 (I2, Injectors 25-44) alarm listing"
        )

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
