"""
Hybrid runner for formal, wiki-markup-style manual test case documents (the
kind exported from Jira/Confluence for a specific ticket, e.g.
scenarios/ALIV-3929.md) - as opposed to scenario_runner.py's simpler,
purpose-written Markdown scenario format.

These documents look nothing like scenario_runner's grammar:
  - Confluence wiki markup headers ("h3.", "h4.") instead of "#"/"##".
  - Numbered steps that bundle several actions *and* a verification into
    one compound sentence (e.g. "Click the 'Go Offline' ribbon button.
    Confirm status is Offline. Click 'Retry Comm' to reconnect. Attempt to
    change a parameter. Confirm AccuMate prompts for a passcode again.").
  - A trailing "Expected Result: ..." line with a "*[PASS/FAIL]*" marker -
    written for a *human* tester to read, act on, and record a verdict for.
  - Steps that reference real device state/values, security passcodes not
    present in the document, firmware files, and multi-minute timing waits
    that fundamentally require a human (or much heavier device/timing
    integration) to judge.

Given that, this is a HYBRID runner, not a full auto-executor:
  - Each step's text is checked as a whole against a small, curated set of
    unambiguous, fully-automatable phrasings (see _TESTCASE_STEP_PATTERNS
    below, plus scenario_runner's own general step grammar) - e.g. "Start
    the AccuMate Application", "Load test configuration file '<name>'
    file". These run automatically with no human involvement.
  - Every other step is NOT guessed at or clause-split for partial
    automation (that was evaluated and rejected - see PR discussion -
    because most steps interleave UI actions with state verification that
    needs a human to read the screen anyway, so partial auto-execution
    would only add fragility without saving real effort). Instead the step
    text and its Expected Result are printed, and the runner pauses for the
    human to perform/verify it and type a verdict (pass/fail/skip).
  - Passcodes are always entered manually, on purpose - real per-site
    security passcodes have no business living in a Markdown test-case
    file or in this repository, so "enter the passcode" steps always pause
    rather than trying to source a passcode from anywhere automatic.
  - Results (per step: AUTO/MANUAL, verdict, notes) are collected and
    written out as a Markdown report next to the input file.

Usage:
    python test_case_runner.py scenarios/ALIV-3929.md
    python test_case_runner.py scenarios/ALIV-3929.md --report results/ALIV-3929-report.md
"""
import argparse
import os
import re
import sys
from datetime import datetime

import scenario_runner as sr
from app.application import AccuMateApp
from pages.main_page import MainPage
from workflows.file_workflows import load_config_file


_HEADER_RE = re.compile(r"^h([1-6])\.\s*(.*)$")
_STEP_RE = re.compile(r"^(\d+)\.\s+(.*)$")
_EXPECTED_RE = re.compile(r"Expected [Rr]esults?:\s*(.*)$")
_TRAILING_PASSFAIL_RE = re.compile(r"\*\[PASS/FAIL\]\*\s*$")
_WRAPPING_EMPHASIS_RE = re.compile(r"^_(.*)_$|^\*(.*)\*$")

# Sentence-ish split: break after . / ! / ? followed by whitespace and a
# capital letter. Deliberately conservative - it under-splits (e.g. leaves
# "e.g. X" alone) rather than over-splitting inside quoted text, since a
# missed split just becomes one slightly bigger unmatched clause (falls
# back to a manual step) rather than a wrongly-matched one.
_CLAUSE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


class TestStep:
    def __init__(self, number, text):
        self.number = number
        self.text = text
        self.expected_result = None

    def __repr__(self):
        return f"TestStep({self.number}, {self.text!r})"


class TestSection:
    def __init__(self, title):
        self.title = title
        self.steps = []

    def __repr__(self):
        return f"TestSection({self.title!r}, {len(self.steps)} steps)"


def _clean_wiki_text(text):
    text = _TRAILING_PASSFAIL_RE.sub("", text).strip()
    m = _WRAPPING_EMPHASIS_RE.match(text)
    if m:
        text = (m.group(1) or m.group(2)).strip()
    return text


