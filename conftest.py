import pytest
from app.application import AccuMateApp

@pytest.fixture(scope="function")
def app():
    """Fixture to create an instance of the AccuMateApp for testing."""

    app_instance = AccuMateApp()
    yield app_instance

    # Add any necessary cleanup code here if needed
    try:
        app_instance.app.kill()
        
    except Exception:
        pass
