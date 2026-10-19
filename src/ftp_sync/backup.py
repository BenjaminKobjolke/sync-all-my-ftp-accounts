"""Backs up each store once per run, right before its first write."""

import shutil
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from ftp_sync.app_logger import AppLogger


class BackupCoordinator:
    def __init__(self, backup_root: Path) -> None:
        self._dir = backup_root / datetime.now().strftime("%Y%m%d_%H%M%S")
        self._done: set[str] = set()

    def backup_file(self, path: Path) -> None:
        self._once(str(path), path.name, lambda target: shutil.copy2(path, target))

    def backup_registry(self, hkcu_key: str, file_name: str) -> None:
        self._once(
            hkcu_key,
            file_name,
            lambda target: subprocess.run(
                ["reg", "export", f"HKCU\\{hkcu_key}", str(target), "/y"],
                check=True,
                capture_output=True,
            ),
        )

    def _once(self, source: str, file_name: str, write: Callable[[Path], object]) -> None:
        if source in self._done:
            return
        self._dir.mkdir(parents=True, exist_ok=True)
        target = self._dir / file_name
        write(target)
        self._done.add(source)
        AppLogger.info(f"Backup: {target}")
