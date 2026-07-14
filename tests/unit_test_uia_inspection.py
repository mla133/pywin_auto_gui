from controls.debug_tools import safe_dump_control

def test_uia_ribbon_inspection(app):
    print("[STEP] Getting UIA window")
    win = app.get_uia_window()

    candidates = [
        "Document Options",
        "General Options",
        "Retry Comm",
        "Go Offline"
    ]

    results = {}

    for name in candidates:
        print(f"[STEP] Inspecting '{name}'")
        info = safe_dump_control(win, name)
        print("[INFO]", info)
        results[name] = info

    found = {name: info for name, info in results.items() if not info.get("error")}

    assert found, f"None of the candidate ribbon controls were found: {results}"
