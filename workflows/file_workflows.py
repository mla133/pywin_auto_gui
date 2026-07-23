import time
import os
import re
from pywinauto.keyboard import send_keys
from pywinauto import Application

from controls.ribbon_controls import find_app_button
from controls.common_controls import get_tree

TEST_FILE = os.path.normpath(
    r"C:\\Users\\allenma\\Documents\\Testing\\Auto_Test.AL4"
    )

# The Application Button's backstage menu is entirely custom-drawn (no UIA
# text/automation_id exposed for any of its items - a `.descendants()` scan
# of the popup's own HWNDs after opening returns 0 elements), so items must
# be clicked by coordinate. These offsets are relative to the Application
# Button's own rectangle (found via UIA, see find_app_button), which keeps
# them correct regardless of the main window's position/size on screen.
_APP_MENU_ITEM_X_OFFSET = 85
# Row spacing in this popup is NOT uniform (confirmed via a live screenshot
# measurement: ~43-44px between the first few items, widening to ~47-49px
# from "Save As..." onward, likely due to a visual separator/section break
# in the real menu). A single fixed row-height multiplier undershoots or
# overshoots depending on target index - this was the root cause of a real,
# 100%-reproducible bug where clicking "Close" (index 6) actually landed on
# "About" (index 7) instead. Each item's y-offset (from the Application
# Button's own bottom edge) is hardcoded here from that measurement instead
# of computed from a uniform row height.
_APP_MENU_ITEM_Y_OFFSETS = [21, 65, 108, 151, 198, 247, 295, 343]
# Menu item order: New(0), Open...(1), Save(2), Save As...(3),
# Firmware Update...(4), Print(5), Close(6), About(7)
_APP_MENU_NEW_INDEX = 0
_APP_MENU_SAVE_AS_INDEX = 3
_APP_MENU_CLOSE_INDEX = 6
_APP_MENU_ABOUT_INDEX = 7

# "New" (and "Print") show a right-pointing fly-out arrow, but a plain
# click_input() on "New" does NOT open that fly-out - it immediately
# executes the default action (creates a blank AccuMate Config File, same
# as Ctrl+N). The fly-out IS reachable via keyboard: Down (focus "New") ->
# Right (expand fly-out) -> Down x N (move to the desired item) -> Enter
# (select) - see _click_new_document_flyout_item(). An earlier version
# drove this via mouse coordinates (a held-mouse-button drag over
# hardcoded pixel Y-offsets, since a plain hover/click never opened the
# fly-out either) but that was found to be unreliable: even with careful
# stepped movement and dwell tuning, it would deterministically land on
# the wrong item depending on app state (confirmed live via
# tests/test_regression_d.py & test_regression_e.py both intermittently
# creating the wrong document type). Keyboard navigation sidesteps pixel
# hit-testing entirely and was confirmed reliable across every app state
# tested. Real on-screen/selection order confirmed live: "AccuMate Config
# File" (0), "Report Configuration" (1), "Translation" (2), "Equation
# Set" (3), "Driver Database" (4).
_NEW_FLYOUT_ACCUMATE_CONFIG_INDEX = 0
_NEW_FLYOUT_REPORT_CONFIGURATION_INDEX = 1
_NEW_FLYOUT_TRANSLATION_INDEX = 2
_NEW_FLYOUT_EQUATION_SET_INDEX = 3
_NEW_FLYOUT_DRIVER_DATABASE_INDEX = 4


# How long a brand-new document takes to populate its Config Directory tree.
# Unlike opening a saved file, "New" creates a blank in-memory document that
# immediately attempts a device connection using default comm settings
# before the tree/list views populate - live testing showed this can take
# ~20s (longer than the ~10-13s load_config_file delay), so new_config_file
# polls rather than using a short fixed sleep.
_NEW_CONFIG_TREE_TIMEOUT = 40

# Seen when closing a document that AccuMate considers modified (e.g. after
# a connection attempt touched in-memory state) - "&Yes"/"&No" match by
# control_id (IDYES=6, IDNO=7), same reasoning as the Save As overwrite
# confirmation below: accelerator-prefixed titles ("&No") shouldn't be
# matched by exact text.
_SAVE_CHANGES_DIALOG_TITLE_RE = ".*(ave changes|onfirm).*"
_IDNO_CONTROL_ID = 7

