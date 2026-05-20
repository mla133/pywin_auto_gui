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

#def select_list_item_by_text(app, target_text):
#    lst = get_list(app)
#
#    item_count = lst.item_count()
#
#    for i in range(item_count):
#        item = lst.get_item(i)
#        texts = item.texts()
#
#        print(f"[DEBUG] Row {i}: {texts}")
#
#        if any(target_text in t for t in texts):
#            print(f"[INFO] Match found at row {i}")
#            lst.select(i)
#            return lst
#
#    raise RuntimeError(f"Item with text '{target_text}' not found in the list.")

def select_list_item_by_text(app, target_text):
    lst = get_list(app)

    item_count = lst.item_count()
    col_count = lst.column_count()

    for i in range(item_count):
        row_texts = []

        for col in range(col_count):
            try:
                cell_text = lst.get_item(i, col).text()
            except Exception:
                cell_text = ""

            row_texts.append(cell_text)

        print(f"[DEBUG] Row {i}: {row_texts}")

        if any(target_text in t for t in row_texts):
            print(f"[INFO] Match found at row {i}")
            lst.select(i)
            return lst

    raise RuntimeError(f"Item with text '{target_text}' not found in the list.")

def expand_first_tree_node(app):
    tree = get_tree(app)
    root = tree.roots()[0]
    root.expand()
    return root

def select_tree_path(app, path):
    """
    Navigate and select a tree path.

    Example path:
        ["System Directory", "Security Directory"]
    """
    tree = get_tree(app)

    # Start from all roots
    nodes = tree.roots()

    current = None

    for level, name in enumerate(path):
        found = None

        if level == 0:
            search_space = nodes
        else:
            search_space = current.children()

        for node in search_space:
            text = node.text()
            print(f"[DEBUG] Tree node: '{text}'")

            if name in text:
                found = node
                break

        if not found:
            raise RuntimeError(f"Tree node '{name}' not found")

        found.expand()
        current = found

    current.select()
    print(f"[INFO] Selected tree path: {path}")

    return current
