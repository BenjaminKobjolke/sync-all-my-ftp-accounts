"""Decides whether a source account already exists in a target store."""

from collections.abc import Iterable
from enum import StrEnum

from ftp_sync.models import FtpAccount


class MatchStatus(StrEnum):
    FOUND = "found"
    DIFFERENT_PASSWORD = "DIFFERENT PASSWORD"
    MISSING = "missing"
    UNSUPPORTED = "unsupported"


class AccountIndex:
    """Accounts of one store, looked up by FtpAccount.match_key()."""

    def __init__(self, accounts: Iterable[FtpAccount]) -> None:
        self._by_key: dict[tuple[str, str], list[FtpAccount]] = {}
        for account in accounts:
            self.add(account)

    def add(self, account: FtpAccount) -> None:
        self._by_key.setdefault(account.match_key(), []).append(account)

    def status_of(self, account: FtpAccount, supported: bool) -> MatchStatus:
        matches = self._by_key.get(account.match_key(), [])
        if any(m.password == account.password for m in matches):
            return MatchStatus.FOUND
        if matches:
            return MatchStatus.DIFFERENT_PASSWORD
        return MatchStatus.MISSING if supported else MatchStatus.UNSUPPORTED