_SAVE_AS_DIALOG_TITLE = "Save As"
_SAVE_AS_DIALOG_CLASS = "#32770"
_SAVE_AS_FILENAME_AUTO_ID = "1001"
_SAVE_AS_SAVE_BUTTON_AUTO_ID = "1"

# Loading an old-format .AL4 (created with an earlier AccuMate version)
# triggers a real, confirmed-live migration flow:
#   1. A notice dialog (title "AccuMate", #32770) - "This configuration was
#      saved with an old version of AccuMate and will be updated to the
#      X.Y.Z version now." - OK dismisses it and starts the migration.
#   2. A "Migrating AccuMate Configuration... [NN%]" progress window (same
#      dynamic-class/title-carries-percentage shape as the PUSH/PULL
#      progress window - see terminal_emulator.wait_for_progress_dialog_to_close)
#      counts up, then closes.
#   3. A completion dialog (title "AccuMate", #32770) - "The opened AccuMate
#      IV configuration was successfully updated.\n\nA new file named
#      '<name>' was created in the same directory as the original file." -
#      OK dismisses it. The ORIGINAL document view is then closed (blank,
#      no tree/tabs) - the migrated file is saved to disk but NOT
#      automatically reopened, so a caller needs to explicitly open it
#      (e.g. via load_config_file) to inspect/verify the converted config.
_MIGRATION_DIALOG_TITLE = "AccuMate"
_MIGRATION_DIALOG_CLASS = "#32770"
_MIGRATION_NOTICE_TEXT = "old version of AccuMate"
_MIGRATION_PROGRESS_TITLE_SUBSTRING = "Migrating AccuMate Configuration"
_MIGRATION_COMPLETE_TEXT_RE = r"new file named '([^']+)'"


def _click_button_by_title(dlg, title):
    """
    Click a Button descendant matching `title` on an already-resolved
    dialog wrapper (child_window() only exists on WindowSpecification, not
    a resolved wrapper's return value - see project conventions/comments
    elsewhere in this file - so this scans .descendants() and matches
    manually instead).
    """
    for ctrl in dlg.descendants(class_name="Button"):
        try:
            if ctrl.window_text() == title:
                ctrl.click_input()
                return
        except Exception:
            continue
    raise RuntimeError(f"Could not find a '{title}' button on dialog {dlg.window_text()!r}")


def load_and_migrate_old_config_file(app_obj, config_path, close_existing=True, migration_timeout=120):
    """
    Open an old-format .AL4 config file (created with an earlier AccuMate
    version) and drive the real migration flow described above to
    completion, returning the full path to the newly-created, migrated
    file (same directory as `config_path`, named per the completion
    dialog's own message).

    Does NOT wait for the Config Directory tree afterward (unlike
    load_config_file) - live testing confirmed the original document view
    closes once migration completes, so there's no tree to wait for; open
    the returned migrated path (e.g. via load_config_file) to inspect it.

    Raises RuntimeError if the expected notice/completion dialogs, or the
    migrated filename within the completion dialog's message, aren't found.
    """
    from workflows.terminal_emulator import wait_for_progress_dialog_to_close

    config_path = os.path.normpath(config_path)

    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"AccuMate config file not found: {config_path}")

    if close_existing:
        close_current_file(app_obj)

    open_file_dialog(app_obj, config_path)

    print("[STEP] Waiting for old-version migration notice dialog")
    notice_dlg_spec = app_obj.app.window(title=_MIGRATION_DIALOG_TITLE, class_name=_MIGRATION_DIALOG_CLASS)
    notice_dlg_spec.wait("exists visible ready", timeout=migration_timeout)
    notice_dlg = notice_dlg_spec.wrapper_object()

    notice_text = " ".join(s.window_text() for s in notice_dlg.descendants(class_name="Static"))
    if _MIGRATION_NOTICE_TEXT not in notice_text:
        raise RuntimeError(
            f"Expected an old-version migration notice dialog, got unrecognized text: {notice_text!r}"
        )

    print(f"[INFO] Migration notice: {notice_text!r}")
    _click_button_by_title(notice_dlg, "OK")

    print("[STEP] Waiting for the 'Migrating AccuMate Configuration' progress window to close")
    completed = wait_for_progress_dialog_to_close(
        app_obj, timeout=migration_timeout, title_substrings=(_MIGRATION_PROGRESS_TITLE_SUBSTRING,)
    )
    if not completed:
        raise RuntimeError(
            f"Migration did not complete within {migration_timeout}s (progress window still open)"
        )

    print("[STEP] Waiting for migration completion dialog")
    complete_dlg_spec = app_obj.app.window(title=_MIGRATION_DIALOG_TITLE, class_name=_MIGRATION_DIALOG_CLASS)
    complete_dlg_spec.wait("exists visible ready", timeout=migration_timeout)
    complete_dlg = complete_dlg_spec.wrapper_object()

    complete_text = " ".join(s.window_text() for s in complete_dlg.descendants(class_name="Static"))
    match = re.search(_MIGRATION_COMPLETE_TEXT_RE, complete_text)
    if not match:
        raise RuntimeError(
            f"Could not find migrated filename in completion dialog text: {complete_text!r}"
        )

    migrated_filename = match.group(1)
    migrated_path = os.path.join(os.path.dirname(config_path), migrated_filename)

    print(f"[INFO] Migration completed: {migrated_path}")
    _click_button_by_title(complete_dlg, "OK")
    time.sleep(0.5)

    return migrated_path

