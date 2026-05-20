from workflows import load_test_file, select_first_list_item, expand_first_tree_node
from utils import wait_for_control


def test_full_user_workflow(app):
    print("[STEP] Opening file")
    load_test_file(app)

    print("[STEP] Expanding tree")
    root = expand_first_tree_node(app)

    print("[STEP] Selecting list item")
    lst = select_first_list_item(app)

    print("[STEP] Validating results")
    assert root is not None
    assert lst.get_selected_count() == 1
