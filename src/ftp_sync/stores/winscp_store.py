"""WinSCP sessions in HKCU registry. Session key names are %-escaped; '/' separates folders."""

import winreg
from urllib.parse import quote, unquote

from ftp_account_readers import is_winscp_available, read_winscp
from ftp_account_readers.helpers import join_folder, unique_name
from ftp_account_readers.winscp_password import encrypt

from ftp_sync import constants as c
from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol

# WinSCP accepts any %XX escape when reading; keep the characters it leaves readable.
_SAFE_NAME_CHARS = "/@-_.~()"


class WinScpStore:
    kind = AppKind.WINSCP

    def __init__(self, sessions_key: str, backup: BackupCoordinator) -> None:
        self._key = sessions_key
        self._backup = backup

    def is_available(self) -> bool:
        return is_winscp_available(self._key)

    def supports(self, protocol: FtpProtocol) -> bool:
        return True

    def load(self) -> list[FtpAccount]:
        return read_winscp(self._key)

    def add(self, account: FtpAccount) -> None:
        self._backup.backup_registry(self._key, "winscp_sessions.reg")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self._key) as root:
            taken = {unquote(n) for n in self._session_names(root)}
            full_name = unique_name(join_folder(account.folder, account.name), taken)
            with winreg.CreateKey(root, quote(full_name, safe=_SAFE_NAME_CHARS)) as session:
                for name, value in _values(account).items():
                    kind = winreg.REG_DWORD if isinstance(value, int) else winreg.REG_SZ
                    winreg.SetValueEx(session, name, 0, kind, value)

    @staticmethod
    def _session_names(root: winreg.HKEYType) -> list[str]:
        return [winreg.EnumKey(root, i) for i in range(winreg.QueryInfoKey(root)[0])]


def _values(account: FtpAccount) -> dict[str, str | int]:
    is_ftp = account.protocol is not FtpProtocol.SFTP
    values: dict[str, str | int] = {
        c.WINSCP_HOST: account.host,
        c.WINSCP_PORT: account.port,
        c.WINSCP_USER: account.user,
        c.WINSCP_PASSWORD: encrypt(account.host, account.user, account.password),
        c.WINSCP_FS_PROTOCOL: c.WINSCP_FS_FTP if is_ftp else c.WINSCP_FS_SFTP,
        c.WINSCP_FTPS: c.WINSCP_FTPS_EXPLICIT
        if account.protocol is FtpProtocol.FTPS
        else c.WINSCP_FTPS_NONE,
    }
    if account.remote_dir:
        values[c.WINSCP_REMOTE_DIR] = account.remote_dir
    return values
