"""Shared fixtures: sample accounts and a backup coordinator writing to tmp_path."""

from pathlib import Path

import pytest

from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import FtpAccount, FtpProtocol


def make_account(**overrides: object) -> FtpAccount:
    values: dict[str, object] = {
        "name": "site",
        "host": "ftp.example.com",
        "user": "bob",
        "password": "p@ss:w/rd ä",
        "port": 21,
        "protocol": FtpProtocol.FTP,
        "folder": "",
        "remote_dir": "",
    }
    values.update(overrides)
    return FtpAccount(**values)  # type: ignore[arg-type]


@pytest.fixture
def backup(tmp_path: Path) -> BackupCoordinator:
    return BackupCoordinator(tmp_path / "backups")
