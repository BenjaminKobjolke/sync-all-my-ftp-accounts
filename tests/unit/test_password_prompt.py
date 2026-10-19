import string
from unittest.mock import MagicMock

import pytest

from ftp_sync import password_prompt
from ftp_sync.models import AppKind
from ftp_sync.password_prompt import NewPasswordAction, PasswordAction, ask_password
from ftp_sync.stores.account_store import AccountStore
from ftp_sync.stores.kas_store import KasStore
from tests.conftest import make_account

ACCOUNT = make_account(password="", folder="A")


def _patch(
    monkeypatch: pytest.MonkeyPatch, choices: list[object], secrets: list[str] | None = None
) -> list[list[str]]:
    shown: list[list[str]] = []

    def show_menu(options: list[str], title: str, **_: object) -> int:
        shown.append(options)
        choice = choices.pop(0)
        return list(type(choice)).index(choice)  # type: ignore[arg-type]

    monkeypatch.setattr("ftp_sync.menu.show_menu", show_menu)
    monkeypatch.setattr("ftp_sync.menu.ask_secret", lambda prompt: (secrets or []).pop(0))
    monkeypatch.setattr("ftp_sync.menu.show_secret", lambda label, value: None)
    return shown


def _kas() -> MagicMock:
    store = MagicMock(spec=KasStore)
    store.kind = AppKind.ALL_INKL
    return store


def test_existing_password(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, [PasswordAction.EXISTING], ["typed"])
    store = _kas()
    assert ask_password(ACCOUNT, store) == "typed"
    store.change_password.assert_not_called()


def test_leave_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, [PasswordAction.EMPTY])
    assert ask_password(ACCOUNT, _kas()) == ""


def test_new_typed_password_reasks_until_both_match(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(
        monkeypatch,
        [PasswordAction.NEW, NewPasswordAction.TYPE],
        ["one", "two", "", "", "same", "same"],
    )
    store = _kas()
    assert ask_password(ACCOUNT, store) == "same"
    store.change_password.assert_called_once_with(ACCOUNT, "same")


def test_new_generated_password(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, [PasswordAction.NEW, NewPasswordAction.GENERATE])
    store = _kas()
    password = ask_password(ACCOUNT, store)
    store.change_password.assert_called_once_with(ACCOUNT, password)
    assert len(password) == 20


def test_failed_change_asks_again(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, [PasswordAction.NEW, NewPasswordAction.GENERATE, PasswordAction.EMPTY])
    store = _kas()
    store.change_password.side_effect = RuntimeError("KAS down")
    assert ask_password(ACCOUNT, store) == ""


def test_new_option_only_for_password_changing_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    shown = _patch(monkeypatch, [PasswordAction.EMPTY])
    source = MagicMock(spec=AccountStore)
    source.kind = AppKind.FMAN
    ask_password(ACCOUNT, source)
    assert len(shown[0]) == len(PasswordAction) - 1


def test_generated_passwords_mix_letters_and_digits() -> None:
    for _ in range(50):
        password = password_prompt.generate_password()
        assert len(password) == 20
        assert set(password) <= set(string.ascii_letters + string.digits)
        assert any(c.isdigit() for c in password) and any(c.isalpha() for c in password)
