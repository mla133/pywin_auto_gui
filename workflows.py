from utils import open_file_dialog, wait_for_control, wait_for_ui_ready

TEST_FILE = r"C:\Users\allenma\Documents\AccuMate Files\Kitchen_Sink-1_12.AL4"

def load_test_file(app):
    open_file_dialog(app, TEST_FILE)


def get_list(app):
    return wait_for_control(app, "SysListView32").wrapper_object()


def get_tree(app):
    return wait_for_control(app, "SysTreeView32").wrapper_object()


def select_first_list_item(app):
    lst = get_list(app)
    lst.select(0)
    return lst


def expand_first_tree_node(app):
    tree = get_tree(app)
    root = tree.roots()[0]
    root.expand()
    return root
