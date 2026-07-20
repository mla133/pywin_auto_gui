from workflows.file_workflows import new_config_file
from workflows.help_viewer import (
    open_help_topics,
    navigate_to_topic,
    get_current_page_url,
    close_help,
    get_context_help_window,
)
from pages.main_page import MainPage
from pywinauto import Application

# Topics under the "Using AccuMate" TOC root, and the .htm page each should
# load - confirmed via a live Help viewer session (the loaded page's
# mk:@MSITStore:...::/<page>.htm URL is exposed as a UIA Pane Name, the most
# reliable way to verify which page is displayed since the embedded
# Internet Explorer_Server content itself isn't practically readable via
# win32/UIA text automation).
_EDITOR_TOPICS = {
    "Using the Language Editor": "lang_editor.htm",
    "Using the Configurable Report Editor": "report_editor.htm",
    "Using the Equation Set Editor": "eqset_editor.htm",
    "Using the Database Editor": "database_editor.htm",
}

_EDIT_DIALOG_HELP_BUTTON_AUTO_ID = "1011"


def test_a16_calling_help(app):
    """
    A16: Calling Help - the ribbon "Help Topics" button opens the Help
    dialog, and each editor topic under "Using AccuMate" loads its
    corresponding help page.
    """
    help_win = open_help_topics(app)

    try:
        for topic_name in _EDITOR_TOPICS:
            navigate_to_topic(help_win, ["Using AccuMate", topic_name])

            url = get_current_page_url(help_win)
            print(f"[INFO] '{topic_name}' loaded: {url}")

            expected_page = _EDITOR_TOPICS[topic_name]
            assert expected_page in url, (
                f"Expected '{topic_name}' to load '{expected_page}', got: {url}"
            )
    finally:
        close_help(help_win)


def test_a17_calling_context_help(app):
    """
    A17: Calling Context Help - opening the "Edit Program Code Data" dialog
    for "HM Class Product" (Recipe Directory -> Recipe 01) and clicking its
    "Help" button displays the relevant help page for that parameter.
    """
    new_config_file(app)
    page = MainPage(app)

    page.select_tree_path(["Recipe Directory", "Recipe 01"])
    dlg = page.open_program_code_data_dialog("HM Class Product")

    try:
        uia_app = Application(backend="uia").connect(handle=dlg.handle)
        uia_dlg = uia_app.window(handle=dlg.handle)
        help_btn = uia_dlg.child_window(auto_id=_EDIT_DIALOG_HELP_BUTTON_AUTO_ID, control_type="Button")
        assert help_btn.exists(), "'Help' button not found in Edit Program Code Data dialog"

        print("[STEP] Clicking 'Help' button in Edit Program Code Data dialog")
        help_btn.click_input()

        help_win = get_context_help_window(timeout=8)
        try:
            url = get_current_page_url(help_win)
            print(f"[INFO] Context help loaded: {url}")
            assert "recipe" in url.lower(), (
                f"Expected a recipe-related context help page for 'HM Class Product', got: {url}"
            )
        finally:
            close_help(help_win)
    finally:
        # Dialog Cancel button, automation_id "2" (IDCANCEL).
        uia_app = Application(backend="uia").connect(handle=dlg.handle)
        uia_dlg = uia_app.window(handle=dlg.handle)
        uia_dlg.child_window(auto_id="2", control_type="Button").click_input()
