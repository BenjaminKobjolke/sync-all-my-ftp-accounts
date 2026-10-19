from unittest.mock import MagicMock

import pytest

from ftp_sync.account_matcher import AccountIndex, MatchStatus
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol
from ftp_sync.stores.account_store import AccountStore
from ftp_sync.sync_runner import AccountScope, SyncAction, SyncRunner
from tests.conftest import make_account


def fake_store(kind: AppKind, accounts: list[FtpAccount], sftp: bool = True) -> MagicMock:
    store = MagicMock(spec=AccountStore)
    store.kind = kind
    store.is_available.return_value = True
    store.load.return_value = accounts
    store.supports.side_effect = lambda p: sftp or p is not FtpProtocol.SFTP
    return store


def test_index_statuses() -> None:
    account = make_account()
    index = AccountIndex([make_account(host="FTP.example.com", user="BOB", port=22)])
    assert index.status_of(account, supported=True) is MatchStatus.FOUND
    assert index.status_of(make_account(password="x"), True) is MatchStatus.DIFFERENT_PASSWORD
    assert index.status_of(make_account(user="eve"), True) is MatchStatus.MISSING
    assert index.status_of(make_account(user="eve"), False) is MatchStatus.UNSUPPORTED


def _patch_menu(monkeypatch: pytest.MonkeyPatch, actions: list[SyncAction]) -> list[list[str]]:
    shown: list[list[str]] = []

    def show_menu(options: list[str], title: str, **_: object) -> int:
        shown.append(options)
        return list(SyncAction).index(actions.pop(0))

    monkeypatch.setattr("ftp_sync.menu.show_menu", show_menu)
    return shown


def test_creates_missing_only_where_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    ftp = make_account(name="ftp1")
    sftp = make_account(name="s", user="sam", protocol=FtpProtocol.SFTP)
    source = fake_store(AppKind.WINSCP, [ftp, sftp])
    filezilla = fake_store(AppKind.FILEZILLA, [ftp])
    fman = fake_store(AppKind.FMAN, [], sftp=False)
    _patch_menu(monkeypatch, [SyncAction.CREATE_MISSING, SyncAction.CREATE_MISSING])

    summary = SyncRunner([source, filezilla, fman]).run(AppKind.WINSCP)

    fman.add.assert_called_once_with(ftp)
    filezilla.add.assert_called_once_with(sftp)
    source.add.assert_not_called()
    assert summary.created == {AppKind.FMAN: 1, AppKind.FILEZILLA: 1}


def test_no_prompt_when_nothing_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    account = make_account()
    shown = _patch_menu(monkeypatch, [])
    SyncRunner([fake_store(AppKind.FMAN, [account]), fake_store(AppKind.NPPFTP, [account])]).run(
        AppKind.FMAN
    )
    assert shown == []


def test_create_all_remaining_stops_asking(monkeypatch: pytest.MonkeyPatch) -> None:
    accounts = [make_account(user=f"u{i}") for i in range(3)]
    target = fake_store(AppKind.NPPFTP, [])
    shown = _patch_menu(monkeypatch, [SyncAction.CREATE_ALL_REMAINING])
    summary = SyncRunner([fake_store(AppKind.FMAN, accounts), target]).run(AppKind.FMAN)
    assert len(shown) == 1
    assert target.add.call_count == 3
    assert summary.created[AppKind.NPPFTP] == 3


def test_skip_and_quit(monkeypatch: pytest.MonkeyPatch) -> None:
    accounts = [make_account(user=f"u{i}") for i in range(3)]
    target = fake_store(AppKind.NPPFTP, [])
    _patch_menu(monkeypatch, [SyncAction.SKIP, SyncAction.QUIT])
    summary = SyncRunner([fake_store(AppKind.FMAN, accounts), target]).run(AppKind.FMAN)
    target.add.assert_not_called()
    assert summary.skipped == 1


