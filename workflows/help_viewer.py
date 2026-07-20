import time

from pywinauto import Application, Desktop

from controls.ribbon_controls import click_ribbon_button

# AccuMate's Help is a standard compiled HTML Help (.chm) viewer, opened
# in-process (same PID as AccuMate itself, not a separate hh.exe process in
# this build) via the ribbon's "Help Topics" button (top-right corner) or a
# dialog's "Help" button (context help). Its top-level window has the fixed
# class name "HH Parent" - confirmed via a live win32 Desktop scan.
_HELP_TOPICS_BUTTON = "Help Topics"
_HELP_WINDOW_CLASS = "HH Parent"


def _find_help_window(timeout=6):
    """Poll the desktop for the "HH Parent" Help viewer top-level window."""
    start = time.time()

    while time.time() - start < timeout:
        for w in Desktop(backend="win32").windows():
            try:
                if w.class_name() == _HELP_WINDOW_CLASS:
                    return w
            except Exception:
                continue
        time.sleep(0.3)

    return None


def open_help_topics(app_obj, retries=3, timeout=6):
    """
    Open the Help viewer via the ribbon "Help Topics" button (A16). Retries
    the ribbon click a few times, since - like other ribbon-triggered UI in
    this codebase - the first click can be missed.

    Returns a win32 wrapper for the Help viewer's top-level window.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            uia_win = app_obj.get_uia_window()
            print(f"[STEP] Opening Help Topics (attempt {attempt}/{retries})")
            click_ribbon_button(uia_win, _HELP_TOPICS_BUTTON)

            help_desktop_win = _find_help_window(timeout=timeout)
            if help_desktop_win is not None:
                help_app = Application(backend="win32").connect(handle=help_desktop_win.handle)
                return help_app.window(handle=help_desktop_win.handle).wrapper_object()

            raise RuntimeError("Help viewer ('HH Parent') window did not appear in time")
        except Exception as e:
            last_error = e
            print(f"[WARN] Attempt {attempt}/{retries} to open Help Topics failed: {e}")
            time.sleep(1)

    raise RuntimeError(f"Failed to open Help Topics after {retries} attempts") from last_error


def get_context_help_window(timeout=6):
    """
    Attach to an already-open Help viewer window that was triggered as
    context help from a dialog's "Help" button (A17), rather than via the
    ribbon "Help Topics" button. Polls the same way as open_help_topics.
    """
    help_desktop_win = _find_help_window(timeout=timeout)
    if help_desktop_win is None:
        raise RuntimeError("Help viewer ('HH Parent') window did not appear in time")

    help_app = Application(backend="win32").connect(handle=help_desktop_win.handle)
    return help_app.window(handle=help_desktop_win.handle).wrapper_object()


def get_toc_tree(help_win):
    """Return the Contents tab's TOC SysTreeView32 wrapper."""
    for ctrl in help_win.descendants():
        if ctrl.class_name() == "SysTreeView32":
            return ctrl

    raise RuntimeError("Help viewer TOC tree (SysTreeView32) not found")


def navigate_to_topic(help_win, topic_path):
    """
    Navigate the Help viewer's Contents tree to a topic, given a path of
    node texts from a root TOC entry down to the target leaf, e.g.
    ["Using AccuMate", "Using the Language Editor"]. Expands each
    intermediate node and clicks the final one to load its page.
    """
    tree = get_toc_tree(help_win)

    roots = tree.roots()
    node = next((r for r in roots if r.text() == topic_path[0]), None)
    if node is None:
        raise RuntimeError(f"TOC root '{topic_path[0]}' not found")

    for name in topic_path[1:]:
        node.expand()
        time.sleep(0.3)
        children = node.children()
        match = next((c for c in children if c.text() == name), None)
        if match is None:
            raise RuntimeError(f"TOC child '{name}' not found under '{node.text()}'")
        node = match

    print(f"[STEP] Clicking Help TOC topic: {' -> '.join(topic_path)}")
    node.click_input()
    time.sleep(1.0)


def get_current_page_url(help_win, timeout=5):
    """
    Return the mk:@MSITStore:...::/<page>.htm URL of the currently
    displayed Help page - the most reliable way to confirm which page
    loaded, since the embedded Internet Explorer_Server content itself
    isn't practically readable via win32/UIA text automation, but the
    hosting Pane's UIA Name exposes this URL directly.
    """
    help_uia_app = Application(backend="uia").connect(handle=help_win.handle)
    help_uia_win = help_uia_app.window(handle=help_win.handle).wrapper_object()

    start = time.time()
    while time.time() - start < timeout:
        for ctrl in help_uia_win.descendants():
            try:
                if ctrl.element_info.control_type != "Pane":
                    continue
                name = ctrl.window_text()
                if name and "MSITStore" in name:
                    return name
            except Exception:
                continue
        time.sleep(0.3)

    raise RuntimeError("Could not read the current Help page URL")


def close_help(help_win):
    help_win.close()
