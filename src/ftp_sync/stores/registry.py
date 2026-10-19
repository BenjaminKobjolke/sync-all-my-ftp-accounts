"""Builds the list of all known stores from Settings."""

from ftp_sync.backup import BackupCoordinator
from ftp_sync.config.settings import Settings
from ftp_sync.stores.account_store import AccountStore
from ftp_sync.stores.filezilla_store import FileZillaStore
from ftp_sync.stores.fman_store import FmanStore
from ftp_sync.stores.nppftp_store import NppFtpStore
from ftp_sync.stores.winscp_store import WinScpStore


def build_stores(settings: Settings, backup: BackupCoordinator) -> list[AccountStore]:
    return [
        WinScpStore(settings.winscp_key, backup),
        FileZillaStore(settings.filezilla_path, backup),
        NppFtpStore(settings.nppftp_path, backup),
        FmanStore(settings.fman_path, backup),
    ]
