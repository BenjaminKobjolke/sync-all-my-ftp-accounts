"""Which processes are running, via tasklist (stdlib only, no psutil)."""

import csv
import subprocess

from ftp_sync import constants
from ftp_sync.app_logger import AppLogger


def running_process_names() -> set[str]:
    """Lowercased executable names; empty when tasklist fails (the check is only a safety net)."""
    try:
        result = subprocess.run(
            constants.TASKLIST_COMMAND, capture_output=True, text=True, errors="replace"
        )
    except OSError as error:
        AppLogger.warning(f"Could not list running apps: {error}")
        return set()
    if result.returncode != 0:
        AppLogger.warning(f"Could not list running apps: tasklist exit {result.returncode}")
        return set()
    return {row[0].lower() for row in csv.reader(result.stdout.splitlines()) if row}
