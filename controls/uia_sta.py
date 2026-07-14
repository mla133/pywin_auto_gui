import pythoncom
import threading

def run_in_sta(func, *args, **kwargs):
    """Run a UIA function inside a dedicated STA thread."""

    result = {} 
    exception = {}

    def wrapper():
        pythoncom.CoInitialize()
        try:
            result["value"] = func(*args, **kwargs)
        except Exception as e:
            exception["error"] = e
        finally:
            pythoncom.CoUninitialize()

    t = threading.Thread(target=wrapper)
    t.start()
    t.join()

    if "error" in exception:
        raise exception["error"]

    return result.get("value")
