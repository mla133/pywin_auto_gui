from controls.common_controls import get_list, get_tree, get_list_row_texts
from controls.ribbon_controls import is_ribbon_button_enabled, click_ribbon_button
from pywinauto.keyboard import send_keys
from pywinauto import Application
import time
from datetime import datetime
import os

# "Edit Program Code Data" is the modal dialog opened by double-clicking a
# SysListView32 row in a config directory view (e.g. "Number of Load Arms"
# under System Layout) - distinct from the F2-inline-edit pattern used by
# edit_value()/edit_dropdown_value() for plain listview cells. Its controls
# are discovered via automation_id (win32 dialog control ids are stable
# across runs, unlike UIA control_type/title which are ambiguous here - the
# dialog has two Edit/ComboBox pairs, "Current" (read-only) and "New"
# (editable), both with empty window_text()).
_EDIT_DIALOG_TITLE = "Edit Program Code Data"
_EDIT_DIALOG_CLASS = "#32770"
_EDIT_DIALOG_NEW_VALUE_AUTO_ID = "1006"
_EDIT_DIALOG_SECURITY_LEVEL_AUTO_ID = "1010"
_EDIT_DIALOG_OK_AUTO_ID = "1"


def auto_step(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        step_name = func.__name__
        self._auto_screenshot(step_name)

        return result

    return wrapper


class MainPage:
    def __init__(self, app, request=None):
        self.app = app
        self.test_name = getattr(app, "test_name", "unknown_test")
        self._step_counter = 0

        print(f"[DEBUG] Page created, has request: {hasattr(app, 'request')}")

    def _auto_screenshot(self, step_name):
        try:
            time.sleep(0.3)

            win = self.app.app.top_window()

            base_dir = "screenshots"
            os.makedirs(base_dir, exist_ok=True)

            # group by test
            test_dir = os.path.join(base_dir, self.test_name)
            os.makedirs(test_dir, exist_ok=True)

            # increment step counter
            self._step_counter += 1

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self._step_counter:02d}_{step_name}_{timestamp}.png"

            path = os.path.join(test_dir, filename)

            img = win.capture_as_image()

            if img:
                img.save(path)
                print(f"[INFO] Auto-screenshot saved: {path}")

        except Exception as e:
            print(f"[ERROR] Exception during auto-screenshot: {e}")

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

    @auto_step
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

    @auto_step
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


    @auto_step
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

    @auto_step
    def get_value(self, target_text):
        lst = get_list(self.app)
        for i in range(lst.item_count()):
            row = get_list_row_texts(lst, i)
            
            if any(target_text in t for t in row):
                print(f"[INFO] Found '{target_text}' at row {i}, value: '{row[2]}'")
                return row[2]

        raise RuntimeError(f"{target_text} not found")



    @auto_step
    @auto_step
    def set_dropdown_value_by_typeahead(self, target_text, first_letter):
        """
        Edit a listview row's in-place dropdown value using type-ahead
        selection rather than the fragile relative-{UP}/{DOWN}-only
        navigation in edit_dropdown_value() (which only knows fixed
        mappings for two "Security Level" options). Opens the dropdown the
        same way (double-click the value cell, {DOWN} to open it), then
        types `first_letter` - standard Win32 combo/listbox controls jump to
        the first item starting with that letter - and commits with
        {ENTER}/{TAB}. Only safe to use when `first_letter` unambiguously
        identifies the desired option (e.g. "n" for a single "Not Used"
        entry in the option list) - confirmed live for Recipe Directory's
        "Recipe Used" field ("Load Arm 1".."Load Arm 6", "Not Used").
        """
        lst = get_list(self.app)

        row_index = None
        for i in range(lst.item_count()):
            row = get_list_row_texts(lst, i)
            if any(target_text in t for t in row):
                row_index = i
                break

        if row_index is None:
            raise RuntimeError(f"{target_text} not found")

        item = lst.get_item(row_index)
        item.select()

        rect = item.rectangle()
        x = rect.left + 250
        y = rect.top + rect.height() // 2
        lst.click_input(coords=(x, y))
        lst.click_input(coords=(x, y), double=True)
        time.sleep(0.3)

        send_keys("{DOWN}")
        time.sleep(0.2)
        send_keys(first_letter)
        time.sleep(0.3)
        send_keys("{ENTER}")
        time.sleep(0.3)
        send_keys("{TAB}")
        time.sleep(0.5)

        print(f"[INFO] Set '{target_text}' via type-ahead '{first_letter}'")
        return row_index

    @auto_step
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

    @auto_step
    def open_program_code_data_dialog(self, target_text):
        """
        Double-click a config directory row (e.g. "HM Class Product") to
        open the "Edit Program Code Data" dialog WITHOUT editing/closing it
        - used by context-help tests (A17) that need to click the dialog's
        own "Help" button rather than set a value. Returns the dialog's
        win32 wrapper; callers are responsible for closing it (e.g. via
        Cancel, automation_id "2").
        """
        lst = get_list(self.app)

        row_index = None
        for i in range(lst.item_count()):
            row = get_list_row_texts(lst, i)
            if any(target_text in t for t in row):
                row_index = i
                break

        if row_index is None:
            raise RuntimeError(f"{target_text} not found")

        print(f"[INFO] Opening 'Edit Program Code Data' dialog for row {row_index}")

        item = lst.get_item(row_index)
        item.select()

        rect = item.rectangle()
        VALUE_COLUMN_X_OFFSET = 250
        x = rect.left + VALUE_COLUMN_X_OFFSET
        y = rect.top + rect.height() // 2

        lst.click_input(coords=(x, y))
        lst.click_input(coords=(x, y), double=True)

        dlg_spec = self.app.app.window(title=_EDIT_DIALOG_TITLE, class_name=_EDIT_DIALOG_CLASS)
        dlg_spec.wait("exists visible ready", timeout=10)

        return dlg_spec.wrapper_object()

    @auto_step
    def edit_program_code_data(self, target_text, new_value, security_level=None):
        """
        Double-click a config directory row (e.g. "Number of Load Arms") to
        open the "Edit Program Code Data" dialog, set its "New" value, and
        optionally its Security Level, then OK the dialog.

        Returns the row index that was edited. Raises RuntimeError if the
        dialog never appears (e.g. this row uses the plain inline-edit
        pattern instead - see edit_value()).
        """
        lst = get_list(self.app)

        row_index = None
        for i in range(lst.item_count()):
            row = get_list_row_texts(lst, i)
            if any(target_text in t for t in row):
                row_index = i
                break

        if row_index is None:
            raise RuntimeError(f"{target_text} not found")

        print(f"[INFO] Opening 'Edit Program Code Data' dialog for row {row_index}")

        item = lst.get_item(row_index)
        item.select()

        rect = item.rectangle()
        VALUE_COLUMN_X_OFFSET = 250
        x = rect.left + VALUE_COLUMN_X_OFFSET
        y = rect.top + rect.height() // 2

        lst.click_input(coords=(x, y))
        lst.click_input(coords=(x, y), double=True)

        dlg_spec = self.app.app.window(title=_EDIT_DIALOG_TITLE, class_name=_EDIT_DIALOG_CLASS)
        dlg_spec.wait("exists visible ready", timeout=10)

        hwnd = dlg_spec.wrapper_object().handle
        uia_app = Application(backend="uia").connect(handle=hwnd)
        uia_dlg = uia_app.window(handle=hwnd)

        new_value_edit = uia_dlg.child_window(auto_id=_EDIT_DIALOG_NEW_VALUE_AUTO_ID, control_type="Edit")
        if not new_value_edit.exists():
            raise RuntimeError("'New' value edit control not found in Edit Program Code Data dialog")

        new_value_edit.set_edit_text(str(new_value))

        if security_level is not None:
            level_combo = uia_dlg.child_window(auto_id=_EDIT_DIALOG_SECURITY_LEVEL_AUTO_ID, control_type="ComboBox")
            if not level_combo.exists():
                raise RuntimeError("Security Level combo box not found in Edit Program Code Data dialog")
            level_combo.select(security_level)

        print(f"[INFO] Setting '{target_text}' New value to '{new_value}'")
        uia_dlg.child_window(auto_id=_EDIT_DIALOG_OK_AUTO_ID, control_type="Button").click_input()

        time.sleep(0.5)

        return row_index

    def is_ribbon_enabled(self, button_name):
        uia_win = self.app.get_uia_window()
        return is_ribbon_button_enabled(uia_win, button_name)

    @auto_step
    def click_ribbon(self, button_name):
        uia_win = self.app.get_uia_window()
        click_ribbon_button(uia_win, button_name)