def open_file_dialog(app_obj, file_path):
    win = app_obj.get_window()
    win.set_focus()

    print("[DEBUG] Triggering Ctrl-O")
    win.type_keys("^o", set_foreground=True)

    time.sleep(0.5)

    # Step 1: Attach to the dialog using Win32 backend
    dlg = app_obj.app.window(class_name="#32770")
    dlg.wait("visible enabled ready", timeout=10)

    # Get the HWND of the dialog
    hwnd = dlg.handle

    print(f"[DEBUG] Dialog HWND = {hex(hwnd)}")

    # Step 2: Attach to the SAME dialog using UIA backend
    uia_app = Application(backend="uia").connect(handle=hwnd)
    uia_dlg = uia_app.window(handle=hwnd)

    print("[DEBUG] Locating filename edit box via UIA")

    # Step 3: Find the Edit control under UIA.
    # NOTE: a plain control_type="Edit" lookup is ambiguous in modern
    # Explorer-style Open dialogs (list view column headers, the search box,
    # etc. are also exposed as Edit controls). automation_id "1148" is the
    # standard Windows common-dialog id for the filename edit box and is
    # unique regardless of how many items/columns are shown.
    filename_edit = uia_dlg.child_window(auto_id="1148", control_type="Edit")

    if not filename_edit.exists():
        raise RuntimeError("UIA Edit control not found in file dialog")

    filename_edit.set_edit_text(file_path)

    print("[DEBUG] Clicking Open")
    # NOTE: title="Open" alone is ambiguous — the "Open" split-button
    # dropdown arrows on the list view items also expose that title. The
    # real dialog commit button is automation_id "1" (standard Windows
    # common-dialog IDOK).
    uia_dlg.child_window(auto_id="1", control_type="Button").click_input()

def load_test_file(app_obj):
    open_file_dialog(app_obj, TEST_FILE)


