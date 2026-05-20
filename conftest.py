import pytest
import subprocess
import os
from datetime import datetime
from app.application import AccuMateApp


@pytest.fixture(scope="function")
def app():
    app_instance = AccuMateApp()

    yield app_instance

    print("\n[DEBUG] Taking screenshot before teardown...")

    try:
        win = app_instance.get_window()

        # Generate a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/test_{timestamp}.png"

        # Ensure folder exists
        os.makedirs("screenshots", exist_ok=True)

        # Capture screenshot
        win.capture_as_image().save(screenshot_path)

        print(f"[DEBUG] Screenshot saved: {screenshot_path}")

    except Exception as e:
        print(f"[WARN] Screenshot failed: {e}")

    print("[DEBUG] Closing application...")

    try:
        pid = app_instance.get_window().process_id()

        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        print(f"[WARN] Failed to kill process: {e}")
