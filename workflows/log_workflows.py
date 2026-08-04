"""
scenarios/regression.md F1-F7 (Transaction/Event/Audit Trail log downloads,
License Status File upload/download).

Thin wrappers around workflows.file_transfer_workflows, following the exact
same pattern already live-verified for D6/D7 (driver_db_workflows.py) and
E4/E5/E8 (equation_workflows.py): these categories
("Transaction Log"/"Event Log"/"Audit Trail Log"/"License Status File") are
already present in file_transfer_workflows.DOWNLOAD_CATEGORY_IDS, and
upload_file()/download_file() are category-agnostic for upload (the upload
dialog has no category picker - only download does), so no new dialog
handling is needed here.

NOT YET LIVE-VERIFIED against a real device (see file_transfer_workflows.py
module docstring for the live-confirmed device-timeout finding that has
affected every real transfer attempt against 10.55.66.70 so far - these
functions are expected to hit the same limitation until it's resolved).
"""
from workflows.file_transfer_workflows import upload_file, download_file


def download_transaction_log(app_obj, save_path):
    """
    F1-F3: Download the Transaction Log from a connected AccuLoad via the
    ribbon "Download File From AccuLoad" button, selecting "Transaction
    Log" in the "File Download Selection" dialog.

    Returns the result dict from workflows.file_transfer_workflows.
    start_transfer(): {"message": str or None, "timed_out": bool}.
    """
    return download_file(app_obj, "Transaction Log", save_path)


def download_event_log(app_obj, save_path):
    """
    F4: Download the Event Log from a connected AccuLoad via the ribbon
    "Download File From AccuLoad" button, selecting "Event Log" in the
    "File Download Selection" dialog.

    Returns the result dict from workflows.file_transfer_workflows.
    start_transfer() - see download_transaction_log's docstring.
    """
    return download_file(app_obj, "Event Log", save_path)


def download_audit_trail_log(app_obj, save_path):
    """
    F5: Download the Audit Trail Log from a connected AccuLoad via the
    ribbon "Download File From AccuLoad" button, selecting "Audit Trail
    Log" in the "File Download Selection" dialog.

    Returns the result dict from workflows.file_transfer_workflows.
    start_transfer() - see download_transaction_log's docstring.
    """
    return download_file(app_obj, "Audit Trail Log", save_path)


def upload_license_status_file(app_obj, file_path):
    """
    F6: Upload a License Status File to a connected AccuLoad via the ribbon
    "Upload File to AccuLoad" button's "AccuMate File Transfer" window.

    Returns the result dict from workflows.file_transfer_workflows.
    start_transfer() - see download_transaction_log's docstring.
    """
    return upload_file(app_obj, file_path)


def download_license_status_file(app_obj, save_path):
    """
    F6/F7: Download the License Status File from a connected AccuLoad via
    the ribbon "Download File From AccuLoad" button, selecting "License
    Status File" in the "File Download Selection" dialog.

    Returns the result dict from workflows.file_transfer_workflows.
    start_transfer() - see download_transaction_log's docstring. F7 expects
    a "no information to pull" warning message rather than a real timeout/
    completion (requires the license dongle to be physically pulled from
    the device - not something this repo can arrange automatically).
    """
    return download_file(app_obj, "License Status File", save_path)
