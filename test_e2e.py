from workflows import load_test_file, select_list_item_by_text, expand_first_tree_node, select_tree_path
from utils import wait_for_control


def test_full_user_workflow(app):
    print("\n[STEP] Opening file")
    load_test_file(app)

    print("[STEP] Expanding tree")
    #root = expand_first_tree_node(app)
    root = select_tree_path(app, ["System Directory", "Security Directory"])

    print("[STEP] Selecting list item")
    lst = select_list_item_by_text(app, "Ethernet Host Security Level")

    print("[STEP] Validating results")
    assert root is not None
    assert lst.get_selected_count() == 1
