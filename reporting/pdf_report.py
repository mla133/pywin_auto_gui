"""
Builds a single PDF regression-report summarizing a pytest run: an overall
pass/fail/skip/error summary at the top, followed by a full per-test
breakdown (docstring, markers, outcome, duration, failure text, and any
screenshots captured during that test).

This module is intentionally decoupled from pytest itself - it only knows
about the plain TestResult dataclass below. The actual pytest hooks that
populate a list of TestResult objects during a real run live in the root
conftest.py (see `pytest_addoption`/`pytest_runtest_makereport`/
`pytest_sessionfinish`), which calls build_pdf_report() at session finish
when `--pdf-report=<path>` was passed. Keeping this module pytest-agnostic
also makes it straightforward to unit-test directly (see
tests/test_pdf_report.py) with hand-built TestResult objects, no live app
or pytest session required.
"""
import glob
import os
from dataclasses import dataclass, field
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Outcome -> background color used in both the summary table and each
# test's own detail-section metadata table.
_OUTCOME_COLORS = {
    "passed": colors.HexColor("#c6efce"),
    "failed": colors.HexColor("#ffc7ce"),
    "error": colors.HexColor("#ffc7ce"),
    "skipped": colors.HexColor("#ffeb9c"),
}
_DEFAULT_OUTCOME_COLOR = colors.HexColor("#d9d9d9")

# Max width/height a screenshot is scaled down to (in inches) so it fits
# comfortably on a US Letter page alongside its caption/heading.
_SCREENSHOT_MAX_WIDTH_IN = 6.5
_SCREENSHOT_MAX_HEIGHT_IN = 4.5


@dataclass
class TestResult:
    """
    A single test's outcome, ready to be rendered into the PDF. Built by
    conftest.py's pytest_runtest_makereport hook during a real run, or by
    hand in tests/test_pdf_report.py for unit testing.
    """
    # Tells pytest not to try collecting this as a test class itself, just
    # because its name starts with "Test" (matches python_classes default).
    __test__ = False

    nodeid: str
    name: str
    outcome: str  # "passed" | "failed" | "skipped" | "error"
    duration: float = 0.0
    docstring: str = ""
    markers: list = field(default_factory=list)
    longrepr: str = ""
    screenshot_dir: str = None


def _find_screenshots(screenshot_dir):
    """
    Returns sorted screenshot file paths for a test, matching the
    "NN_<method>_<timestamp>.png" naming convention used by
    pages/main_page.py's MainPage._auto_screenshot (numeric step prefix
    first, so a plain sort already yields step order). Returns an empty
    list if the directory doesn't exist or has no PNGs (e.g. the test
    errored before any @auto_step ran, or isn't a UI test at all).
    """
    if not screenshot_dir or not os.path.isdir(screenshot_dir):
        return []
    return sorted(glob.glob(os.path.join(screenshot_dir, "*.png")))


def _counts_by_outcome(results):
    counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
    for result in results:
        counts[result.outcome] = counts.get(result.outcome, 0) + 1
    return counts


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontSize=22, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle", parent=styles["Normal"], fontSize=10,
        textColor=colors.grey, spaceAfter=18,
    ))
    styles.add(ParagraphStyle(
        name="TestHeading", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Docstring", parent=styles["BodyText"], fontSize=9, leading=12,
        spaceAfter=8,
    ))
    return styles