def load_config_file(app_obj, config_path, close_existing=True, wait_for_tree=True, tree_timeout=_NEW_CONFIG_TREE_TIMEOUT):
    """
    Open an arbitrary, previously-saved AccuMate config file (e.g.
    DefaultAL4.dat or a specific .AL4 file) via the same Open-file dialog
    flow as load_test_file. Useful for device-connectivity checks, since a
    saved config may already carry the real device's connection settings
    (IP/COM port/etc.) rather than the generic Auto_Test.AL4 test data.

    AccuMate always has *some* document open (it auto-loads DefaultAL4.dat
    on startup), and re-opening a different file via Ctrl-O while a document
    is already open can pop an extra "save changes?" confirmation first -
    which the plain Ctrl-O -> #32770 Open-dialog wait below doesn't expect,
    so it just times out. By default (`close_existing=True`) this closes the
    currently-open document first (Application Button -> Close, NOT closing
    the app itself - see close_current_file), then opens the requested file
    in the same app instance. Pass `close_existing=False` to skip this (e.g.
    if a caller already knows nothing is open).

    By default (`wait_for_tree=True`) this also polls for the Config
    Directory tree to populate before returning - like new_config_file, the
    loaded document attempts its own device connection using its baked-in
    comm settings before the tree/list views populate, so a caller that
    immediately navigates the tree right after this returns can otherwise
    hit a real "tree node not found" race. Pass `wait_for_tree=False` to
    skip this (e.g. a caller that only cares about the Open dialog itself).
    """
    config_path = os.path.normpath(config_path)

    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"AccuMate config file not found: {config_path}")

    if close_existing:
        close_current_file(app_obj)

    open_file_dialog(app_obj, config_path)

    if wait_for_tree:
        start = time.time()
        while time.time() - start < tree_timeout:
            try:
                if get_tree(app_obj).roots():
                    return
            except Exception:
                pass
            time.sleep(1)
        raise RuntimeError(
            f"Config Directory tree did not populate within {tree_timeout}s after loading {config_path}"
        )


def _click_app_menu_item(app_obj, item_index):
    """
    Open the ribbon's Application Button backstage menu and click the item
    at `item_index` (0-based, in on-screen top-to-bottom order: New, Open...,
    Save, Save As..., ...).
    """
    win = app_obj.get_window()
    win.set_focus()
    time.sleep(0.3)

    uia_win = app_obj.get_uia_window()
    app_button = find_app_button(uia_win)
    app_button.click_input()
    time.sleep(1)  # let the (custom-drawn, non-UIA) popup finish rendering

    win_rect = win.rectangle()
    btn_rect = app_button.rectangle()

    x = (btn_rect.left - win_rect.left) + _APP_MENU_ITEM_X_OFFSET
    y = (btn_rect.bottom - win_rect.top) + _APP_MENU_ITEM_Y_OFFSETS[item_index]

    win.click_input(coords=(x, y))


def _click_new_document_flyout_item(app_obj, flyout_index):
    """
    Open the ribbon Application Button's backstage menu and select an item
    from "New"'s fly-out submenu (AccuMate Config File / Report
    Configuration / Translation / Equation Set / Driver Database - see
    _NEW_FLYOUT_*_INDEX constants).

    Uses pure keyboard navigation (Down to focus "New" -> Right to expand
    its fly-out -> Down `flyout_index` times -> Enter), NOT mouse
    coordinates. An earlier version drove this via a held-mouse-button
    drag gesture with hardcoded pixel Y-offsets per item (mouse hover was
    required since a plain click_input() on "New" just runs its default
    action instead of opening the fly-out) - live testing showed that
    approach was fundamentally flaky: even with a stepped drag and
    generous dwell times, it would sporadically (and *deterministically*,
    not randomly - retries with the same offset kept landing on the same
    wrong item depending on app state) select the wrong document type, or
    none at all. Keyboard navigation sidesteps pixel hit-testing entirely
    and was confirmed live to be 100% reliable across repeated trials in
    every app state tested.
    """
    win = app_obj.get_window()
    win.set_focus()
    time.sleep(0.3)

    uia_win = app_obj.get_uia_window()
    app_button = find_app_button(uia_win)
    app_button.click_input()
    time.sleep(1)  # let the (custom-drawn, non-UIA) popup finish rendering

    win.type_keys("{DOWN}")  # focus "New" (the backstage menu's first item)
    time.sleep(0.4)
    win.type_keys("{RIGHT}")  # expand New's fly-out submenu
    time.sleep(0.6)
    for _ in range(flyout_index):
        win.type_keys("{DOWN}")
        time.sleep(0.2)
    win.type_keys("{ENTER}")
    time.sleep(0.5)


