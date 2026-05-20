from app.application import AccuMateApp
from workflows.file_workflows import load_test_file
from pages.main_page import MainPage


def test_full_user_workflow():
    app = AccuMateApp()

    print("\n[STEP] Opening file")
    load_test_file(app)

    page = MainPage(app)

    print("[STEP] Expanding tree")
    page.select_tree_path(["System Directory", "Security Directory"])

    print("[STEP] Selecting list item")
    row_index = page.select_list_item("Ethernet Host Security Level")

    print("[STEP] Validating results")
    assert row_index is not None