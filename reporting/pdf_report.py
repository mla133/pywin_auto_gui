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
import re
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

# Inline text colors (as opposed to the table-cell background colors
# above) used for the "[PASS]"/"[FAIL]"/"[SKIP]" badge appended to a
# numbered docstring step when a matching StepResult was recorded.
_STEP_BADGE_COLORS = {
    "passed": "#2e7d32",
    "failed": "#c62828",
    "skipped": "#b8860b",
}
_STEP_BADGE_LABELS = {
    "passed": "PASS",
    "failed": "FAIL",
    "skipped": "SKIP",
}

# Max width/height a screenshot is scaled down to (in inches) so it fits
# comfortably on a US Letter page alongside its caption/heading.
_SCREENSHOT_MAX_WIDTH_IN = 6.5
_SCREENSHOT_MAX_HEIGHT_IN = 4.5


@dataclass
class StepResult:
    """
    One explicitly-recorded numbered-step verdict within a test, captured
    via the `record_step` fixture (see conftest.py) so the PDF report can
    show PASS/FAIL/SKIP per docstring step instead of only one overall
    test outcome. Matched to a docstring's numbered list item by
    `step_number` (e.g. step_number=11 matches a docstring line starting
    "11. ..."). Optional and additive - docstrings/tests that don't use
    `record_step` render exactly as before (plain, unannotated list).
    """
    __test__ = False

    step_number: int
    outcome: str = "passed"  # "passed" | "failed" | "skipped"
    note: str = ""
    screenshot_path: str = None


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
    steps: list = field(default_factory=list)  # list[StepResult], see above


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
    styles.add(ParagraphStyle(
        # A single numbered-step line (e.g. "1. Open a saved file.") -
        # hanging indent so a wrapped continuation line lines up under the
        # step text rather than back under the number.
        name="DocstringStep", parent=styles["Docstring"], leftIndent=16,
        firstLineIndent=-16, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        # An optional note attached to a record_step() verdict, shown
        # indented under its step line (e.g. "Migration notice text did
        # not match expected wording").
        name="DocstringStepNote", parent=styles["Docstring"], fontSize=8,
        leftIndent=28, spaceAfter=4, textColor=colors.grey,
    ))
    styles.add(ParagraphStyle(
        # Used for table cells that may contain long, unbroken strings
        # (pytest node IDs like "tests/foo.py::test_x[param-with-no-spaces]",
        # comma-joined marker lists) - wordWrap=None + the small font size
        # let reportlab break mid-word when a cell's content is wider than
        # its column, instead of silently overflowing past the page margin.
        name="WrapCell", parent=styles["BodyText"], fontSize=8, leading=10,
        wordWrap=None,
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


_NUMBERED_STEP_RE = re.compile(r"^\d+[\.\)]\s+")
_STEP_NUMBER_PREFIX_RE = re.compile(r"^(\d+)[\.\)]\s+")


def _screenshot_flowables(screenshot_path, styles, caption=None):
    """
    Returns flowables (caption Paragraph + scaled Image) embedding one
    screenshot, or a short italic error note if the file can't be loaded
    (e.g. a corrupt/partial PNG) - shared by both the test-level
    "Screenshots" section and per-step screenshots in the docstring list,
    so both places scale/caption images identically.
    """
    try:
        img = Image(screenshot_path)
        # Scale to fit within the max box while preserving aspect ratio -
        # reportlab's Image doesn't do this automatically.
        scale = min(
            (_SCREENSHOT_MAX_WIDTH_IN * inch) / img.imageWidth,
            (_SCREENSHOT_MAX_HEIGHT_IN * inch) / img.imageHeight,
            1.0,
        )
        img.drawWidth = img.imageWidth * scale
        img.drawHeight = img.imageHeight * scale
        return [
            Paragraph(caption or os.path.basename(screenshot_path), styles["Italic"]),
            img,
            Spacer(1, 0.1 * inch),
        ]
    except Exception as exc:  # pragma: no cover - defensive, a corrupt PNG shouldn't kill the whole report
        return [Paragraph(
            f"(could not embed screenshot {os.path.basename(screenshot_path)}: {exc})",
            styles["Italic"],
        )]


def _docstring_flowables(docstring, styles, steps=None):
    """
    Renders a test's docstring as one or more flowables instead of a
    single run-on paragraph, so multi-paragraph text and numbered step
    lists (the common style used across tests/test_regression_*.py, e.g.
    "1. Open a saved file.\n2. Print it.\n3. Verify...") stay readable
    instead of collapsing into one dense block.

    Blocks are split on blank lines (paragraph breaks). Within a block, a
    line starting with "N." or "N)" starts a new numbered step; any
    following non-numbered line is treated as a wrapped continuation of
    that step and merged onto it with a space. A block containing at
    least one numbered line is rendered as a sequence of "DocstringStep"
    paragraphs (hanging indent, so wrapped continuations still line up
    under the step text); any other block is rendered as a single plain
    "Docstring" paragraph, same as before.

    `steps` (optional list[StepResult]) lets a test explicitly record a
    PASS/FAIL/SKIP verdict (and optional screenshot/note) for one of its
    numbered steps via the `record_step` fixture (see conftest.py). Each
    numbered item whose leading number matches a StepResult.step_number
    gets a colored "[PASS]"/"[FAIL]"/"[SKIP]" badge appended, an optional
    note paragraph, and its recorded screenshot embedded right below it -
    steps with no matching StepResult render exactly as before (plain,
    unannotated).
    """
    steps_by_number = {s.step_number: s for s in (steps or [])}

    raw_lines = docstring.strip().splitlines()
    # Dedent: strip only the common leading whitespace pytest docstrings
    # pick up from source indentation, not intentional list indent.
    stripped_lines = [line.strip() for line in raw_lines]

    blocks = []
    current_block = []
    for line in stripped_lines:
        if not line:
            if current_block:
                blocks.append(current_block)
                current_block = []
            continue
        current_block.append(line)
    if current_block:
        blocks.append(current_block)

    flowables = []
    for block in blocks:
        items = []
        for line in block:
            if _NUMBERED_STEP_RE.match(line):
                items.append(line)
            elif items:
                # Continuation of a wrapped numbered step's text.
                items[-1] = f"{items[-1]} {line}"
            else:
                items.append(line)

        is_numbered_list = any(_NUMBERED_STEP_RE.match(item) for item in items)
        if is_numbered_list:
            for item in items:
                step_result = None
                match = _STEP_NUMBER_PREFIX_RE.match(item)
                if match:
                    step_result = steps_by_number.get(int(match.group(1)))

                if step_result is None:
                    flowables.append(Paragraph(item, styles["DocstringStep"]))
                    continue

                badge_color = _STEP_BADGE_COLORS.get(step_result.outcome, "#666666")
                badge_label = _STEP_BADGE_LABELS.get(step_result.outcome, step_result.outcome.upper())
                flowables.append(Paragraph(
                    f'{item}  <font color="{badge_color}"><b>[{badge_label}]</b></font>',
                    styles["DocstringStep"],
                ))
                if step_result.note:
                    flowables.append(Paragraph(f"<i>{step_result.note}</i>", styles["DocstringStepNote"]))
                if step_result.screenshot_path and os.path.isfile(step_result.screenshot_path):
                    flowables.extend(_screenshot_flowables(
                        step_result.screenshot_path, styles,
                        caption=f"Step {step_result.step_number} screenshot: "
                                f"{os.path.basename(step_result.screenshot_path)}",
                    ))
        else:
            flowables.append(Paragraph(" ".join(items), styles["Docstring"]))

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
            ["Markers", Paragraph(markers_text, styles["WrapCell"])],
            ["Node ID", Paragraph(result.nodeid, styles["WrapCell"])],
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
        # Docstrings can be long/multi-paragraph free text with numbered
        # step lists (see e.g. tests/test_regression_f.py) - render each
        # paragraph/step as its own flowable so lists stay readable
        # instead of collapsing into one dense run-on paragraph. Any
        # steps explicitly recorded via record_step() get a PASS/FAIL/SKIP
        # badge (and optional screenshot) inline with their list item.
        flowables.extend(_docstring_flowables(result.docstring, styles, steps=result.steps))

    if result.outcome in ("failed", "error") and result.longrepr:
        flowables.append(Paragraph("<b>Failure Detail</b>", styles["BodyText"]))
        flowables.append(Preformatted(result.longrepr, styles["Code"]))
        flowables.append(Spacer(1, 0.1 * inch))

    screenshots = _find_screenshots(result.screenshot_dir)
    if screenshots:
        flowables.append(Paragraph(f"<b>Screenshots ({len(screenshots)})</b>", styles["BodyText"]))
        for screenshot_path in screenshots:
            flowables.extend(_screenshot_flowables(screenshot_path, styles))
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