def open_new_document_verified(app_obj, flyout_index, verify_fn, timeout=8, max_attempts=4):
    """
    Robust wrapper around _click_new_document_flyout_item(): the fly-out's
    per-item hit-testing was found to be flaky even with a stepped drag
    and generous dwell times (live testing showed the wrong document type
    - or no new document at all - created on a meaningful fraction of
    attempts, seemingly due to inherent OS menu-tracking timing variance
    rather than any single fixable offset/timing constant). Rather than
    chase a "perfect" offset/timing combination that doesn't seem to
    exist, this retries the whole click gesture up to `max_attempts`
    times, calling `verify_fn(app_obj)` (a callable that should return
    True once the *correct* document type is confirmed present, e.g. by
    checking window_text() for a type-specific substring) after each
    attempt. A wrong-type document created by a failed attempt is
    harmless - the next "New" click simply replaces it with a fresh
    document, so no explicit close/undo is needed between retries.
    """
    last_title = None
    for attempt in range(1, max_attempts + 1):
        _click_new_document_flyout_item(app_obj, flyout_index)

        start = time.time()
        while time.time() - start < timeout:
            try:
                if verify_fn(app_obj):
                    return
                last_title = app_obj.get_window().window_text()
            except Exception:
                pass
            time.sleep(0.4)

        print(f"[WARN] Attempt {attempt}/{max_attempts}: New fly-out item {flyout_index} "
              f"did not verify in time (last title seen: {last_title!r}) - retrying")

    raise RuntimeError(
        f"New fly-out item {flyout_index} did not produce the expected document "
        f"after {max_attempts} attempts (last title seen: {last_title!r})"
    )


def new_config_file(app_obj, timeout=_NEW_CONFIG_TREE_TIMEOUT):
    """
    Create a new, blank AccuMate Config File via the ribbon Application
    Button's "New" menu item.

    A plain click on "New" (no fly-out interaction) directly runs its
    default action, creating a new AccuMate Config File - "New" does have a
    fly-out submenu with other document types (see
    _click_new_document_flyout_item), but reaching it requires a held-mouse
    drag gesture, and AccuMate Config File is simply the default action a
    plain click already produces (confirmed live: identical resulting
    state, Config Directory tree populates the same way either path), so
    this keeps the simpler, already-working coordinate-click machinery
    rather than driving the fly-out unnecessarily.

    The new document starts completely blank (title has no filename, tree
    and list views report zero items) while AccuMate attempts an initial
    device connection using default comm settings; the Config
    Directory/System Directory/Arm N tree only populates once that settles
    (observed up to ~20s), so this polls for the tree to report at least
    one root node rather than assuming success immediately. Raises
    RuntimeError if the tree never populates within `timeout` seconds.
    """
    print("[STEP] Opening Application menu -> New")
    _click_app_menu_item(app_obj, _APP_MENU_NEW_INDEX)

    start = time.time()
    while time.time() - start < timeout:
        try:
            tree = get_tree(app_obj)
            if tree.roots():
                print("[INFO] New AccuMate Config File created")
                return
        except Exception:
            pass
        time.sleep(1)

    raise RuntimeError(
        f"New AccuMate Config File did not populate its Config Directory tree within {timeout}s"
    )


_ABOUT_DIALOG_TITLE_RE = ".*[Aa]bout.*AccuMate.*"