def parse_test_case_document(path):
    """
    Parse a Confluence/Jira-style wiki-markup manual test case document into
    an ordered list of TestSection objects, each holding its TestStep
    objects (step text + optional expected_result).

    Only content under "h4." headers is treated as test steps - preamble
    (an "h3." title, notes, a settings-value list before any "h4.") is
    narration/setup context and is intentionally skipped, since it isn't
    itself a sequence of test actions.
    """
    sections = []
    current_section = None
    current_step = None
    in_step_section = False

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    def flush_step():
        nonlocal current_step
        if current_step is not None and current_section is not None:
            current_section.steps.append(current_step)
        current_step = None

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            continue

        header_match = _HEADER_RE.match(stripped)
        if header_match:
            level, title = header_match.groups()
            flush_step()
            if level == "4":
                current_section = TestSection(title.strip())
                sections.append(current_section)
                in_step_section = True
            else:
                current_section = None
                in_step_section = False
            continue

        if not in_step_section:
            continue

        expected_match = _EXPECTED_RE.search(stripped)
        if expected_match and current_step is not None:
            current_step.expected_result = _clean_wiki_text(expected_match.group(1))
            continue

        step_match = _STEP_RE.match(stripped)
        if step_match:
            flush_step()
            number, text = step_match.groups()
            current_step = TestStep(int(number), text.strip())
            continue

        # Wrapped continuation of the current step's own text (not an
        # "Expected Result:" line, not a new numbered step).
        if current_step is not None:
            current_step.text += " " + stripped

    flush_step()

    return sections


def split_into_clauses(text):
    """Split one compound step sentence into individual clauses."""
    return [c.strip() for c in _CLAUSE_SPLIT_RE.split(text) if c.strip()]


# Small, curated set of additional literal phrasings seen in formal
# test-case documents that are unambiguous and safe to fully automate.
# Deliberately NOT trying to cover every phrasing variant here - anything
# not covered falls back to a manual prompt, which is the safe default.
_TESTCASE_STEP_PATTERNS = []


def _testcase_step(pattern):
    compiled = re.compile(pattern, re.IGNORECASE)

    def register(fn):
        _TESTCASE_STEP_PATTERNS.append((compiled, fn))
        return fn

    return register


@_testcase_step(r"^start (?:the )?accumate application\.?$")
def _tc_start_app(app, page, m, base_dir):
    # AccuMateApp is already launched by run_test_case() before any steps
    # run - this step just confirms the main window is actually up.
    app.get_window()


@_testcase_step(r"^load test configuration file ['\"]?(.+?)['\"]?(?: file)?\.?$")
def _tc_load_test_configuration_file(app, page, m, base_dir):
    filename = m.group(1)
    config_path = filename if os.path.dirname(filename) else os.path.join(base_dir, filename)
    load_config_file(app, config_path)


# scenario_runner's generic "click <name>" catch-all is intentionally loose
# (see its own docstring) because it's meant for purpose-written, single-
# clause scenario files where the whole line *is* the button name. Formal
# test-case prose is much messier ("Click on the 'Open' button in the top
# left corner of the application.") and that looseness lets filler words
# slip into the captured button name, causing a wrong auto-click attempt
# instead of correctly falling back to a manual step. So it's excluded from
# the whole-step fallback here - real testing against ALIV-3929.md caught
# this exact false positive.
_UNSAFE_FOR_WHOLE_STEP_MATCHING = {sr._step_click_ribbon}


def match_testcase_step(step_text, base_dir):
    """
    Try to match a whole step's text against the curated fully-automatable
    patterns, falling back to scenario_runner's general step grammar (minus
    patterns judged unsafe for messy, compound test-case prose - see
    _UNSAFE_FOR_WHOLE_STEP_MATCHING). Returns (handler, args) where
    handler(app, page, *args) executes the step, or (None, None) if nothing
    matched (-> manual step).
    """
    stripped = step_text.strip()

    for pattern, handler in _TESTCASE_STEP_PATTERNS:
        m = pattern.match(stripped)
        if m:
            return (lambda app, page, m=m, handler=handler: handler(app, page, m, base_dir)), m

    for pattern, handler in sr._STEP_PATTERNS:
        if handler in _UNSAFE_FOR_WHOLE_STEP_MATCHING:
            continue
        m = pattern.match(stripped)
        if m:
            return (lambda app, page, m=m, handler=handler: handler(app, page, m)), m

    return None, None


