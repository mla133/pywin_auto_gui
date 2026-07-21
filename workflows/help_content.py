"""
Non-UI verification of AccuMate's compiled Help file (AccuMate.CHM) content.

Unlike workflows/help_viewer.py (which drives the live Help window via
UIA/win32), this module reads the CHM's actual page content directly by
decompiling it with the OS's built-in `hh.exe -decompile` (HTML Help), then
grep-style scanning the extracted .htm files. This is deliberately used for
scenarios/regression.md's H1/H2 (verifying injector 1-44 content in the DY/EA
command reference topics) instead of live UI automation: the check is
fundamentally about page CONTENT, not UI interaction, so reading the
decompiled HTML directly is both more reliable (the embedded
Internet_Explorer_Server content in the live Help viewer isn't practically
readable via win32/UIA text automation - see help_viewer.py's docstrings)
and avoids unnecessarily opening/focusing windows for a content-only check.

NOTE: The DY command's actual "Injector Dynamic Displays"/"Additive Batch
Volume"/"Additive Transaction Volume" tables are embedded as PNG images
(CmdDY_IV1/IV2.PNG, CmdDY_BV1/2.PNG, CmdDY_TV1/2.PNG) rather than HTML text,
so their specific injector-numbering content can't be grepped and was
instead manually visually verified (confirmed live: Current/Programmed Pulse
Rate go up to Injector 44 across CmdDY_IV1/IV2.PNG; Additive Batch/
Transaction Volume go up to Additive #44 across CmdDY_BV1/2.PNG and
CmdDY_TV1/2.PNG). This module only automates what IS plain HTML text: the
presence of those image references in command_DY.htm (a structural check
that the page hasn't been reorganized/renamed) and the EA command's fully
text-based Injector Group 2 (25-44) alarm mnemonic listing.
"""

import os
import subprocess
import tempfile
import shutil

from app.application import APP_EXE

_CHM_PATH = os.path.join(os.path.dirname(APP_EXE.replace("\\\\", "\\")), "AccuMate.CHM")


def decompile_chm(chm_path=None, dest_dir=None):
    """
    Decompile the AccuMate.CHM help file into a temp directory using the
    Windows-builtin `hh.exe -decompile <dir> <chm>` command, returning the
    directory path. Caller is responsible for cleanup (or use the
    `decompiled_chm` context manager below, which cleans up automatically).
    """
    chm_path = chm_path or _CHM_PATH
    if not os.path.isfile(chm_path):
        raise FileNotFoundError(f"AccuMate.CHM not found at {chm_path!r}")

    dest_dir = dest_dir or tempfile.mkdtemp(prefix="accumate_chm_")

    # hh.exe -decompile doesn't reliably report failure via exit code (it's
    # a GUI-less helper built into HTML Help), so confirm success by
    # checking that at least one .htm file actually landed in dest_dir
    # afterward, rather than trusting the process return code alone.
    subprocess.run(["hh.exe", "-decompile", dest_dir, chm_path], timeout=30)

    if not any(f.lower().endswith(".htm") for f in os.listdir(dest_dir)):
        raise RuntimeError(
            f"hh.exe -decompile did not extract any .htm files from {chm_path!r} into {dest_dir!r}"
        )

    return dest_dir


class decompiled_chm:
    """Context manager: decompile the CHM into a temp dir, clean up on exit."""

    def __init__(self, chm_path=None):
        self.chm_path = chm_path
        self.dest_dir = None

    def __enter__(self):
        self.dest_dir = decompile_chm(self.chm_path)
        return self.dest_dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.dest_dir and os.path.isdir(self.dest_dir):
            shutil.rmtree(self.dest_dir, ignore_errors=True)
        return False


def read_help_page(dest_dir, page_filename):
    """Read a single decompiled .htm page's raw text content."""
    path = os.path.join(dest_dir, page_filename)
    with open(path, encoding="windows-1252", errors="replace") as f:
        return f.read()