def _summary_flowables(results, run_started, run_finished, styles):
    flowables = []

    flowables.append(Paragraph("Regression Test Report", styles["ReportTitle"]))
    duration_seconds = (run_finished - run_started).total_seconds()
    flowables.append(Paragraph(
        f"Generated {run_finished.strftime('%Y-%m-%d %H:%M:%S')} "
        f"&mdash; total run duration {duration_seconds:.1f}s",
        styles["ReportSubtitle"],
    ))

    counts = _counts_by_outcome(results)
    total = len(results)
    pass_rate = (counts["passed"] / total * 100.0) if total else 0.0

    counts_table_data = [
        ["Total", "Passed", "Failed", "Error", "Skipped", "Pass Rate"],
        [
            str(total),
            str(counts["passed"]),
            str(counts["failed"]),
            str(counts["error"]),
            str(counts["skipped"]),
            f"{pass_rate:.1f}%",
        ],
    ]
    counts_table = Table(counts_table_data, hAlign="LEFT")
    counts_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472c4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (1, 1), (1, 1), _OUTCOME_COLORS["passed"]),
        ("BACKGROUND", (2, 1), (2, 1), _OUTCOME_COLORS["failed"]),
        ("BACKGROUND", (3, 1), (3, 1), _OUTCOME_COLORS["error"]),
        ("BACKGROUND", (4, 1), (4, 1), _OUTCOME_COLORS["skipped"]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flowables.append(counts_table)
    flowables.append(Spacer(1, 0.25 * inch))

    flowables.append(Paragraph("Test Summary", styles["Heading2"]))
    summary_data = [["Test", "Outcome", "Duration (s)"]]
    row_colors = []
    for result in results:
        summary_data.append([
            Paragraph(result.name, styles["BodyText"]),
            result.outcome.upper(),
            f"{result.duration:.2f}",
        ])
        row_colors.append(_OUTCOME_COLORS.get(result.outcome, _DEFAULT_OUTCOME_COLOR))

    summary_table = Table(summary_data, colWidths=[3.5 * inch, 1.5 * inch, 1.5 * inch], hAlign="LEFT")
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472c4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for row_index, row_color in enumerate(row_colors, start=1):
        table_style.append(("BACKGROUND", (1, row_index), (1, row_index), row_color))
    summary_table.setStyle(TableStyle(table_style))
    flowables.append(summary_table)
    flowables.append(PageBreak())

    return flowables


def _detail_flowables_for_result(result, styles):
    flowables = []

    flowables.append(Paragraph(result.name, styles["TestHeading"]))

    outcome_color = _OUTCOME_COLORS.get(result.outcome, _DEFAULT_OUTCOME_COLOR)
    markers_text = ", ".join(result.markers) if result.markers else "(none)"
    meta_table = Table(
        [
            ["Outcome", result.outcome.upper()],
            ["Duration", f"{result.duration:.2f}s"],
            ["Markers", markers_text],
            ["Node ID", result.nodeid],
        ],
        colWidths=[1.2 * inch, 5.3 * inch],
    )
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, 0), outcome_color),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flowables.append(meta_table)
    flowables.append(Spacer(1, 0.1 * inch))

    if result.docstring:
        flowables.append(Paragraph("<b>Description</b>", styles["BodyText"]))
        # Docstrings can be long/multi-paragraph free text (see e.g.
        # tests/test_regression_f.py) - use a wrapping Paragraph rather
        # than Preformatted so it reflows naturally across page width.
        cleaned = " ".join(line.strip() for line in result.docstring.strip().splitlines())
        flowables.append(Paragraph(cleaned, styles["Docstring"]))

    if result.outcome in ("failed", "error") and result.longrepr:
        flowables.append(Paragraph("<b>Failure Detail</b>", styles["BodyText"]))
        flowables.append(Preformatted(result.longrepr, styles["Code"]))
        flowables.append(Spacer(1, 0.1 * inch))

    screenshots = _find_screenshots(result.screenshot_dir)
    if screenshots:
        flowables.append(Paragraph(f"<b>Screenshots ({len(screenshots)})</b>", styles["BodyText"]))
        for screenshot_path in screenshots:
            try:
                img = Image(screenshot_path)
                # Scale to fit within the max box while preserving aspect
                # ratio - reportlab's Image doesn't do this automatically.
                scale = min(
                    (_SCREENSHOT_MAX_WIDTH_IN * inch) / img.imageWidth,
                    (_SCREENSHOT_MAX_HEIGHT_IN * inch) / img.imageHeight,
                    1.0,
                )
                img.drawWidth = img.imageWidth * scale
                img.drawHeight = img.imageHeight * scale
                flowables.append(Paragraph(os.path.basename(screenshot_path), styles["Italic"]))
                flowables.append(img)
                flowables.append(Spacer(1, 0.1 * inch))
            except Exception as exc:  # pragma: no cover - defensive, a corrupt PNG shouldn't kill the whole report
                flowables.append(Paragraph(
                    f"(could not embed screenshot {os.path.basename(screenshot_path)}: {exc})",
                    styles["Italic"],
                ))
    else:
        flowables.append(Paragraph("<i>No screenshots captured for this test.</i>", styles["BodyText"]))

    flowables.append(PageBreak())
    return flowables


def build_pdf_report(results, output_path, run_started=None, run_finished=None):
    """
    Renders `results` (a list of TestResult) into a PDF at `output_path`:
    a summary section (counts + per-test status table) followed by a full
    detail section per test (docstring, markers, outcome, duration,
    failure text, embedded screenshots).

    `run_started`/`run_finished` default to "now" if not supplied (mainly
    a convenience for unit tests that don't care about exact timestamps).
    Creates any missing parent directory for `output_path`.
    """
    run_started = run_started or datetime.now()
    run_finished = run_finished or datetime.now()

    parent_dir = os.path.dirname(os.path.abspath(output_path))
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    styles = _build_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        title="Regression Test Report",
    )

    flowables = []
    flowables.extend(_summary_flowables(results, run_started, run_finished, styles))
    for result in results:
        flowables.extend(_detail_flowables_for_result(result, styles))

    # Drop the trailing PageBreak from the last test's detail section so
    # the document doesn't end with a blank page.
    if flowables and isinstance(flowables[-1], PageBreak):
        flowables.pop()

    doc.build(flowables)
    return output_path
