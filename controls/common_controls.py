import time


def wait_for_control(app_obj, class_name, timeout=10):
    start = time.time()

    while time.time() - start < timeout:
        win = app_obj.get_window()

        try:
            # win is already a resolved wrapper (not a WindowSpecification),
            # so child_window() isn't available here - scan descendants by
            # class name instead.
            matches = win.descendants(class_name=class_name)

            if matches:
                return matches[0]
        except Exception:
            pass

        time.sleep(0.3)

    raise TimeoutError(f"{class_name} not found")


def get_list(app_obj):
    return wait_for_control(app_obj, "SysListView32")


def get_tree(app_obj):
    return wait_for_control(app_obj, "SysTreeView32")


def get_list_row_texts(lst, row_index):
    col_count = lst.column_count()
    row = []

    for col in range(col_count):
        try:
            text = lst.get_item(row_index, col).text()
        except Exception:
            text = ""

        row.append(text)

    return row