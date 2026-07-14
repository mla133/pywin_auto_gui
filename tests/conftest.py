# conftest.py
#
# Ensures all pytest tests run inside a COM STA apartment.
# This prevents UIAutomation crashes such as:
#   0x80040155 (interface not registered)
#   0x8001010D (COM threading violation)
#
# Pywinauto's UIA backend *requires* STA threading.

import pytest
import pythoncom
import logging
import pywinauto

from pages.main_page import MainPage


@pytest.fixture
def page(app, request):
    return MainPage(app, request=request)


@pytest.fixture(autouse=True)
def ensure_sta_thread():
        # Initialize COM as STA for this thread
        pythoncom.CoInitialize()
        try:
            yield
        finally:
            # Clean up COM apartment
            pythoncom.CoUninitialize()

def pytest_configure():
    # Silence pywinauto UIA debug noise
    logger = logging.getLogger("pywinauto")
    logger.setLevel(logging.ERROR)
