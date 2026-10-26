from pathlib import Path

import pytest

from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import AppKind, FtpAccount
from ftp_sync.stores import filezilla_store, nppftp_store, winscp_store
from ftp_sync.stores.filezilla_store import FileZillaStore
from ftp_sync.stores.nppftp_store import NppFtpStore
from ftp_sync.stores.winscp_store import WinScpStore
from tests.conftest import make_account


def test_filezilla_load_uses_library_reader(
    tmp_path: Path, backup: BackupCoordinator, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "sitemanager.xml"
    expected = [make_account()]
    calls: list[Path] = []

    def read(config_path: Path) -> list[FtpAccount]:
        calls.append(config_path)
        return expected

    monkeypatch.setattr(filezilla_store, "read_filezilla", read, raising=False)
    store = FileZillaStore(path, backup)

    assert store.load() == expected
    assert calls == [path]


def test_filezilla_availability_uses_configured_path(
    tmp_path: Path, backup: BackupCoordinator, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "custom-sitemanager.xml"
    calls: list[Path] = []
    monkeypatch.setattr(
        filezilla_store,
        "is_filezilla_available",
        lambda config_path: calls.append(config_path) or True,
        raising=False,
    )
    store = FileZillaStore(path, backup)

    assert store.is_available()
    assert calls == [path]


def test_nppftp_load_uses_library_reader(
    tmp_path: Path, backup: BackupCoordinator, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "NppFTP.xml"
    expected = [make_account()]
    calls: list[Path] = []

    def read(config_path: Path) -> list[FtpAccount]:
        calls.append(config_path)
        return expected

    monkeypatch.setattr(nppftp_store, "read_nppftp", read, raising=False)
    store = NppFtpStore(path, backup)

    assert store.load() == expected
    assert calls == [path]


def test_nppftp_availability_uses_configured_path(
    tmp_path: Path, backup: BackupCoordinator, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "custom-NppFTP.xml"
    calls: list[Path] = []
    monkeypatch.setattr(
        nppftp_store,
        "is_nppftp_available",
        lambda config_path: calls.append(config_path) or True,
        raising=False,
    )
    store = NppFtpStore(path, backup)

    assert store.is_available()
    assert calls == [path]


def test_winscp_load_uses_library_reader_with_configured_key(
    backup: BackupCoordinator, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = r"Software\Custom\Sessions"
    expected = [make_account()]
    calls: list[str] = []

    def read(sessions_key: str) -> list[FtpAccount]:
        calls.append(sessions_key)
        return expected

    monkeypatch.setattr(winscp_store, "read_winscp", read, raising=False)
    store = WinScpStore(key, backup)

    assert store.load() == expected
    assert calls == [key]


def test_winscp_availability_uses_configured_key(
    backup: BackupCoordinator, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = r"Software\Custom\Sessions"
    calls: list[str] = []
    monkeypatch.setattr(
        winscp_store,
        "is_winscp_available",
        lambda sessions_key: calls.append(sessions_key) or True,
        raising=False,
    )
    store = WinScpStore(key, backup)

    assert store.is_available()
    assert calls == [key]


def test_store_kinds_remain_project_owned() -> None:
    assert (WinScpStore.kind, FileZillaStore.kind, NppFtpStore.kind) == (
        AppKind.WINSCP,
        AppKind.FILEZILLA,
        AppKind.NPPFTP,
    )
