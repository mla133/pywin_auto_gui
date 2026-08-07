"""
Unit tests for reporting/pdf_report.py's PDF generation, independent of any
live pytest run/app/device - feeds hand-built TestResult objects (and, for
the screenshot-embedding case, a small real fixture PNG) into
build_pdf_report() and checks a valid, non-empty PDF is produced.

These run by default (no special marker) since they're fast and need no
live app - keeps the reporting code itself covered even though the
--pdf-report CLI flag is opt-in for real regression runs.
"""
import os

from PIL import Image as PILImage
from pypdf import PdfReader

from reporting.pdf_report import StepResult, TestResult, build_pdf_report


def _make_fixture_screenshot(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = PILImage.new("RGB", (320, 200), color=(120, 160, 200))
    img.save(path)


def test_build_pdf_report_creates_valid_pdf(tmp_path):
    results = [
        TestResult(
            nodeid="tests/test_example.py::test_a",
            name="test_a",
            outcome="passed",
            duration=1.23,
            docstring="A1: Example passing test.",
            markers=["requires_device"],
        ),
        TestResult(
            nodeid="tests/test_example.py::test_b",
            name="test_b",
            outcome="failed",
            duration=4.56,
            docstring="A2: Example failing test.",
            markers=[],
            longrepr="AssertionError: expected True, got False\n  at line 42",
        ),
        TestResult(
            nodeid="tests/test_example.py::test_c",
            name="test_c",
            outcome="skipped",
            duration=0.01,
            docstring="A3: Example skipped test (device unreachable).",
            markers=["requires_device", "needs_live_verification"],
        ),
    ]

    output_path = str(tmp_path / "report.pdf")
    returned_path = build_pdf_report(results, output_path)

    assert returned_path == output_path
    assert os.path.isfile(output_path)
    assert os.path.getsize(output_path) > 0

    with open(output_path, "rb") as pdf_file:
        assert pdf_file.read(5) == b"%PDF-"

    reader = PdfReader(output_path)
    # At least a summary page plus one detail page per test.
    assert len(reader.pages) >= 1 + len(results)


def test_build_pdf_report_embeds_screenshots(tmp_path):
    screenshot_dir = str(tmp_path / "screenshots" / "test_with_shots")
    _make_fixture_screenshot(os.path.join(screenshot_dir, "01_step_one_20260101_000000.png"))
    _make_fixture_screenshot(os.path.join(screenshot_dir, "02_step_two_20260101_000001.png"))

    results = [
        TestResult(
            nodeid="tests/test_example.py::test_with_shots",
            name="test_with_shots",
            outcome="passed",
            duration=2.0,
            docstring="Example test with captured screenshots.",
            screenshot_dir=screenshot_dir,
        ),
    ]

    output_path = str(tmp_path / "report_with_shots.pdf")
    build_pdf_report(results, output_path)

    assert os.path.isfile(output_path)
    reader = PdfReader(output_path)
    assert len(reader.pages) >= 2


def test_build_pdf_report_handles_missing_screenshot_dir(tmp_path):
    results = [
        TestResult(
            nodeid="tests/test_example.py::test_no_shots",
            name="test_no_shots",
            outcome="passed",
            duration=0.5,
            docstring="Example test with no screenshots directory at all.",
            screenshot_dir=str(tmp_path / "screenshots" / "does_not_exist"),
        ),
    ]

    output_path = str(tmp_path / "report_no_shots.pdf")
    # Should not raise even though the screenshot_dir doesn't exist.
    build_pdf_report(results, output_path)

    assert os.path.isfile(output_path)


def test_build_pdf_report_creates_parent_directory(tmp_path):
    results = [
        TestResult(
            nodeid="tests/test_example.py::test_a",
            name="test_a",
            outcome="passed",
            duration=1.0,
            docstring="Example test.",
        ),
    ]

    output_path = str(tmp_path / "nested" / "dir" / "report.pdf")
    build_pdf_report(results, output_path)

    assert os.path.isfile(output_path)


def test_build_pdf_report_empty_results(tmp_path):
    output_path = str(tmp_path / "empty_report.pdf")
    build_pdf_report([], output_path)

    assert os.path.isfile(output_path)
    with open(output_path, "rb") as pdf_file:
        assert pdf_file.read(5) == b"%PDF-"


def test_build_pdf_report_renders_step_verdicts_and_screenshots(tmp_path):
    """
    A docstring's numbered steps that have a matching StepResult (by
    step_number) should render with a PASS/FAIL/SKIP badge and, when a
    screenshot_path is provided, embed that screenshot right after the
    step - while a step with no matching StepResult (step 3 here) still
    renders plain/unannotated, same as before this feature existed.
    """
    step_screenshot = str(tmp_path / "step_screenshots" / "step01.png")
    _make_fixture_screenshot(step_screenshot)

    results = [
        TestResult(
            nodeid="tests/test_example.py::test_with_steps",
            name="test_with_steps",
            outcome="failed",
            duration=3.0,
            docstring="""
            Example test with per-step verdicts.
              1. Open a saved file.
              2. Verify the file loaded correctly.
              3. Close the file (not explicitly recorded).
            """,
            steps=[
                StepResult(step_number=1, outcome="passed", note="File opened cleanly",
                           screenshot_path=step_screenshot),
                StepResult(step_number=2, outcome="failed", note="Expected value missing"),
            ],
        ),
    ]

    output_path = str(tmp_path / "report_with_steps.pdf")
    build_pdf_report(results, output_path)

    assert os.path.isfile(output_path)
    reader = PdfReader(output_path)
    detail_text = reader.pages[1].extract_text()
    assert "PASS" in detail_text
    assert "FAIL" in detail_text
    assert "File opened cleanly" in detail_text
    assert "Expected value missing" in detail_text
    # Step 3 has no recorded StepResult - it should still appear plainly.
    assert "Close the file" in detail_text
    # Two detail pages: one for the step-1 embedded screenshot, one more
    # for the wrap-up (page count grows vs. a docstring-only report).
    assert len(reader.pages) >= 2