def close_current_file(app_obj, retries=3):
    """
    Close the currently-open AccuMate document via the Application Button's
    "Close" menu item - WITHOUT closing the application itself - so a
    different config/test file can be opened afterward in the same app
    instance (see load_config_file). If AccuMate considers the document
    modified, Close can pop a "save changes?" confirmation dialog first;
    that's answered "No" here, since an automated test run should never
    silently persist in-app changes back over a saved config file.

    Retries a few times: live testing (right after a fresh app launch)
    showed the coordinate-based click can land one row low, on "About"
    (item_index=7) instead of "Close" (item_index=6) - opening the About
    dialog instead, which then blocks the main frame ("enabled" check
    fails) and hangs any subsequent call forever. This is detected here
    (About dialog title match) and recovered from by closing it and
    retrying the Close click, rather than letting it hang.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        print("[STEP] Opening Application menu -> Close (current document only)")
        _click_app_menu_item(app_obj, _APP_MENU_CLOSE_INDEX)
        time.sleep(0.5)

        try:
            about_dlg_spec = app_obj.app.window(
                title_re=_ABOUT_DIALOG_TITLE_RE, class_name="#32770"
            )
            if about_dlg_spec.exists(timeout=1):
                print(
                    f"[WARN] Attempt {attempt}/{retries}: Close menu click landed on "
                    "'About' instead - dismissing and retrying"
                )
                last_error = RuntimeError("Application menu click landed on 'About' dialog")
                try:
                    about_dlg_spec.wrapper_object().close()
                except Exception:
                    try:
                        app_obj.get_window().type_keys("{ESC}")
                    except Exception:
                        pass
                time.sleep(0.5)
                continue
        except Exception:
            pass

        break
    else:
        raise RuntimeError(
            f"Failed to close current document after {retries} attempts (kept landing on 'About')"
        ) from last_error

    try:
        confirm_dlg_spec = app_obj.app.window(
            title_re=_SAVE_CHANGES_DIALOG_TITLE_RE, class_name="#32770"
        )
        if not confirm_dlg_spec.exists(timeout=2):
            return
    except Exception:
        return

    print("[STEP] Dismissing 'save changes?' prompt with No (discard)")
    confirm_dlg = confirm_dlg_spec.wrapper_object()

    clicked = False
    for ctrl in confirm_dlg.descendants(class_name="Button"):
        try:
            if ctrl.control_id() == _IDNO_CONTROL_ID or "No" in ctrl.window_text():
                ctrl.click_input()
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        raise RuntimeError("Could not find 'No' button on save-changes confirmation dialog")

    time.sleep(0.5)


def open_about_dialog(app_obj, timeout=8):
    """
    Open the ribbon Application Button's "About" menu item (index 7) and
    return the resulting About dialog as a win32 WindowSpecification.

    This was previously only known as an accidental failure mode of
    close_current_file() (a mis-click landing here instead of "Close") -
    exposed here as a real, intentional helper since scenarios/regression.md
    G3-G5 need to verify the correct version number is shown after
    installing (see get_about_dialog_text/close_about_dialog).
    """
    _click_app_menu_item(app_obj, _APP_MENU_ABOUT_INDEX)

    dlg_spec = app_obj.app.window(title_re=_ABOUT_DIALOG_TITLE_RE, class_name="#32770")
    dlg_spec.wait("exists enabled visible ready", timeout=timeout)
    return dlg_spec


def get_about_dialog_text(app_obj, timeout=8):
    """
    Open the About dialog, concatenate all of its Static control text (which
    includes the version number, e.g. "Version 1.12"), close it again, and
    return that text. Used to confirm the installed AccuMate's About section
    reports the expected version after a fresh install (G3/G4/G5 step 1).
    """
    dlg_spec = open_about_dialog(app_obj, timeout=timeout)
    dlg = dlg_spec.wrapper_object()

    texts = []
    for ctrl in dlg.descendants(class_name="Static"):
        try:
            text = ctrl.window_text()
            if text:
                texts.append(text)
        except Exception:
            continue

    close_about_dialog(app_obj, dlg_spec)
    return "\n".join(texts)


def close_about_dialog(app_obj, dlg_spec=None):
    """Close the About dialog (OK button, falls back to Escape)."""
    try:
        if dlg_spec is None:
            dlg_spec = app_obj.app.window(title_re=_ABOUT_DIALOG_TITLE_RE, class_name="#32770")
        dlg = dlg_spec.wrapper_object()
        for ctrl in dlg.descendants(class_name="Button"):
            try:
                if "OK" in ctrl.window_text():
                    ctrl.click_input()
                    return
            except Exception:
                continue
        dlg.close()
    except Exception:
        try:
            app_obj.get_window().type_keys("{ESC}")
        except Exception:
            pass


def _open_save_as_dialog(app_obj, retries=3):
    """
    Open the ribbon Application Button -> "Save As..." menu item and wait
    for the resulting "Save As" common dialog. Retries a few times: the
    backstage menu is entirely custom-drawn (no UIA text/automation_id
    exposed for any of its items - see find_app_button/_click_app_menu_item),
    so the coordinate-based click can occasionally miss if the popup is
    still animating in, or land on nothing if the menu didn't open at all.
    Presses Escape between attempts to dismiss any stuck/mis-clicked menu.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            _click_app_menu_item(app_obj, _APP_MENU_SAVE_AS_INDEX)

            dlg_spec = app_obj.app.window(title=_SAVE_AS_DIALOG_TITLE, class_name=_SAVE_AS_DIALOG_CLASS)
            dlg_spec.wait("exists enabled visible ready", timeout=8)

            return dlg_spec
        except Exception as e:
            last_error = e
            print(f"[WARN] Attempt {attempt}/{retries} to open Save As dialog failed: {e}")
            try:
                app_obj.get_window().type_keys("{ESC}")
            except Exception:
                pass
            time.sleep(1)

    raise RuntimeError(f"Failed to open Save As dialog after {retries} attempts") from last_error


