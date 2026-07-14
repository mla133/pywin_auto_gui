"""
Tests for scenario_runner.py's Markdown parsing and step-matching logic.

These are pure parsing/regex tests - no real AccuMate instance is launched,
so unlike the app-driving tests under tests/, this one is collected by
default (matches pytest.ini's python_files = test_*.py).
"""
import os
import tempfile

import pytest

import scenario_runner as sr


def _write_markdown(tmp_path, content):
    path = os.path.join(tmp_path, "scenario.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def test_parse_scenario_markdown_extracts_bullet_items(tmp_path):
    content = """# Title

Some narration paragraph explaining the scenario - not a step.

- First bullet step
* Second bullet step (asterisk style)
1. First numbered step
2) Second numbered step (paren style)
"""
    path = _write_markdown(tmp_path, content)
    steps = sr.parse_scenario_markdown(path)

    assert steps == [
        "First bullet step",
        "Second bullet step (asterisk style)",
        "First numbered step",
        "Second numbered step (paren style)",
    ]


def test_parse_scenario_markdown_ignores_headers_blanks_and_code_blocks(tmp_path):
    content = """# Heading one
## Heading two

- Load the test file

```
this looks like a step but is inside a code fence
- fake step
```

- Wait 1 seconds
"""
    path = _write_markdown(tmp_path, content)
    steps = sr.parse_scenario_markdown(path)

    assert steps == ["Load the test file", "Wait 1 seconds"]


def test_parse_scenario_markdown_ignores_plain_paragraph_narration(tmp_path):
    content = (
        "# Just a title\n\n"
        "This paragraph explains why the scenario exists, but is not a step.\n"
    )
    path = _write_markdown(tmp_path, content)
    steps = sr.parse_scenario_markdown(path)

    assert steps == []


@pytest.mark.parametrize(
    "step_text,expected_handler,expected_groups",
    [
        ("Load the test file", sr._step_load_test_file, ()),
        ("load test file", sr._step_load_test_file, ()),
        (
            r"Load the config file at C:\path\DefaultAL4.dat",
            sr._step_load_config_file,
            (r"C:\path\DefaultAL4.dat",),
        ),
        ("Connect to 10.55.66.70", sr._step_connect_to_ip, ("10.55.66.70",)),
        ("connect to the device at 10.55.66.70", sr._step_connect_to_ip, ("10.55.66.70",)),
        (r"Save as C:\out\test1.al4", sr._step_save_as, (r"C:\out\test1.al4",)),
        (r"Save the file as C:\out\test1.al4", sr._step_save_as, (r"C:\out\test1.al4",)),
        ("Enter passcode 1234", sr._step_enter_passcode, ("1234",)),
        ("Verify that the device is connected", sr._step_assert_connected, ()),
        ("check device is connected", sr._step_assert_connected, ()),
        ("Verify device is offline", sr._step_assert_disconnected, ()),
        ("Wait 2 seconds", sr._step_wait, ("2",)),
        ("Wait 1.5 seconds", sr._step_wait, ("1.5",)),
        ("Click the Retry Comm button", sr._step_click_ribbon, ("Retry Comm",)),
        ("Click Document Options", sr._step_click_ribbon, ("Document Options",)),
    ],
)
def test_match_step_recognizes_expected_patterns(step_text, expected_handler, expected_groups):
    handler, m = sr.match_step(step_text)

    assert handler is expected_handler
    assert m is not None
    assert m.groups() == expected_groups


def test_match_step_returns_none_for_unrecognized_text():
    handler, m = sr.match_step("do a barrel roll")

    assert handler is None
    assert m is None


def test_select_tree_path_splits_on_separators():
    handler, m = sr.match_step("Select tree path Setup > Communications > IP Address")

    assert handler is sr._step_select_tree_path
    assert m.group(1) == "Setup > Communications > IP Address"
