"""fman FTP plugin bookmarks: {"ftp://<name>": ["<scheme>://user:pw@host:port", "<path>", ...]}.

Credentials sit percent-encoded in the URL (the plugin unquotes them). FTP/FTPS only.
"""

import json
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from ftp_account_readers.helpers import unique_name

from ftp_sync import constants as c
from ftp_sync.app_logger import AppLogger
from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol


class FmanStore:
    kind = AppKind.FMAN

    def __init__(self, path: Path, backup: BackupCoordinator) -> None:
        self._path = path
        self._backup = backup

    def is_available(self) -> bool:
        return self._path.is_file()

    def supports(self, protocol: FtpProtocol) -> bool:
        return protocol is not FtpProtocol.SFTP

    def load(self) -> list[FtpAccount]:
        accounts = []
        for key, value in self._read().items():
            account = _parse(key, value)
            if account is None:
                AppLogger.warning(f"fman: skipping unreadable bookmark {key.split('@')[-1]}")
            else:
                accounts.append(account)
        return accounts

    def add(self, account: FtpAccount) -> None:
        self._backup.backup_file(self._path)
        data = self._read()
        scheme = account.protocol.value
        names = {key.split("://", 1)[-1] for key in data}
        key = f"{scheme}://{unique_name(account.name, names)}"
        credentials = f"{quote(account.user, safe='')}:{quote(account.password, safe='')}"
        url = f"{scheme}://{credentials}@{account.host}:{account.port}"
        data[key] = [url, account.remote_dir or c.FMAN_DEFAULT_PATH]
        self._path.write_text(json.dumps(data, indent=4), encoding="utf-8")

    def _read(self) -> dict[str, list[str]]:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{self._path} is not a JSON object")
        return data


def _parse(key: str, value: object) -> FtpAccount | None:
    if not isinstance(value, list) or not value or not isinstance(value[0], str):
        return None
    url = urlsplit(value[0])
    if url.scheme not in c.FMAN_SCHEMES or not url.hostname:
        return None
    protocol = FtpProtocol.FTPS if url.scheme == FtpProtocol.FTPS.value else FtpProtocol.FTP
    try:
        port = url.port or protocol.default_port
    except ValueError:
        return None
    path = value[1] if len(value) > 1 and isinstance(value[1], str) else ""
    return FtpAccount(
        name=key.split("://", 1)[-1],
        host=url.hostname,
        user=unquote(url.username or ""),
        password=unquote(url.password or ""),
        port=port,
        protocol=protocol,
        remote_dir=path,
    )
