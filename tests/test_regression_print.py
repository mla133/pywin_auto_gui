import os
import re

from pypdf import PdfReader

from workflows.file_workflows import new_config_file
from workflows.print_workflows import print_to_pdf
from workflows import general_options as go
from pages.main_page import MainPage
from controls.common_controls import get_list_row_texts, get_list

_PDF_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "print_output"))


def _pdf_path(name):
    os.makedirs(_PDF_DIR, exist_ok=True)
    return os.path.join(_PDF_DIR, name)


def _extract_all_text(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _find_line(text, needle):
    for line in text.splitlines():
        if needle in line:
            return line
    return None


def test_a23_print_security_level(app):
    """
    A23: General Options - Print Security Level. Toggling "Include security
    level on printout" adds/removes a trailing security-level column on
    every printed parameter line - verified against the "Number of Load
    Arms" row (System Layout Directory, always present in a blank config),
    whose printed line gains exactly one extra trailing token (the level,
    e.g. "1") when the option is enabled.
    """
    new_config_file(app)

    dlg = go.open_general_options(app)
    # "Limit Printout" is a global app preference, not part of the document
    # itself - "New Config File" does not reset it. A prior test run (e.g.
    # test_a26, which cycles through every option) can leave it set to
    # something other than "Print All", silently truncating this test's
    # printout to a handful of pages and hiding "Number of Load Arms"
    # entirely - confirmed live as the root cause of a spurious failure
    # when running this whole file back-to-back. Reset explicitly.
    go.set_limit_printout_value(dlg, "Print All")
    go.set_checkbox(dlg, go.CHECKBOX_INCLUDE_SECURITY_LEVEL_ON_PRINTOUT, True)
    go.close_general_options(dlg, accept=True)

    with_path = print_to_pdf(app, _pdf_path("a23_with_security_level.pdf"))
    with_text = _extract_all_text(with_path)
    with_line = _find_line(with_text, "Number of Load Arms")
    assert with_line is not None, "Could not find 'Number of Load Arms' line in printed PDF"

    dlg = go.open_general_options(app)
    go.set_checkbox(dlg, go.CHECKBOX_INCLUDE_SECURITY_LEVEL_ON_PRINTOUT, False)
    go.close_general_options(dlg, accept=True)

    without_path = print_to_pdf(app, _pdf_path("a23_without_security_level.pdf"))
    without_text = _extract_all_text(without_path)
    without_line = _find_line(without_text, "Number of Load Arms")
    assert without_line is not None, "Could not find 'Number of Load Arms' line in printed PDF"

    with_tokens = with_line.split()
    without_tokens = without_line.split()

    print(f"[INFO] With security level column: {with_tokens}")
    print(f"[INFO] Without security level column: {without_tokens}")

    assert len(with_tokens) == len(without_tokens) + 1, (
        "Expected exactly one extra trailing token (security level) when "
        f"the column is enabled, got with={with_tokens} without={without_tokens}"
    )
    assert with_tokens[-1] in {"1", "2", "3", "4", "5"}, (
        f"Expected the extra trailing token to be a security level digit, got: {with_tokens[-1]}"
    )
    assert with_tokens[:-1] == without_tokens, (
        "Expected the line to be otherwise identical aside from the trailing security level"
    )


def test_a25_print_unused_recipes(app):
    """
    A25: General Options - Print Unused Recipes. Setting Recipe 01's
    "Recipe Used" value to "Not Used" and enabling "Suppress printing
    unused recipes" removes all mention of that recipe (searched via its
    "Recipe Name" value, "Recipe 1") from the printout; disabling the
    option re-includes it.
    """
    new_config_file(app)
    page = MainPage(app)

    page.select_tree_path(["Recipe Directory", "Recipe 01"])
    page.set_dropdown_value_by_typeahead("Recipe Used", "n")

    lst = get_list(app)
    row = get_list_row_texts(lst, 0)
    assert "Not Used" in row, f"Failed to set Recipe 01 'Recipe Used' to 'Not Used', got: {row}"

    # A distinctive, unique marker rather than the default "Recipe 1" name -
    # "Recipe 1" alone is too generic a substring and false-matches
    # unrelated printed text elsewhere (e.g. "Recipe 1 Injector" headers in
    # the Recipe Additives Directory section, confirmed live), so renaming
    # to something unmistakable makes the printout search unambiguous.
    unique_recipe_name = "ZZMARKA25TEST"
    page.edit_program_code_data("Recipe Name", unique_recipe_name)

    recipe_name_row = get_list_row_texts(lst, 1)
    assert "Recipe Name" in recipe_name_row
    recipe_name = recipe_name_row[2]
    assert recipe_name == unique_recipe_name, f"Failed to rename Recipe 01, got: {recipe_name_row}"
    print(f"[INFO] Recipe 01 name to search for: '{recipe_name}'")

    dlg = go.open_general_options(app)
    # See test_a23's comment: "Limit Printout" is a global app preference
    # that survives "New Config File" and can leak in from a prior test run.
    go.set_limit_printout_value(dlg, "Print All")
    go.set_checkbox(dlg, go.CHECKBOX_SUPPRESS_PRINTING_UNUSED_RECIPES, True)
    go.close_general_options(dlg, accept=True)

    suppressed_path = print_to_pdf(app, _pdf_path("a25_suppressed.pdf"))
    suppressed_text = _extract_all_text(suppressed_path)
    recipe_suppressed = recipe_name not in suppressed_text
    assert recipe_suppressed, (
        f"Expected unused recipe {recipe_name!r} to be suppressed from the printout"
    )

    dlg = go.open_general_options(app)
    go.set_checkbox(dlg, go.CHECKBOX_SUPPRESS_PRINTING_UNUSED_RECIPES, False)
    go.close_general_options(dlg, accept=True)

    included_path = print_to_pdf(app, _pdf_path("a25_included.pdf"))
    included_text = _extract_all_text(included_path)
    recipe_included = recipe_name in included_text
    assert recipe_included, (
        f"Expected unused recipe {recipe_name!r} to be included in the printout "
        "once suppression is disabled"
    )


def test_a26_limit_printout(app):
    """
    A26: General Options - Limit Printout. For each "Limit printout of
    parameters to:" option, prints the config and verifies only parameters
    of the specified security level(s) or higher appear - checked via the
    per-line trailing security-level digit (see test_a23), which requires
    the "Include security level on printout" option enabled so the digit is
    present to check against.
    """
    new_config_file(app)

    dlg = go.open_general_options(app)
    go.set_checkbox(dlg, go.CHECKBOX_INCLUDE_SECURITY_LEVEL_ON_PRINTOUT, True)
    go.close_general_options(dlg, accept=True)

    # Value -> minimum security level that should appear in the printout.
    limit_options = {
        "Print All": 1,
        "Level 2 and above": 2,
        "Level 3 and above": 3,
        "Level 4 and above": 4,
        "Level 5": 5,
    }

    line_pattern = re.compile(r"^\s*\d{3}\S.*\s([1-5])\s*$", re.MULTILINE)

    for option, min_level in limit_options.items():
        dlg = go.open_general_options(app)
        go.set_limit_printout_value(dlg, option)
        assert go.get_limit_printout_value(dlg) == option
        go.close_general_options(dlg, accept=True)

        safe_name = option.lower().replace(" ", "_").replace(":", "")
        path = print_to_pdf(app, _pdf_path(f"a26_{safe_name}.pdf"))
        text = _extract_all_text(path)

        levels_found = {int(m) for m in line_pattern.findall(text)}
        print(f"[INFO] '{option}' -> security levels found in printout: {sorted(levels_found)}")

        assert levels_found, f"No parameter lines with a recognizable security level found for '{option}'"
        below_min = {lvl for lvl in levels_found if lvl < min_level}
        assert not below_min, (
            f"'{option}' should only print level {min_level}+ parameters, "
            f"but found levels below that: {sorted(below_min)}"
        )
