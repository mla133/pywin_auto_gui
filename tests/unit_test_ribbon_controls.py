import pytest


@pytest.mark.parametrize("button_name", [
    "Document Options",
    "General Options",
    "Retry Comm",
])

def test_click_ribbon_button(page, button_name):
    """
    Smoke test for ribbon buttons.
    Verifies that clicking does not raise exceptions.
    """

    print(f"[TEST] Checking ribbon button: {button_name}")

    if not page.is_ribbon_enabled(button_name):
        print(f"[TEST] Button disabled (expected): {button_name}")
        return

    page.click_ribbon(button_name)

