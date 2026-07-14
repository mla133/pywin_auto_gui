"""
Standalone runner that reads a plain-English Markdown "scenario" file and
executes it step-by-step against a real, running AccuMate for AccuLoad
instance - using the exact same reusable workflows/ (and pages/MainPage)
functions the pytest test suite is built on. This lets a non-technical
description of a manual test ("connect to the device, then save as
test2.al4") be re-run automatically without writing a new pytest test.

Usage:
    python scenario_runner.py scenarios/example_connect_and_save.md

Markdown format: any bullet ("- "/"* "), numbered ("1. ") list item is
treated as one ordered step; everything else (headers, blank lines, fenced
code blocks, and plain paragraph text) is narration and ignored. See
scenarios/ for worked examples.

Recognized step phrasing is intentionally small and literal (see
_STEP_PATTERNS below) rather than a full NLP parser - each pattern is a
regex mapped to one workflow call. Unrecognized steps are reported and
skipped rather than guessed at, so a typo in a scenario file fails loudly
instead of silently doing the wrong thing.
"""
import re
import sys
import os
import time
import subprocess
from datetime import datetime

from app.application import AccuMateApp
from pages.main_page import MainPage
from workflows.file_workflows import load_test_file, load_config_file, save_as
from workflows.comm_workflows import configure_ip_and_connect
from workflows.security_workflows import enter_passcode


_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.*\S)\s*$")


def parse_scenario_markdown(path):
    """
    Extract an ordered list of plain-English step strings from a Markdown
    file. Only bullet ("- "/"* ") and numbered ("1. "/"1)") list items count
    as steps, in file order. Everything else - headers (#...), blank lines,
    fenced code blocks, and plain paragraph text - is treated as narration
    and ignored, so a scenario file can freely explain *why* it does
    something in prose without that prose being mistaken for a step.
    """
    steps = []
    in_code_block = False

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if not stripped:
                continue

            match = _LIST_ITEM_RE.match(line)
            if match:
                steps.append(match.group(1))

    return steps


# Each pattern is matched (case-insensitively, whole-string) against one
# step. Registration order matters when patterns could overlap - more
# specific patterns are registered before the generic ribbon-click catch-all.
_STEP_PATTERNS = []


def step(pattern):
    """Decorator registering a handler function for a step-matching regex."""
    compiled = re.compile(pattern, re.IGNORECASE)

    def register(fn):
        _STEP_PATTERNS.append((compiled, fn))
        return fn

    return register


@step(r"^load (?:the )?test file$")
def _step_load_test_file(app, page, m):
    load_test_file(app)


@step(r"^load (?:the )?config(?:uration)? file (?:at |from )?['\"]?(.+?)['\"]?$")
def _step_load_config_file(app, page, m):
    load_config_file(app, m.group(1))


@step(r"^connect to(?: the)?(?: device at)? ((?:\d{1,3}\.){3}\d{1,3})$")
def _step_connect_to_ip(app, page, m):
    ip_address = m.group(1)
    if not configure_ip_and_connect(app, ip_address):
        raise RuntimeError(f"Failed to establish a live connection to {ip_address}")


@step(r"^save (?:the (?:file|config(?:uration)?) )?as ['\"]?(.+?)['\"]?$")
def _step_save_as(app, page, m):
    save_as(app, m.group(1))


@step(r"^enter(?: the)? passcode ['\"]?(\S+)['\"]?$")
def _step_enter_passcode(app, page, m):
    if not enter_passcode(app, m.group(1)):
        raise RuntimeError("Passcode was rejected")


@step(r"^(?:verify|assert|check)(?: that)? (?:the )?device is connected$")
def _step_assert_connected(app, page, m):
    if not app.wait_for_device_connection(timeout=10):
        raise AssertionError("Expected the device to be connected, but it is not")


@step(r"^(?:verify|assert|check)(?: that)? (?:the )?device is (?:not connected|offline|disconnected)$")
def _step_assert_disconnected(app, page, m):
    if app.is_device_connected():
        raise AssertionError("Expected the device to be offline, but it is connected")


