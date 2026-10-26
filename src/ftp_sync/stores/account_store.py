"""Contract every credential store implements, plus small shared helpers."""

from typing import Protocol, runtime_checkable

from ftp_account_readers.helpers import (
    join_folder as join_folder,
)
from ftp_account_readers.helpers import (
    parse_port as parse_port,
)
from ftp_account_readers.helpers import (
    unique_name as unique_name,
)

from ftp_sync.models import AppKind, FtpAccount, FtpProtocol


class AccountStore(Protocol):
    kind: AppKind

    def is_available(self) -> bool: ...

    def load(self) -> list[FtpAccount]: ...

    def add(self, account: FtpAccount) -> None: ...

    def supports(self, protocol: FtpProtocol) -> bool: ...


@runtime_checkable
class PasswordChangingStore(Protocol):
    """A source that can set a new password on the server for one of its accounts."""

    def change_password(self, account: FtpAccount, password: str) -> None: ...
