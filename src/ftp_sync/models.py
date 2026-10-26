"""Domain types shared by every credential store."""

from enum import StrEnum

from ftp_account_readers import FtpAccount as FtpAccount
from ftp_account_readers import FtpProtocol as FtpProtocol

from ftp_sync import constants


class AppKind(StrEnum):
    WINSCP = "winscp"
    FILEZILLA = "filezilla"
    NPPFTP = "nppftp"
    FMAN = "fman"
    ALL_INKL = "allinkl"
    DEPLOY_TOOL = "deploytool"

    @property
    def label(self) -> str:
        return constants.APP_LABELS[self.value]

    @property
    def is_writable(self) -> bool:
        """False for remote sources that can only be read (no process to close either)."""
        return self not in (AppKind.ALL_INKL, AppKind.DEPLOY_TOOL)

    @property
    def process_name(self) -> str:
        return constants.APP_PROCESS_NAMES[self.value]