@step(r"^select (?:the )?tree(?: path)? (.+)$")
def _step_select_tree_path(app, page, m):
    path_parts = [p.strip() for p in re.split(r"\s*(?:>|/|->)\s*", m.group(1)) if p.strip()]
    page.select_tree_path(path_parts)


@step(r"^select (?:the )?(?:list )?item ['\"]?(.+?)['\"]?$")
def _step_select_list_item(app, page, m):
    page.select_list_item(m.group(1))


@step(r"^(?:set|edit|change) ['\"]?(.+?)['\"]? to ['\"]?(.+?)['\"]?$")
def _step_edit_value(app, page, m):
    page.edit_value(m.group(1), m.group(2))


@step(r"^(?:verify|assert|check)(?: that)? ['\"]?(.+?)['\"]? (?:is|equals) ['\"]?(.+?)['\"]?$")
def _step_assert_value(app, page, m):
    target, expected = m.group(1), m.group(2)
    actual = page.get_value(target)
    if actual != expected:
        raise AssertionError(f"Expected '{target}' to be '{expected}', got '{actual}'")


@step(r"^wait (\d+(?:\.\d+)?) seconds?$")
def _step_wait(app, page, m):
    time.sleep(float(m.group(1)))


# Generic fallback: click a named ribbon button. Registered last since its
# pattern is intentionally broad ("click ... [button]").
@step(r"^click(?: the)? ['\"]?(.+?)['\"]?(?: ribbon)?(?: button)?$")
def _step_click_ribbon(app, page, m):
    page.click_ribbon(m.group(1))


def match_step(step_text):
    """Return (handler, match) for the first pattern matching step_text, or (None, None)."""
    stripped = step_text.strip()

    for pattern, handler in _STEP_PATTERNS:
        m = pattern.match(stripped)
        if m:
            return handler, m

    return None, None


def run_scenario(markdown_path):
    steps = parse_scenario_markdown(markdown_path)

    if not steps:
        print(f"[WARN] No steps found in {markdown_path}")
        return True

    print(f"[INFO] Parsed {len(steps)} step(s) from {markdown_path}")

    app = AccuMateApp()
    page = MainPage(app)
    failures = []

    try:
        for i, step_text in enumerate(steps, start=1):
            handler, m = match_step(step_text)

            if handler is None:
                print(f"[WARN] Step {i}: could not interpret '{step_text}' - skipping")
                failures.append((i, step_text, "unrecognized step"))
                continue

            print(f"[STEP] {i}/{len(steps)}: {step_text}")

            try:
                handler(app, page, m)
            except Exception as e:
                print(f"[ERROR] Step {i} ('{step_text}') failed: {e}")
                failures.append((i, step_text, str(e)))
                break  # stop early - later steps likely depend on this one
    finally:
        _teardown(app, markdown_path)

    print()
    if failures:
        print(f"[RESULT] FAILED - {len(failures)} issue(s):")
        for i, step_text, err in failures:
            print(f"  step {i}: '{step_text}' -> {err}")
        return False

    print(f"[RESULT] PASSED - all {len(steps)} step(s) completed")
    return True


def _teardown(app, markdown_path):
    print("[DEBUG] Taking screenshot before teardown...")

    try:
        win = app.get_window()
        scenario_name = os.path.splitext(os.path.basename(markdown_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("screenshots", exist_ok=True)
        path = f"screenshots/{scenario_name}_{timestamp}.png"
        win.capture_as_image().save(path)
        print(f"[DEBUG] Screenshot saved: {path}")
    except Exception as e:
        print(f"[WARN] Screenshot failed: {e}")

    print("[DEBUG] Closing application...")

    try:
        pid = app.get_window().process_id()
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[WARN] Failed to kill process: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scenario_runner.py <scenario.md>")
        sys.exit(2)

    success = run_scenario(sys.argv[1])
    sys.exit(0 if success else 1)
