from unittest.mock import MagicMock

import pytest
from kas_api import KasClient, KasError, KasErrorKind, KasFtpUser

from ftp_sync.models import AppKind, FtpProtocol
from ftp_sync.stores.account_store import PasswordChangingStore
from ftp_sync.stores.kas_store import KasStore
from tests.conftest import make_account


def _client(*users: KasFtpUser) -> MagicMock:
    client = MagicMock(spec=KasClient)
    client.get_ftp_users.return_value = list(users)
    return client


def test_load_maps_ftp_users_per_kas_account() -> None:
    main = KasFtpUser("w0001", "w0001", "/", "main user", True)
    sub = KasFtpUser("f0002", "w0001", "/demo/", "", False)
    store = KasStore({"Customer A": _client(main, sub)})

    first, second = store.load()

    assert first == make_account(
        name="main user",
        host="w0001.kasserver.com",
        user="w0001",
        password="",
        port=21,
        protocol=FtpProtocol.FTPS,
        folder="Customer A",
    )
    assert (second.name, second.user, second.remote_dir) == ("f0002", "f0002", "")


def test_failing_kas_account_is_skipped() -> None:
    broken = _client()
    broken.get_ftp_users.side_effect = KasError(KasErrorKind.AUTH, "get_ftpusers", "bad")
    ok = _client(KasFtpUser("w2", "w2", "/", "", True))
    accounts = KasStore({"Broken": broken, "Ok": ok}).load()
    assert [a.folder for a in accounts] == ["Ok"]


def test_source_only_contract() -> None:
    store = KasStore({})
    assert store.kind is AppKind.ALL_INKL and not store.kind.is_writable
    assert not store.is_available()
    assert not store.supports(FtpProtocol.FTP)
    with pytest.raises(NotImplementedError):
        store.add(make_account())


def test_change_password_uses_client_of_the_accounts_folder() -> None:
    a, b = _client(), _client()
    store = KasStore({"A": a, "B": b})
    assert isinstance(store, PasswordChangingStore)
    store.change_password(make_account(user="f0002", folder="B"), "new")
    b.set_ftp_password.assert_called_once_with("f0002", "new")
    a.set_ftp_password.assert_not_called()
