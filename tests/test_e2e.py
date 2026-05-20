from app.application import AccuMateApp
from workflows.file_workflows import load_test_file
from workflows.security_workflows import enter_passcode
from pages.main_page import MainPage


def test_full_user_workflow(app, request):

    print("[STEP] Loading test file")
    load_test_file(app)
    page = MainPage(app, request=request)

    print("[STEP] Navigating to Security Directory")
    page.select_tree_path(["System Directory", "Security Directory"])

    print("[STEP] Selecting Ethernet Host Security Level")
    row_index = page.select_list_item("Ethernet Host Security Level")

    print("[STEP] Editing dropdown value")
    page.edit_dropdown_value("Ethernet Host Security Level", "Security Level 2")

    print("[STEP] Handling passcode dialog (bad passcode)")
    success = enter_passcode(app, "1234")
    assert success is False

    print("[STEP] Verifying dropdown value is NOT updated")
    selected_value = page.get_value("Ethernet Host Security Level")
    assert selected_value != "Security Level 2"
