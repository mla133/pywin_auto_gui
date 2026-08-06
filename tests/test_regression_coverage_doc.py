"""
Guardrail against docs/regression-coverage.md drifting out of sync with
reality (see docs/regression-coverage.md's own header: "Regenerate/update
this whenever a scenario's status changes").

This is a pure documentation/text-parsing check - no app is launched, no
device is needed, and it runs as part of the default `pytest -s -v` suite
(no marker needed).

Two things are checked:
  1. Every scenario ID (h4. heading) in scenarios/regression.md has a
     corresponding row in docs/regression-coverage.md's status tables, and
     vice versa - so a newly added/removed/renumbered regression.md
     scenario can't silently go unreflected in the coverage doc.
  2. Every test function name referenced in a coverage-doc row (backtick-
     quoted, `test_...`) actually exists in the tests/ package - if a
     referenced file is named explicitly (`some_file.py::test_x`), the
     function must exist in that specific file; otherwise it just needs to
     exist somewhere under tests/ - so a renamed/removed/moved test can't
     silently leave a stale, broken reference in the docs.

This intentionally does NOT try to verify marker correctness (manual vs.
special_case vs. requires_device etc.) against the doc's Status column -
that's a much fuzzier text-matching problem and not worth the fragility;
the two checks above catch the two concrete, unambiguous failure modes
that actually matter (a missing/extra ID, a dead test reference).
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGRESSION_MD = _REPO_ROOT / "scenarios" / "regression.md"
_COVERAGE_MD = _REPO_ROOT / "docs" / "regression-coverage.md"
_TESTS_DIR = Path(__file__).resolve().parent

# Matches an "h4. <ID>[: | -]<title>" heading, capturing just the ID token.
# Handles both plain IDs ("h4. A1: Creating New Config Files") and ID
# ranges ("h4. H3 - H8:  Updated max values for Parameters") - the range
# half only matches if followed by another letter+digit token, so a
# dash-separated title (e.g. "h4. H9 - HMI B Failure...") doesn't get
# mistaken for a range.
_HEADING_ID_RE = re.compile(r"^h4\.\s*([A-Z]{1,3}\d+(?:\s*-\s*[A-Z]{0,3}\d+)?)\b")

# Matches the leading ID token in a coverage-doc table row's first cell,
# e.g. "A1", "H3-H8", or "G1 (uninstall-while-running)" (only the "G1" is
# captured - the parenthetical is a sub-case label, not a distinct
# regression.md scenario ID).
_ROW_ID_RE = re.compile(r"^([A-Z]{1,3}\d+(?:-[A-Z]{0,3}\d+)?)")

# Matches a backtick-quoted test reference in a coverage-doc row's Test
# column, optionally prefixed with an explicit "file.py::" - e.g.
# "`test_a1_creating_new_config_file`" or
# "`test_regression_config_files.py::test_a1_creating_new_config_file`".
_TEST_REF_RE = re.compile(r"`(?:([\w.]+\.py)::)?(test_[A-Za-z0-9_]+)`")

_DEF_TEST_RE = re.compile(r"^def (test_[A-Za-z0-9_]+)\(", re.MULTILINE)


def _parse_regression_scenario_ids():
    """All scenario ID tokens (whitespace-normalized) from regression.md's
    h4. headings, e.g. {"A1", ..., "H3-H8", "H9"}."""
    ids = set()
    for line in _REGRESSION_MD.read_text(encoding="utf-8").splitlines():
        m = _HEADING_ID_RE.match(line.strip())
        if m:
            ids.add(re.sub(r"\s+", "", m.group(1)))
    return ids


def _parse_coverage_table_rows():
    """All (base_id, test_column_text) pairs from every Markdown table row
    in docs/regression-coverage.md that starts with a real ID (skips
    header/separator rows and any non-table lines)."""
    rows = []
    for line in _COVERAGE_MD.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue

        id_cell, _title, _status, test_cell = cells[0], cells[1], cells[2], cells[3]
        m = _ROW_ID_RE.match(id_cell)
        if not m:
            continue  # header row ("ID"), separator row ("---"), etc.

        rows.append((m.group(1), test_cell))
    return rows


def _all_test_defs_by_file():
    """{filename: {test function names defined in it}} for every
    tests/*.py file."""
    defs_by_file = {}
    for f in _TESTS_DIR.glob("*.py"):
        defs_by_file[f.name] = set(_DEF_TEST_RE.findall(f.read_text(encoding="utf-8")))
    return defs_by_file


def test_every_regression_scenario_id_has_a_coverage_row():
    """
    Every scenario ID (or ID range, e.g. "H3-H8") in scenarios/regression.md
    must appear as a row in docs/regression-coverage.md, and every row in
    the coverage doc must correspond to a real scenario ID - catches a
    scenario being added/renumbered/removed in regression.md without the
    coverage doc being updated to match (or a stale row left behind after
    a renumbering).
    """
    regression_ids = _parse_regression_scenario_ids()
    coverage_ids = {base_id for base_id, _test_cell in _parse_coverage_table_rows()}

    missing_from_coverage_doc = regression_ids - coverage_ids
    stale_in_coverage_doc = coverage_ids - regression_ids

    assert not missing_from_coverage_doc, (
        f"scenarios/regression.md has scenario ID(s) with no row in "
        f"docs/regression-coverage.md: {sorted(missing_from_coverage_doc)} - "
        "add a status row for each (see docs/adding-a-test.md)."
    )
    assert not stale_in_coverage_doc, (
        f"docs/regression-coverage.md has row(s) for scenario ID(s) that no "
        f"longer exist in scenarios/regression.md: {sorted(stale_in_coverage_doc)} - "
        "remove or correct the stale row(s)."
    )


def test_coverage_doc_test_references_are_not_stale():
    """
    Every backtick-quoted `test_...` reference in docs/regression-coverage.md's
    Test column must resolve to a real test function - to a function
    actually defined in the named file when a file is given explicitly
    (`some_file.py::test_x`), or to a function defined *somewhere* under
    tests/ when no file is given - catches a referenced test being renamed,
    removed, or moved to a different file without the doc being updated.
    """
    defs_by_file = _all_test_defs_by_file()
    all_test_names = set().union(*defs_by_file.values()) if defs_by_file else set()

    broken_references = []

    for base_id, test_cell in _parse_coverage_table_rows():
        for file_name, func_name in _TEST_REF_RE.findall(test_cell):
            if file_name:
                if func_name not in defs_by_file.get(file_name, set()):
                    broken_references.append(
                        f"{base_id}: `{file_name}::{func_name}` - no such function in tests/{file_name}"
                    )
            elif func_name not in all_test_names:
                broken_references.append(
                    f"{base_id}: `{func_name}` - no test function with this name found anywhere under tests/"
                )

    assert not broken_references, (
        "docs/regression-coverage.md references test function(s) that no "
        "longer exist (renamed/removed/moved?):\n" + "\n".join(broken_references)
    )
