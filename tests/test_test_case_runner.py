"""
Tests for test_case_runner.py's wiki-markup test-case document parser and
whole-step pattern matching.

These are pure parsing/regex tests against the real
scenarios/ALIV-3929.md fixture - no AccuMate instance is launched, so this
is collected by default (matches pytest.ini's python_files = test_*.py).
"""
import os

import test_case_runner as tcr

ALIV_3929_PATH = os.path.join(os.path.dirname(__file__), "..", "scenarios", "ALIV-3929.md")


def test_parse_test_case_document_skips_preamble_before_first_h4():
    sections = tcr.parse_test_case_document(ALIV_3929_PATH)

    # The h3. title, notes, and the settings-value numbered list all sit
    # before the first "h4." section and must not be parsed as steps.
    assert sections[0].title == "Testing Parameter Security Passcode Access"
    assert sections[0].steps[0].number == 1
    assert sections[0].steps[0].text == "Start the Accumate Application."


def test_parse_test_case_document_finds_all_sections_in_order():
    sections = tcr.parse_test_case_document(ALIV_3929_PATH)

    titles = [s.title for s in sections]
    assert titles == [
        "Testing Parameter Security Passcode Access",
        "Testing Logging Out Effects",
        "Testing Ethernet Host Security Level",
        "Testing Serial Host Security Level",
        "Testing Whitelisted IP parameters",
        "Testing Dump Selected/Dump All functionality",
        "Testing Communications Security Timeout functionality",
        "Testing Firmware Upgrade",
        "Firmware Upgrades with whitelisted IPs",
    ]


def test_parse_test_case_document_extracts_expected_result_and_strips_markup():
    sections = tcr.parse_test_case_document(ALIV_3929_PATH)
    step1 = sections[0].steps[0]

    assert step1.expected_result == "The application will open to a blank view."
    # Wiki italics (_..._) and the trailing *[PASS/FAIL]* marker must both
    # be stripped from the cleaned expected_result text.
    assert "_" not in step1.expected_result
    assert "PASS/FAIL" not in step1.expected_result


def test_parse_test_case_document_step_without_expected_result_is_none():
    sections = tcr.parse_test_case_document(ALIV_3929_PATH)
    whitelisted_section = next(s for s in sections if s.title == "Testing Whitelisted IP parameters")

    # Step 1 in this section has no "Expected Result:" line in the source doc.
    assert whitelisted_section.steps[0].expected_result is None


def test_parse_test_case_document_step_numbers_are_sequential_per_section():
    sections = tcr.parse_test_case_document(ALIV_3929_PATH)

    for section in sections:
        numbers = [s.number for s in section.steps]
        assert numbers == list(range(1, len(numbers) + 1)), f"{section.title}: {numbers}"


def test_split_into_clauses_separates_compound_sentences():
    text = (
        "Enter the passcode for security level 1. Verify that a popup indicating "
        '"Incorrect security level for this parameter." is displayed. '
        'Verify after clicking "OK" that the parameter was not changed.'
    )
    clauses = tcr.split_into_clauses(text)

    assert clauses[0] == "Enter the passcode for security level 1."
    assert clauses[-1] == 'Verify after clicking "OK" that the parameter was not changed.'
    # The period inside the quoted phrase, followed by lowercase "is", must
    # not cause a spurious split.
    assert not any(c.startswith("is displayed") for c in clauses)


def test_match_testcase_step_recognizes_start_application():
    handler, m = tcr.match_testcase_step("Start the Accumate Application.", base_dir=".")

    assert handler is not None


def test_match_testcase_step_recognizes_load_test_configuration_file():
    handler, m = tcr.match_testcase_step('Load test configuration file "ALIV-3929.AL4" file.', base_dir=".")

    assert handler is not None
    assert m.group(1) == "ALIV-3929.AL4"


def test_resolve_config_path_prefers_configs_directory_when_file_exists():
    # configs/ALIV-3929.AL4 is a real fixture committed for this test case.
    resolved = tcr._resolve_config_path("ALIV-3929.AL4", base_dir="/some/scenarios/dir")

    assert resolved == os.path.join(tcr._CONFIGS_DIR, "ALIV-3929.AL4")
    assert os.path.isfile(resolved)


def test_resolve_config_path_falls_back_to_base_dir_when_not_in_configs():
    resolved = tcr._resolve_config_path("DoesNotExistAnywhere.AL4", base_dir="/some/scenarios/dir")

    assert resolved == os.path.join("/some/scenarios/dir", "DoesNotExistAnywhere.AL4")


def test_resolve_config_path_leaves_explicit_directory_untouched():
    resolved = tcr._resolve_config_path(r"C:\explicit\path\Foo.AL4", base_dir="/some/scenarios/dir")

    assert resolved == r"C:\explicit\path\Foo.AL4"


def test_match_testcase_step_falls_back_to_scenario_runner_grammar():
    # "Wait N seconds" is only defined in scenario_runner's general grammar,
    # not in test_case_runner's curated patterns - confirms the fallback works.
    handler, m = tcr.match_testcase_step("Wait 5 seconds", base_dir=".")

    assert handler is not None


def test_match_testcase_step_returns_none_for_compound_manual_step():
    sections = tcr.parse_test_case_document(ALIV_3929_PATH)
    compound_step = sections[0].steps[3]  # step 4: navigate + click ribbon button

    handler, m = tcr.match_testcase_step(compound_step.text, base_dir=".")

    assert handler is None


def test_match_testcase_step_does_not_false_positive_on_messy_click_prose():
    # Regression test: scenario_runner's generic "click <name>" catch-all is
    # too loose for compound prose and previously let filler words slip into
    # the captured button name (e.g. "on the 'Open' button in the top left
    # corner of the application" was captured as a literal ribbon button
    # name and a wrong auto-click was attempted). This phrasing must fall
    # back to a manual step instead.
    handler, m = tcr.match_testcase_step(
        'Click on the "Open" button in the top left corner of the application.',
        base_dir=".",
    )

    assert handler is None


def test_match_testcase_step_does_not_false_positive_on_change_to_prose():
    # Regression test: scenario_runner's "change/set X to Y" pattern's
    # non-greedy-but-end-anchored capture previously swallowed an entire
    # trailing compound sentence as the "value" (e.g. real step 4 of
    # "Testing Dump Selected/Dump All functionality" - "Change Security
    # Directory -> Ethernet Host Security Level to 'No Security'.  Confirm
    # the AccuLoad updated the parameter.  Go offline with AccuMate, then
    # Retry Comm to reconnect.  Attempt to push the selected Security
    # Directory -> Security Directory again." - matched as one edit_value
    # call and failed with "SysListView32 not found" instead of correctly
    # falling back to a manual step.
    sections = tcr.parse_test_case_document(ALIV_3929_PATH)
    dump_section = next(s for s in sections if s.title == "Testing Dump Selected/Dump All functionality")
    compound_step = dump_section.steps[3]  # step 4

    handler, m = tcr.match_testcase_step(compound_step.text, base_dir=".")

    assert handler is None
