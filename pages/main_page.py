from controls.common_controls import get_list, get_tree, get_list_row_texts
from pywinauto.keyboard import send_keys
import time
from datetime import datetime
import os

class MainPage:
    def __init__(self, app, request=None):
        self.app = app
        self.request = getattr(request, "request", None)  # Support both direct and fixture injection

    def screenshot(self, label):
        try:
            win = self.app.app.top_window()

            os.makedirs("screenshots", exist_ok=True)
            test_name = (
                    self.request.node.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
                    if self.request else "unknown_test"
                    )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_{label}_{timestamp}.png"
            path = f"screenshots/{filename}"

            img = win.capture_as_image()

            if img:
                img.save(path)
                print(f"[INFO] Screenshot saved: {path}")
            else:
                print("[WARN] Screenshot capture returned None")

        except Exception as e:
            print(f"[ERROR] Exception during screenshot: {e}")

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


    def edit_value(self, target_text, new_value):
        lst = get_list(self.app)

        # Step 1: find row
        row_index = None

        for i in range(lst.item_count()):
            row = get_list_row_texts(lst, i)

            if any(target_text in t for t in row):
                row_index = i
                break

        if row_index is None:
            raise RuntimeError(f"{target_text} not found")

        print(f"[INFO] Editing row {row_index}")

        # Step 2: select row
        item = lst.get_item(row_index)
        item.select()

        # Step 3: click VALUE column (column index 2)
        rect = item.rectangle()

        # Approximate column offsets (you may tweak slightly)
        VALUE_COLUMN_X_OFFSET = 250
        y = rect.top + rect.height() // 2
        x = rect.left + VALUE_COLUMN_X_OFFSET

        print(f"[DEBUG] Clicking value cell at ({x},{y})")

        lst.click_input(coords=(x, y))

        # Step 4: enter edit mode
        send_keys("{F2}")

        # Step 5: replace value
        send_keys("^a")  # select all
        send_keys(new_value)

        # Step 6: commit
        send_keys("{ENTER}")

        print(f"[INFO] Value updated to: {new_value}")

        return row_index

    def get_value(self, target_text):
        lst = get_list(self.app)
        for i in range(lst.item_count()):
            row = get_list_row_texts(lst, i)
            
            if any(target_text in t for t in row):
                print(f"[INFO] Found '{target_text}' at row {i}, value: '{row[2]}'")
                return row[2]

        raise RuntimeError(f"{target_text} not found")



    def edit_dropdown_value(self, target_text, target_option):
        lst = get_list(self.app)

        # Step 1: find and select row
        row_index = None
        for i in range(lst.item_count()):
            row = get_list_row_texts(lst, i)
            if any(target_text in t for t in row):
                row_index = i
                break

        print(f"[DEBUG] Searching for '{target_text}', found at row index: {row_index}")

        if row_index is None:
            raise RuntimeError(f"{target_text} not found")

        item = lst.get_item(row_index)
        item.select()

        # Step 2: click VALUE column
        rect = item.rectangle()
        x = rect.left + 250
        y = rect.top + rect.height() // 2
        lst.click_input(coords=(x, y))

        # double-click VALUE column -> activates actual editor
        lst.click_input(coords=(x, y), double=True)
        time.sleep(0.2)

        # Step 4: open dropdown
        print("[DEBUG] Opening dropdown")
        send_keys("{DOWN}")
        time.sleep(0.2)

        print("[DEBUG] Dropdown opened at current selection")

        # KEY CHANGE: only move relative to current value
        # (you already know you're starting at "Security Level 3")

        if target_option == "Security Level 2":
            send_keys("{UP}")
        elif target_option == "Security Level 4":
            send_keys("{DOWN}")
        else:
            print("[WARN] Unknown relative mapping, fallback needed")

        time.sleep(0.2)

        # Step 5: commit
        send_keys("{ENTER}")
        time.sleep(0.3)

        send_keys("{TAB}")
        time.sleep(0.2)

        print(f"[INFO] Selected dropdown value: {target_option}")

        return row_index
