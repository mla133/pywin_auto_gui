from controls.common_controls import get_list, get_tree, get_list_row_texts


class MainPage:
    def __init__(self, app):
        self.app = app

    def select_tree_path(self, path):
        tree = get_tree(self.app)

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

    def select_list_item(self, target_text):
        lst = get_list(self.app)

        for i in range(lst.item_count()):
            row_texts = get_list_row_texts(lst, i)

            print(f"[DEBUG] Row {i}: {row_texts}")

            if any(target_text in t for t in row_texts):
                print(f"[INFO] Match found at row {i}")
                lst.get_item(i).select()
                return i

        raise RuntimeError(f"Item with text '{target_text}' not found")