def _prompt_manual_verdict(step):
    print(f"    [MANUAL] Perform this step by hand: {step.text}")
    if step.expected_result:
        print(f"    [MANUAL] Expected result: {step.expected_result}")

    while True:
        answer = input("    Result? [p]ass / [f]ail / [s]kip: ").strip().lower()
        if answer in ("p", "pass"):
            return "PASS", None
        if answer in ("f", "fail"):
            note = input("    Failure notes (optional): ").strip()
            return "FAIL", note or None
        if answer in ("s", "skip"):
            return "SKIP", None
        print("    Please enter 'p', 'f', or 's'.")


def run_test_case(markdown_path, report_path=None):
    base_dir = os.path.dirname(os.path.abspath(markdown_path))
    sections = parse_test_case_document(markdown_path)

    total_steps = sum(len(s.steps) for s in sections)
    if total_steps == 0:
        print(f"[WARN] No test steps found in {markdown_path} (no 'h4.' sections with numbered steps?)")
        return True

    print(f"[INFO] Parsed {len(sections)} section(s), {total_steps} step(s) from {markdown_path}")

    app = AccuMateApp()
    page = MainPage(app)
    results = []  # (section_title, step, mode, verdict, note)

    try:
        for section in sections:
            print(f"\n=== {section.title} ===")

            for tc_step in section.steps:
                print(f"\n[STEP {tc_step.number}] {tc_step.text}")
                if tc_step.expected_result:
                    print(f"  Expected: {tc_step.expected_result}")

                handler, _ = match_testcase_step(tc_step.text, base_dir)

                if handler is not None:
                    try:
                        handler(app, page)
                        print("  [AUTO] executed successfully")
                        results.append((section.title, tc_step, "AUTO", "PASS", None))
                    except Exception as e:
                        print(f"  [AUTO] FAILED: {e}")
                        results.append((section.title, tc_step, "AUTO", "FAIL", str(e)))
                else:
                    verdict, note = _prompt_manual_verdict(tc_step)
                    results.append((section.title, tc_step, "MANUAL", verdict, note))
    finally:
        sr._teardown(app, markdown_path)

    _print_summary(results)
    _write_report(markdown_path, report_path, results)

    return all(r[3] in ("PASS", "SKIP") for r in results)


def _print_summary(results):
    print("\n=== Summary ===")
    for section_title, tc_step, mode, verdict, note in results:
        note_str = f" ({note})" if note else ""
        print(f"  [{section_title}] step {tc_step.number} - {mode}/{verdict}{note_str}")

    failed = [r for r in results if r[3] == "FAIL"]
    print(f"\n{len(results)} step(s) recorded, {len(failed)} failure(s)")


def _write_report(markdown_path, report_path, results):
    if report_path is None:
        base = os.path.splitext(os.path.basename(markdown_path))[0]
        report_path = os.path.join(os.path.dirname(os.path.abspath(markdown_path)), f"{base}-report.md")

    lines = [
        f"# Test case results: {os.path.basename(markdown_path)}",
        "",
        f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    current_section = None
    for section_title, tc_step, mode, verdict, note in results:
        if section_title != current_section:
            lines.append(f"\n## {section_title}\n")
            current_section = section_title

        lines.append(f"- **Step {tc_step.number}** ({mode}/{verdict}): {tc_step.text}")
        if tc_step.expected_result:
            lines.append(f"  - Expected: {tc_step.expected_result}")
        if note:
            lines.append(f"  - Notes: {note}")

    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[INFO] Report written to {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("markdown_file", help="Path to a wiki-markup test case Markdown file")
    parser.add_argument("--report", default=None, help="Path to write the results Markdown report to")
    args = parser.parse_args()

    success = run_test_case(args.markdown_file, args.report)
    sys.exit(0 if success else 1)
