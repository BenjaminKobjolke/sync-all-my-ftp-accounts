"""Contract every credential store implements, plus small shared helpers."""

from collections.abc import Collection
from typing import Protocol

from ftp_sync import constants
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol


class AccountStore(Protocol):
    kind: AppKind

    def is_available(self) -> bool: ...

    def load(self) -> list[FtpAccount]: ...

    def add(self, account: FtpAccount) -> None: ...

    def supports(self, protocol: FtpProtocol) -> bool: ...


def unique_name(name: str, taken: Collection[str]) -> str:
    """Return `name`, or `name (2)`, `name (3)`, ... if already taken."""
    candidate, counter = name, 2
    while candidate in taken:
        candidate = f"{name} ({counter})"
        counter += 1
    return candidate


def join_folder(*parts: str) -> str:
    return constants.FOLDER_SEPARATOR.join(p for p in parts if p)


def parse_port(value: str | int | None, protocol: FtpProtocol) -> int:
    if value is None or value == "":
        return protocol.default_port
    try:
        return int(value)
    except ValueError:
        return protocol.default_port