def test_choose_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    account = make_account()
    a, b = fake_store(AppKind.NPPFTP, []), fake_store(AppKind.FILEZILLA, [])
    _patch_menu(monkeypatch, [SyncAction.CHOOSE])
    monkeypatch.setattr("ftp_sync.menu.show_multiselect", lambda options, title: [1])
    SyncRunner([fake_store(AppKind.FMAN, [account]), a, b]).run(AppKind.FMAN)
    a.add.assert_not_called()
    b.add.assert_called_once_with(account)


def test_add_error_is_counted_and_run_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    target = fake_store(AppKind.NPPFTP, [])
    target.add.side_effect = [OSError("locked"), None]
    accounts = [make_account(user="a"), make_account(user="b")]
    _patch_menu(monkeypatch, [SyncAction.CREATE_ALL_REMAINING])
    summary = SyncRunner([fake_store(AppKind.FMAN, accounts), target]).run(AppKind.FMAN)
    assert summary.errors[AppKind.NPPFTP] == 1
    assert summary.created[AppKind.NPPFTP] == 1


def test_duplicate_source_account_created_once(monkeypatch: pytest.MonkeyPatch) -> None:
    account = make_account()
    target = fake_store(AppKind.NPPFTP, [])
    _patch_menu(monkeypatch, [SyncAction.CREATE_MISSING])
    SyncRunner([fake_store(AppKind.FMAN, [account, account]), target]).run(AppKind.FMAN)
    target.add.assert_called_once()


def test_source_picked_from_menu(monkeypatch: pytest.MonkeyPatch) -> None:
    source = fake_store(AppKind.FILEZILLA, [])
    titles: list[str] = []
    answers = [1, list(AccountScope).index(AccountScope.ALL)]

    def show_menu(options: list[str], title: str, **_: object) -> int:
        titles.append(title)
        return answers.pop(0)

    monkeypatch.setattr("ftp_sync.menu.show_menu", show_menu)
    SyncRunner([fake_store(AppKind.WINSCP, []), source]).run(None)
    source.load.assert_called_once()
    assert len(titles) == 2


def test_account_matches_all_terms_any_order() -> None:
    account = make_account(name="prod-Blocker", folder="clients")
    assert account.matches("blocker")
    assert account.matches("BLOCK clients")
    assert account.matches("example blocker")
    assert not account.matches("blocker staging")


def _search_run(
    monkeypatch: pytest.MonkeyPatch, queries: list[str], result_index: int
) -> tuple[MagicMock, list[FtpAccount], list[str]]:
    accounts = [
        make_account(name="blocker-prod", user="a"),
        make_account(name="other", user="b"),
        make_account(name="blocker-dev", user="c"),
    ]
    target = fake_store(AppKind.NPPFTP, [])
    asked: list[str] = []

    def ask_text(prompt: str) -> str:
        asked.append(prompt)
        return queries.pop(0)

    answers = [
        0,  # source: FMAN
        list(AccountScope).index(AccountScope.SEARCH),
        result_index,
        *[list(SyncAction).index(SyncAction.CREATE_MISSING)] * 3,
    ]
    monkeypatch.setattr("ftp_sync.menu.ask_text", ask_text)
    monkeypatch.setattr("ftp_sync.menu.show_menu", lambda options, title, **_: answers.pop(0))
    SyncRunner([fake_store(AppKind.FMAN, accounts), target]).run(None)
    return target, accounts, asked


def test_search_pick_one(monkeypatch: pytest.MonkeyPatch) -> None:
    target, accounts, _ = _search_run(monkeypatch, ["blocker"], result_index=2)
    target.add.assert_called_once_with(accounts[2])


def test_search_all_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    target, accounts, _ = _search_run(monkeypatch, ["blocker"], result_index=0)
    assert [c.args[0] for c in target.add.call_args_list] == [accounts[0], accounts[2]]


def test_search_reprompts_on_blank_or_no_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    target, accounts, asked = _search_run(monkeypatch, ["  ", "zzz", "other"], result_index=1)
    assert len(asked) == 3
    target.add.assert_called_once_with(accounts[1])
