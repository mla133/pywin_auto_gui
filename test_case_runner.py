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

Bugfix regression convention:
    Any "scenarios/ALIV-<number>.md" file (naming convention: the Jira
    ticket ID for the bug it documents) is treated as a one-off, snap-in
    bugfix regression case - written once when a bug is fixed/verified, then
    available to be re-run standalone at any time, or as part of a full
    bugfix-regression sweep, without needing to be folded into the curated
    A-H regression.md test files. Discover/run them with:

        python test_case_runner.py --list-bugfixes
        python test_case_runner.py --bugfix ALIV-4085
        python test_case_runner.py --all-bugfixes
        python test_case_runner.py --all-bugfixes --report-dir scenarios/reports

    New bugfix cases just need to be dropped into scenarios/ as
    "ALIV-<number>.md" (same wiki-markup format as ALIV-3929.md) - no
    registration step required, they're picked up automatically by name.
"""
import argparse
import glob
import os
import re
import sys
import time
from datetime import datetime

import scenario_runner as sr
from app.application import AccuMateApp
from pages.main_page import MainPage
from workflows.file_workflows import load_config_file


# Naming convention for one-off, snap-in bugfix regression cases (see
# module docstring "Bugfix regression convention"): any file matching this
# glob under scenarios/ is auto-discovered, no registration needed.
_BUGFIX_GLOB = "ALIV-*.md"
_DEFAULT_SCENARIOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios")


def discover_bugfix_files(scenarios_dir=_DEFAULT_SCENARIOS_DIR):
    """
    Return a sorted list of full paths to bugfix regression Markdown files
    (scenarios/ALIV-<number>.md) found in scenarios_dir. Excludes any
    generated "-report.md" files that live alongside them.
    """
    pattern = os.path.join(scenarios_dir, _BUGFIX_GLOB)
    files = [f for f in glob.glob(pattern) if not f.endswith("-report.md")]
    return sorted(files)


def resolve_bugfix_id(bugfix_id, scenarios_dir=_DEFAULT_SCENARIOS_DIR):
    """
    Resolve a bare bugfix ticket ID (e.g. "ALIV-4085" or "4085") to its
    full scenarios/ALIV-<number>.md path. Raises FileNotFoundError with a
    helpful message (including the list of known IDs) if no match exists.
    """
    candidate = bugfix_id if bugfix_id.upper().startswith("ALIV-") else f"ALIV-{bugfix_id}"
    path = os.path.join(scenarios_dir, f"{candidate}.md")
    if os.path.isfile(path):
        return path

    known = [os.path.splitext(os.path.basename(f))[0] for f in discover_bugfix_files(scenarios_dir)]
    raise FileNotFoundError(
        f"No bugfix scenario found for {bugfix_id!r} (looked for {path!r}). "
        f"Known bugfix IDs: {', '.join(known) if known else '(none found)'}"
    )


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


# Bounded, per-clause pattern for read-only value assertions embedded in an
# otherwise-compound step, e.g. "Confirm that *1903 - Ethernet Host Security
# Level* is set to "No Security"." - anchored to the whole clause (not the
# whole step), so it's exactly as safe as the whole-step matching above: a
# clause this pattern doesn't fully match (e.g. a compound "X & Y is set to
# Z" clause, or "is set to anything other than ...") is simply skipped
# rather than guessed at.
_CLAUSE_VALUE_CHECK_RE = re.compile(
    r"^(?:confirm|verify)(?: that)? (.+?) (?:is|are) set to [\"'](.+?)[\"']\.?$",
    re.IGNORECASE,
)


def auto_check_value_clauses(tc_step, page):
    """
    Best-effort, READ-ONLY auto-check for simple "Confirm/Verify that
    <parameter> is set to '<value>'" clauses embedded in a step's text
    and/or Expected Result - using page.get_value() (a plain listview read;
    no UI action, no device write, no passcode involved).

    This is deliberately NOT used to change a step's recorded PASS/FAIL/SKIP
    verdict - most of these steps are compound (they also involve passcodes,
    connectivity, or other actions a human still needs to judge) - but it
    surfaces a concrete, automatically-checked fact per clause to help
    whoever performs the manual verification, instead of leaving the whole
    step as an unassisted guess. Returns a list of
    (parameter, expected_value, actual_value_or_None, ok_or_None) tuples;
    `ok` is None (with actual_value None) when the parameter couldn't be
    read at all (e.g. not visible in the currently-selected directory's
    list view) rather than guessed at.

    Clauses this pattern doesn't cleanly match (e.g. "*A* & *B* is set to
    ...", or negated claims like "is set to anything other than ...") are
    silently skipped - the whole point of anchoring to the whole clause is
    that an unmatched clause means "don't know", never a wrong guess.
    """
    checks = []
    text = tc_step.text
    if tc_step.expected_result:
        text = f"{text}  {tc_step.expected_result}"

    for clause in split_into_clauses(text):
        m = _CLAUSE_VALUE_CHECK_RE.match(clause.strip())
        if not m:
            continue

        raw_param, expected_value = m.group(1), m.group(2)
        # Compound clauses (e.g. "both *A* & *B* is set to ...") are never
        # split further here - matching them would require guessing which
        # side of the "&" the expected value applies to.  Skip entirely.
        if "&" in raw_param or re.search(r"\bboth\b", raw_param, re.IGNORECASE):
            continue

        param = raw_param.strip("*_ ")
        if "->" in param:
            param = param.split("->")[-1].strip()

        try:
            actual_value = page.get_value(param)
        except Exception:
            checks.append((param, expected_value, None, None))
            continue

        ok = actual_value.strip().lower() == expected_value.strip().lower()
        checks.append((param, expected_value, actual_value, ok))

    return checks


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


_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_CONFIGS_DIR = os.path.join(_REPO_ROOT, "configs")


def _resolve_config_path(filename, base_dir):
    """
    Resolve a bare config filename (no directory) referenced by a test-case
    step, e.g. "ALIV-3929.AL4", against the repo's configs/ directory (where
    saved AccuMate config files referenced by these formal test-case
    documents are expected to live - see configs/ALIV-3929.AL4), falling
    back to the scenario Markdown file's own directory for backward
    compatibility. A filename that already includes a directory is used
    as-is unchanged.
    """
    if os.path.dirname(filename):
        return filename

    configs_candidate = os.path.join(_CONFIGS_DIR, filename)
    if os.path.isfile(configs_candidate):
        return configs_candidate

    return os.path.join(base_dir, filename)


@_testcase_step(r"^start (?:the )?accumate application\.?$")
def _tc_start_app(app, page, m, base_dir):
    # AccuMateApp is already launched by run_test_case() before any steps
    # run - this step just confirms the main window is actually up.
    app.get_window()


@_testcase_step(r"^load test configuration file ['\"]?(.+?)['\"]?(?: file)?\.?$")
def _tc_load_test_configuration_file(app, page, m, base_dir):
    config_path = _resolve_config_path(m.group(1), base_dir)
    load_config_file(app, config_path)


# "Navigate to the X -> Y.  Click the 'Z' Ribbon button." is a common, safe
# pattern in these documents for *read-only* directory operations (Pull
# Selected/Pull All) - no parameter value is written and no passcode is
# consumed, unlike the "attempt to change ..." steps, so it's safe to
# automate the navigation + ribbon click itself. Real example (ALIV-3929.md):
# "Navigate to the System Directory -> Security Directory.  Click the
# 'Pull Selected from AccuLoad' Ribbon button."
@_testcase_step(
    r"^navigate to the ['\"]?(.+?)['\"]? -> ['\"]?(.+?)['\"]?\.\s*"
    r"click the ['\"](.+?)['\"] ribbon button\.?$"
)
def _tc_navigate_and_click_ribbon(app, page, m, base_dir):
    parent, child, button_name = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    page.select_tree_path([parent, child])

    if not page.is_ribbon_enabled(button_name):
        raise RuntimeError(
            f"Ribbon button '{button_name}' is disabled (device likely not connected) - "
            "cannot safely verify this step"
        )

    page.click_ribbon(button_name)


# scenario_runner's step grammar was designed for purpose-written, single-
# clause scenario files where the whole line *is* the instruction. Several
# of those patterns use an open-ended, non-greedy capture anchored only at
# the end of the string (e.g. "set X to Y", "click <name>") - fine for a
# clean one-line scenario step, but unsafe against messy, compound
# test-case prose: a real run against ALIV-3929.md showed both the
# "click <name>" catch-all AND "change X to Y" wrongly swallowing an
# entire trailing sentence ("Change Security Directory -> ... to 'No
# Security'.  Confirm the AccuLoad updated the parameter.  Go offline...")
# into the captured value, then attempting (and failing) a bogus action
# instead of correctly falling back to a manual step.
#
# Rather than denylist the risky patterns one at a time as each new false
# positive surfaces, this is an explicit ALLOWLIST of scenario_runner
# handlers judged genuinely bounded/safe for whole-step matching against
# arbitrary prose: each either matches a short, literal fixed phrase, or
# has a tightly-constrained capture group (an IPv4 regex, a single
# whitespace-free token, a bare number) that can't accidentally absorb an
# unrelated trailing clause.
_SAFE_STEP_HANDLERS = {
    sr._step_load_test_file,
    sr._step_load_config_file,
    sr._step_connect_to_ip,
    sr._step_enter_passcode,
    sr._step_assert_connected,
    sr._step_assert_disconnected,
    sr._step_wait,
}


# --- Automated post-execution verification ---------------------------------
#
# Historically, an AUTO step's verdict was just "did the handler raise an
# exception?" - which confirms the *action* ran, but not that the app
# actually reached the state the step's Expected Result claims. Where we can
# check that safely and unambiguously using existing app/page primitives
# (not by guessing at arbitrary prose), we do - each matched handler above
# may have an associated verifier here that re-checks real app state after
# the handler runs and turns that into the recorded PASS/FAIL, instead of
# just assuming success. Steps whose expected result can't be safely
# verified this way keep the previous "ran without raising -> PASS"
# behavior; steps with no matching *action* handler at all still always
# fall back to a manual prompt (see match_testcase_step) - we only verify
# the aftermath of something we ourselves already executed.
def _verify_window_title_contains(app, expected_substring, timeout=25):
    """
    AccuMate's main frame title becomes "<filename> - AccuMate for
    AccuLoad" once a document is open (see app/application.py's _TITLE_RE
    comment). Checking for the loaded file's base name in the title
    confirms a file genuinely loaded, as opposed to load_config_file()
    merely not raising (e.g. the Open dialog silently failing to commit).

    Polls for up to `timeout` seconds. The title update lags well behind
    the Open dialog closing: live testing showed AccuMate spends ~10-13s
    attempting a device connection (using the newly-loaded config's
    comm settings) before it finishes loading the document and updates the
    title - a naive immediate/short-poll check reads the *previous* title
    during that window and reports a false failure.
    """
    start = time.time()
    title = ""

    while time.time() - start < timeout:
        win = app.get_window()
        title = win.window_text()
        if expected_substring.lower() in title.lower():
            return True, f"window title: {title!r}"
        time.sleep(0.5)

    return False, f"window title: {title!r}"



def _verify_config_file_loaded(app, page, m, base_dir):
    config_path = _resolve_config_path(m.group(1), base_dir)
    expected_name = os.path.splitext(os.path.basename(config_path))[0]
    return _verify_window_title_contains(app, expected_name)


def _verify_sr_test_file_loaded(app, page, m, base_dir):
    expected_name = os.path.splitext(os.path.basename(sr.TEST_FILE))[0]
    return _verify_window_title_contains(app, expected_name)


def _verify_sr_config_file_loaded(app, page, m, base_dir):
    expected_name = os.path.splitext(os.path.basename(m.group(1)))[0]
    return _verify_window_title_contains(app, expected_name)


def _verify_connected(app, page, m, base_dir):
    connected = app.is_device_connected()
    return connected, ("device reports connected" if connected else "device reports NOT connected")


def _dialog_present(app, timeout=3):
    """
    True if any generic #32770 dialog (passcode prompt, error popup, etc.)
    is currently showing. Used to verify the *absence* of an unexpected
    passcode/credentials prompt after a read-only directory pull, per
    _verify_no_passcode_prompt below.
    """
    try:
        return app.app.window(class_name="#32770").exists(timeout=timeout)
    except Exception:
        return False


def _verify_no_passcode_prompt(app, page, m, base_dir):
    """
    For _tc_navigate_and_click_ribbon: the Expected Result claims the pull
    completes "without prompting for credentials" - verify that no #32770
    dialog (the passcode prompt's window class) appeared as a side effect.
    """
    prompted = _dialog_present(app, timeout=3)
    return (not prompted), ("no passcode/credentials prompt appeared" if not prompted
                             else "an unexpected dialog appeared after the pull")


# Keyed by the _TESTCASE_STEP_PATTERNS handler function.
_STEP_VERIFIERS = {
    _tc_load_test_configuration_file: _verify_config_file_loaded,
    _tc_navigate_and_click_ribbon: _verify_no_passcode_prompt,
}


# Keyed by the scenario_runner handler function (subset of _SAFE_STEP_HANDLERS).
_SR_STEP_VERIFIERS = {
    sr._step_load_test_file: _verify_sr_test_file_loaded,
    sr._step_load_config_file: _verify_sr_config_file_loaded,
    sr._step_connect_to_ip: _verify_connected,
}


def match_testcase_step(step_text, base_dir):
    """
    Try to match a whole step's text against the curated fully-automatable
    patterns, falling back to the allowlisted subset of scenario_runner's
    general step grammar (see _SAFE_STEP_HANDLERS). Returns (handler, args)
    where handler(app, page, *args) executes the step, or (None, None) if
    nothing matched (-> manual step). If a verifier is registered for the
    matched pattern (see _STEP_VERIFIERS/_SR_STEP_VERIFIERS), it's attached
    as `handler.verifier(app, page) -> (bool_ok, detail_str)` for the caller
    to use instead of assuming success merely because the handler didn't
    raise.
    """
    stripped = step_text.strip()

    for pattern, handler in _TESTCASE_STEP_PATTERNS:
        m = pattern.match(stripped)
        if m:
            exec_fn = lambda app, page, m=m, handler=handler: handler(app, page, m, base_dir)
            verifier = _STEP_VERIFIERS.get(handler)
            if verifier is not None:
                exec_fn.verifier = lambda app, page, m=m, verifier=verifier: verifier(app, page, m, base_dir)
            return exec_fn, m

    for pattern, handler in sr._STEP_PATTERNS:
        if handler not in _SAFE_STEP_HANDLERS:
            continue
        m = pattern.match(stripped)
        if m:
            exec_fn = lambda app, page, m=m, handler=handler: handler(app, page, m)
            verifier = _SR_STEP_VERIFIERS.get(handler)
            if verifier is not None:
                exec_fn.verifier = lambda app, page, m=m, verifier=verifier: verifier(app, page, m, base_dir)
            return exec_fn, m

    return None, None


def _format_auto_checks(checks):
    lines = []
    for param, expected_value, actual_value, ok in checks:
        if ok is None:
            lines.append(f"[AUTO-CHECK] '{param}' expected '{expected_value}' - could not read current value")
        elif ok:
            lines.append(f"[AUTO-CHECK] '{param}' = '{actual_value}' (matches expected '{expected_value}')")
        else:
            lines.append(f"[AUTO-CHECK] '{param}' = '{actual_value}' (expected '{expected_value}' - MISMATCH)")
    return lines


def _prompt_manual_verdict(step, page=None):
    print(f"    [MANUAL] Perform this step by hand: {step.text}")
    if step.expected_result:
        print(f"    [MANUAL] Expected result: {step.expected_result}")

    auto_check_notes = []
    if page is not None:
        checks = auto_check_value_clauses(step, page)
        for line in _format_auto_checks(checks):
            print(f"    {line}")
        auto_check_notes = [line for line in _format_auto_checks(checks) if "could not read" not in line]

    while True:
        answer = input("    Result? [p]ass / [f]ail / [s]kip: ").strip().lower()
        if answer in ("p", "pass"):
            return "PASS", "; ".join(auto_check_notes) or None
        if answer in ("f", "fail"):
            note = input("    Failure notes (optional): ").strip()
            combined = "; ".join([note] + auto_check_notes) if note else ("; ".join(auto_check_notes) or None)
            return "FAIL", combined or None
        if answer in ("s", "skip"):
            return "SKIP", "; ".join(auto_check_notes) or None
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
                        verifier = getattr(handler, "verifier", None)

                        if verifier is not None:
                            try:
                                ok, detail = verifier(app, page)
                            except Exception as e:
                                ok, detail = False, f"verification error: {e}"

                            verdict = "PASS" if ok else "FAIL"
                            print(f"  [AUTO] executed; verification {verdict} ({detail})")
                            results.append((section.title, tc_step, "AUTO", verdict, f"auto-verified: {detail}"))
                        else:
                            print("  [AUTO] executed successfully")
                            results.append((section.title, tc_step, "AUTO", "PASS", None))
                    except Exception as e:
                        print(f"  [AUTO] FAILED: {e}")
                        results.append((section.title, tc_step, "AUTO", "FAIL", str(e)))
                else:
                    verdict, note = _prompt_manual_verdict(tc_step, page)
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


def run_bugfix_batch(paths, report_dir=None):
    """
    Run several bugfix test case documents back-to-back (one AccuMate
    process/run per file, sequentially - each still opens/tears down its
    own app instance via run_test_case). Returns True only if every file's
    steps were PASS/SKIP.
    """
    overall_success = True
    per_file_results = []

    for path in paths:
        report_path = None
        if report_dir is not None:
            base = os.path.splitext(os.path.basename(path))[0]
            report_path = os.path.join(report_dir, f"{base}-report.md")

        print(f"\n{'=' * 70}\n[INFO] Running bugfix scenario: {path}\n{'=' * 70}")
        ok = run_test_case(path, report_path)
        per_file_results.append((path, ok))
        overall_success = overall_success and ok

    print(f"\n{'=' * 70}\n[INFO] Bugfix batch summary\n{'=' * 70}")
    for path, ok in per_file_results:
        print(f"  {'PASS' if ok else 'FAIL'}  {path}")

    return overall_success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("markdown_file", nargs="?", default=None,
                         help="Path to a wiki-markup test case Markdown file")
    parser.add_argument("--report", default=None, help="Path to write the results Markdown report to")
    parser.add_argument("--bugfix", default=None, metavar="ALIV-<number>",
                         help="Run a single bugfix scenario by ticket ID, e.g. --bugfix ALIV-4085 "
                              "(resolves to scenarios/ALIV-4085.md)")
    parser.add_argument("--all-bugfixes", action="store_true",
                         help="Run every scenarios/ALIV-*.md bugfix scenario, one after another")
    parser.add_argument("--list-bugfixes", action="store_true",
                         help="List discovered scenarios/ALIV-*.md bugfix scenarios and exit")
    parser.add_argument("--scenarios-dir", default=_DEFAULT_SCENARIOS_DIR,
                         help="Directory to search for ALIV-*.md bugfix scenarios (default: scenarios/)")
    parser.add_argument("--report-dir", default=None,
                         help="Directory to write per-file reports to when running --all-bugfixes "
                              "(default: alongside each input file)")
    args = parser.parse_args()

    if args.list_bugfixes:
        found = discover_bugfix_files(args.scenarios_dir)
        if not found:
            print(f"[INFO] No bugfix scenarios found in {args.scenarios_dir}")
        else:
            print(f"[INFO] Found {len(found)} bugfix scenario(s) in {args.scenarios_dir}:")
            for f in found:
                print(f"  {os.path.splitext(os.path.basename(f))[0]}")
        sys.exit(0)

    if args.all_bugfixes:
        found = discover_bugfix_files(args.scenarios_dir)
        if not found:
            print(f"[WARN] No bugfix scenarios found in {args.scenarios_dir}")
            sys.exit(0)
        success = run_bugfix_batch(found, args.report_dir)
        sys.exit(0 if success else 1)

    if args.bugfix:
        target = resolve_bugfix_id(args.bugfix, args.scenarios_dir)
        success = run_test_case(target, args.report)
        sys.exit(0 if success else 1)

    if not args.markdown_file:
        parser.error("markdown_file is required unless --bugfix/--all-bugfixes/--list-bugfixes is used")

    success = run_test_case(args.markdown_file, args.report)
    sys.exit(0 if success else 1)
