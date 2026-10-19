"""WinSCP sessions in HKCU registry. Session key names are %-escaped; '/' separates folders."""

import winreg
from urllib.parse import quote, unquote

from ftp_sync import constants as c
from ftp_sync.app_logger import AppLogger
from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol
from ftp_sync.stores import winscp_password
from ftp_sync.stores.account_store import join_folder, parse_port, unique_name

# WinSCP accepts any %XX escape when reading; keep the characters it leaves readable.
_SAFE_NAME_CHARS = "/@-_.~()"


class WinScpStore:
    kind = AppKind.WINSCP

    def __init__(self, sessions_key: str, backup: BackupCoordinator) -> None:
        self._key = sessions_key
        self._backup = backup

    def is_available(self) -> bool:
        try:
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._key))
            return True
        except OSError:
            return False

    def supports(self, protocol: FtpProtocol) -> bool:
        return True

    def load(self) -> list[FtpAccount]:
        accounts = []
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._key) as root:
            for raw_name in self._session_names(root):
                if raw_name == c.WINSCP_DEFAULT_SETTINGS_SESSION:
                    continue
                with winreg.OpenKey(root, raw_name) as session:
                    account = _parse(unquote(raw_name), session)
                if account is not None:
                    accounts.append(account)
        return accounts

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


def _read(session: winreg.HKEYType, name: str) -> str | int | None:
    try:
        value: str | int = winreg.QueryValueEx(session, name)[0]
        return value
    except OSError:
        return None


def _parse(full_name: str, session: winreg.HKEYType) -> FtpAccount | None:
    host, user = _read(session, c.WINSCP_HOST), _read(session, c.WINSCP_USER) or ""
    if not isinstance(host, str) or not host:
        return None
    protocol = _protocol(_read(session, c.WINSCP_FS_PROTOCOL), _read(session, c.WINSCP_FTPS))
    password = ""
    encrypted = _read(session, c.WINSCP_PASSWORD)
    if isinstance(encrypted, str) and encrypted:
        try:
            password = winscp_password.decrypt(host, str(user), encrypted)
        except (ValueError, IndexError, UnicodeDecodeError):
            AppLogger.warning(f"WinSCP: cannot decrypt password of session {full_name}")
    folder, _, name = full_name.rpartition(c.FOLDER_SEPARATOR)
    port = _read(session, c.WINSCP_PORT)
    return FtpAccount(
        name=name,
        host=host,
        user=str(user),
        password=password,
        port=parse_port(port if isinstance(port, int) else None, protocol),
        protocol=protocol,
        folder=folder,
        remote_dir=str(_read(session, c.WINSCP_REMOTE_DIR) or ""),
    )


def _protocol(fs_protocol: str | int | None, ftps: str | int | None) -> FtpProtocol:
    if fs_protocol != c.WINSCP_FS_FTP:
        return FtpProtocol.SFTP  # WinSCP's default when FSProtocol is absent
    return FtpProtocol.FTP if ftps in (None, c.WINSCP_FTPS_NONE) else FtpProtocol.FTPS


def _values(account: FtpAccount) -> dict[str, str | int]:
    is_ftp = account.protocol is not FtpProtocol.SFTP
    values: dict[str, str | int] = {
        c.WINSCP_HOST: account.host,
        c.WINSCP_PORT: account.port,
        c.WINSCP_USER: account.user,
        c.WINSCP_PASSWORD: winscp_password.encrypt(account.host, account.user, account.password),
        c.WINSCP_FS_PROTOCOL: c.WINSCP_FS_FTP if is_ftp else c.WINSCP_FS_SFTP,
        c.WINSCP_FTPS: c.WINSCP_FTPS_EXPLICIT
        if account.protocol is FtpProtocol.FTPS
        else c.WINSCP_FTPS_NONE,
    }
    if account.remote_dir:
        values[c.WINSCP_REMOTE_DIR] = account.remote_dir
    return values
