# pywin_auto_gui

A Python-based UI automation test framework for Win32/MFC applications using **pywinauto** and **pytest**.

This project demonstrates a clean, maintainable approach to automating legacy Windows desktop applications.

---

# 🚀 Features

- Automates Win32/MFC UI using `pywinauto`
- Structured architecture (App → Controls → Pages → Workflows → Tests)
- Robust window handling and synchronization
- Tree navigation and ListView interaction
- Pytest-based test execution
- Automatic teardown (no orphan processes)
- Screenshot capture before teardown

---

# 📁 Project Structure

```
pywin_auto_gui/
│
├── app/                  # Application lifecycle + window handling
│   └── application.py
│
├── controls/             # Low-level UI control helpers
│   └── common_controls.py
│
├── pages/                # Page object models
│   └── main_page.py
│
├── workflows/            # High-level user workflows
│   └── file_workflows.py
│
├── tests/                # Pytest tests
│   └── test_e2e.py
│
├── screenshots/          # Screenshots captured during tests
│
├── conftest.py           # Pytest fixtures (setup/teardown)
├── pytest.ini            # Pytest configuration
└── README.md
```

---

# 🛠️ Requirements

## ✅ Python

- Python 3.10+ (recommended)

⚠️ If automating a 32-bit application, consider using **32-bit Python** for better compatibility.

---

## ✅ Dependencies

Install required packages:

```bash
pip install pywinauto pytest Pillow
```

---

# ▶️ Running Tests

From the project root:

```bash
pytest -s -v
```

---

# 🧪 Example Test

```python
def test_full_user_workflow(app):
    from workflows.file_workflows import load_test_file
    from pages.main_page import MainPage

    load_test_file(app)

    page = MainPage(app)

    page.select_tree_path(["System Directory", "Security Directory"])
    row_index = page.select_list_item("Ethernet Host Security Level")

    assert row_index is not None
```

---

# 📸 Screenshots

Screenshots are taken automatically before teardown and stored in:

```
screenshots/
```

---

# 👍 Summary

✅ Clean architecture  
✅ Stable Win32 UI automation  
✅ Scalable pytest setup  
✅ Debug-friendly workflow  

---

Happy automating 🚀
