"""All-Inkl FTP users read via the KAS API. Source only: accounts are never written here."""

from kas_api import KasClient

from ftp_sync.app_logger import AppLogger
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol


class KasStore:
    kind = AppKind.ALL_INKL

    def __init__(self, clients: dict[str, KasClient]) -> None:
        """`clients` maps the configured KAS account name (the folder) to its client."""
        self._clients = clients

    def is_available(self) -> bool:
        return bool(self._clients)

    def load(self) -> list[FtpAccount]:
        accounts: list[FtpAccount] = []
        for name, client in self._clients.items():
            try:
                users = client.get_ftp_users()
            except Exception as error:  # noqa: BLE001 - one bad KAS login must not hide the rest
                AppLogger.error(f"{self.kind.label}: skipped '{name}': {error}")
                continue
            # No remote_dir: a sub-user is already chrooted to its ftp_path.
            # KAS never returns FTP passwords; SyncRunner asks for one per account.
            accounts.extend(
                FtpAccount(
                    name=user.comment or user.login,
                    host=user.host,
                    user=user.login,
                    password="",
                    port=FtpProtocol.FTPS.default_port,
                    protocol=FtpProtocol.FTPS,
                    folder=name,
                )
                for user in users
            )
        return accounts

    def add(self, account: FtpAccount) -> None:
        raise NotImplementedError(f"{self.kind.label} is a source only")

    def supports(self, protocol: FtpProtocol) -> bool:
        return False

    def change_password(self, account: FtpAccount, password: str) -> None:
        self._clients[account.folder].set_ftp_password(account.user, password)
