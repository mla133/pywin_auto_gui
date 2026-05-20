from pywinauto import Application
import time

APP_TITLE = "AccuMate for AccuLoad"
APP_EXE = r"C:\\Users\\allenma\\SoftwareDevelopment\\acculoadiv.AccuMate\\Release\\AccuMate.exe"
BACKEND = "win32"


class AccuMateApp:
    def __init__(self):
        self.app = Application(backend=BACKEND).start(APP_EXE)

    def get_window(self):
        """
        Resolve the correct active window.
        """
        for _ in range(10):
            windows = self.app.windows()

            for w in windows:
                try:
                    title = w.window_text()

                    if title and ".AL4" in title and "AccuMate" in title:
                        print(f"[DEBUG] Candidate window: '{title}'")
                        handle = w.handle
                        win = self.app.window(handle=handle)
                        win.wait("exists enabled visible ready", timeout=5)

                        print(f"[DEBUG] Using document window: '{title}'")
                        return win

                except Exception:
                    continue

            # fallback
            try:
                win = self.app.window(title_re=".*AccuMate.*")
                if win.exists():
                    print("[DEBUG] Falling back to main window")
                    win.wait("exists enabled visible ready", timeout=5)
                    return win
            except Exception:
                pass

            time.sleep(0.5)

        raise RuntimeError("Could not resolve main window")
