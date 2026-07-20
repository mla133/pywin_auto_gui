import time

from controls.ribbon_controls import click_ribbon_button, is_ribbon_button_enabled

# The new view opened by "Retrieve Totalizers" is a new MDI child frame with
# this MFC-generated class name (confirmed live), titled "<doc>:N" where N
# increments per open view (e.g. "AL4ConfigFile1:1" is the original config
# view, "AL4ConfigFile1:2" appears after Retrieve Totalizers). Detecting via
# a NEW top-level window whose title merely contains "Totalizer" is NOT
# reliable - clicking the ribbon button also (harmlessly) surfaces a
# 'tooltips_class32' window whose title is the button's own tooltip text
# ("Retreive Totalizers", note the app's own typo), which looks like a
# false-positive match if title substring matching alone is used.
_MDI_CHILD_VIEW_CLASS = "AfxFrameOrView110su"


def retrieve_totalizers(app_obj, timeout=20):
    """
    Click the ribbon "Retrieve Totalizers" button and wait for AccuLoad's
    totalizer data to be downloaded and displayed in a new MDI child view.

    Detects success via a NEW `_MDI_CHILD_VIEW_CLASS` child window appearing
    under the main frame (confirmed live: this class name/pattern, not a
    generic title-substring match on top-level windows, which false-positive
    matches the ribbon button's own tooltip text "Retreive Totalizers").

    Returns the new view's win32 wrapper if one appears within `timeout`
    seconds, or raises RuntimeError otherwise (including if the ribbon
    button itself is disabled, e.g. because the device isn't connected).
    """
    win = app_obj.get_window()
    uia_win = app_obj.get_uia_window()

    if not is_ribbon_button_enabled(uia_win, "Retrieve Totalizers"):
        raise RuntimeError(
            "'Retrieve Totalizers' ribbon button is disabled - device likely not connected"
        )

    existing_titles = set()
    for ctrl in win.descendants(class_name=_MDI_CHILD_VIEW_CLASS):
        try:
            existing_titles.add(ctrl.window_text())
        except Exception:
            continue

    print("[STEP] Clicking ribbon 'Retrieve Totalizers'")
    click_ribbon_button(uia_win, "Retrieve Totalizers")

    start = time.time()
    while time.time() - start < timeout:
        try:
            for ctrl in win.descendants(class_name=_MDI_CHILD_VIEW_CLASS):
                title = ctrl.window_text()
                if title and title not in existing_titles:
                    return ctrl
        except Exception:
            pass

        time.sleep(0.5)

    raise RuntimeError(
        f"No new totalizers view appeared within {timeout}s after clicking "
        "'Retrieve Totalizers'"
    )
