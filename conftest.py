import pytest
from utils import connect_app, get_main_window, wait_for_ui_ready
from utils import open_file_workflow

@pytest.fixture(scope="function")
def app():
    return connect_app()