def save_as(app_obj, save_path):
    """
    Save the currently-open AccuMate document to a new path via the ribbon's
    Application Button -> "Save As..." menu item.

    NOTE: there's no dedicated ribbon button or keyboard accelerator for
    Save As - F12 and Ctrl+Shift+S both do nothing, and it isn't reachable
    via the classic Alt+F menu key either (this ribbon skin has no menu bar
    at all). The only path is the Application Button's backstage menu.

    `save_path` may include a directory; the standard Windows Save dialog
    accepts a full path typed into the filename field and will navigate
    there directly. Raises FileNotFoundError if the target directory
    doesn't exist, and RuntimeError if the save doesn't produce the
    expected file (e.g. the dialog failed to open/commit).
    """
    save_path = os.path.normpath(save_path)
    directory = os.path.dirname(save_path)

    if directory and not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory does not exist: {directory}")

    print("[STEP] Opening Application menu -> Save As...")
    dlg_spec = _open_save_as_dialog(app_obj)
    hwnd = dlg_spec.wrapper_object().handle

    uia_app = Application(backend="uia").connect(handle=hwnd)
    uia_dlg = uia_app.window(handle=hwnd)

    filename_edit = uia_dlg.child_window(auto_id=_SAVE_AS_FILENAME_AUTO_ID, control_type="Edit")
    if not filename_edit.exists():
        raise RuntimeError("UIA Edit control not found in Save As dialog")

    filename_edit.set_edit_text(save_path)

    print(f"[STEP] Saving as: {save_path}")
    uia_dlg.child_window(auto_id=_SAVE_AS_SAVE_BUTTON_AUTO_ID, control_type="Button").click_input()
    time.sleep(1)

    # If save_path already exists, this can trigger up to two overwrite
    # confirmations in sequence:
    #   1. The OS-level common-dialog "Confirm Save As" prompt (IDYES=6,
    #      button title is "&Yes" with an accelerator - NOT "Yes").
    #   2. AccuMate's own app-level confirmation, once it actually opens the
    #      file for writing.
    # Handle both, since not doing so leaves a stuck modal dialog that only
    # surfaces later as a screenshot/teardown timeout - not a clear failure
    # at the point it actually went wrong.
    for _ in range(2):
        try:
            confirm_dlg_spec = app_obj.app.window(title_re=".*(onfirm|verwrite).*", class_name="#32770")
            if not confirm_dlg_spec.exists(timeout=2):
                break
        except Exception:
            break

        print("[STEP] Confirming overwrite")
        confirm_dlg = confirm_dlg_spec.wrapper_object()

        # Prefer the standard IDYES control_id (6) - robust regardless of
        # the button's displayed accelerator text ("&Yes" vs "Yes").
        clicked = False
        for ctrl in confirm_dlg.descendants(class_name="Button"):
            try:
                if ctrl.control_id() == 6 or "Yes" in ctrl.window_text():
                    ctrl.click_input()
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            raise RuntimeError("Could not find 'Yes' button on overwrite confirmation dialog")

        time.sleep(1)

    if not os.path.isfile(save_path):
        raise RuntimeError(f"Save As did not create the expected file: {save_path}")

    print(f"[INFO] Saved: {save_path}")
