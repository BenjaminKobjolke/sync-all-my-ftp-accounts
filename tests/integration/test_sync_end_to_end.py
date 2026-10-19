"""Real stores against temp files and a throwaway HKCU key; only the menu is patched."""

import json
import subprocess
import winreg
from collections.abc import Iterator
from pathlib import Path

import pytest

from ftp_sync.backup import BackupCoordinator
from ftp_sync.config.settings import Settings
from ftp_sync.models import AppKind, FtpProtocol
from ftp_sync.stores.registry import build_stores
from ftp_sync.stores.winscp_store import WinScpStore
from ftp_sync.sync_runner import SyncAction, SyncRunner
from tests.conftest import make_account

TEST_KEY = r"Software\ftp-sync-test\Sessions"


@pytest.fixture
def settings(tmp_path: Path) -> Iterator[Settings]:
    (tmp_path / "sitemanager.xml").write_text(
        '<?xml version="1.0"?><FileZilla3><Servers /></FileZilla3>', encoding="utf-8"
    )
    (tmp_path / "NppFTP.xml").write_text("<NppFTP><Profiles /></NppFTP>", encoding="utf-8")
    bookmark = ["ftp://fred:f%40pw@f.example:21", "/pub"]
    (tmp_path / "fman.json").write_text(json.dumps({"ftp://F": bookmark}), encoding="utf-8")
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, TEST_KEY).Close()
    yield Settings(
        filezilla_path=tmp_path / "sitemanager.xml",
        nppftp_path=tmp_path / "NppFTP.xml",
        fman_path=tmp_path / "fman.json",
        winscp_key=TEST_KEY,
        backup_dir=tmp_path / "backups",
    )
    subprocess.run(["reg", "delete", r"HKCU\Software\ftp-sync-test", "/f"], capture_output=True)


def test_winscp_store_roundtrip(settings: Settings) -> None:
    store = WinScpStore(settings.winscp_key, BackupCoordinator(settings.backup_dir))
    account = make_account(folder="Clients/Sub", protocol=FtpProtocol.FTPS, remote_dir="/www")
    sftp = make_account(name="my site", user="sam", protocol=FtpProtocol.SFTP, port=2222)
    store.add(account)
    store.add(sftp)
    assert store.load() == [account, sftp]
    assert len(list(settings.backup_dir.rglob("*.reg"))) == 1


def test_sync_from_fman_creates_everywhere(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "ftp_sync.menu.show_menu",
        lambda *_a, **_k: list(SyncAction).index(SyncAction.CREATE_MISSING),
    )
    stores = build_stores(settings, BackupCoordinator(settings.backup_dir))
    summary = SyncRunner(stores).run(AppKind.FMAN)
    assert summary.created == {AppKind.WINSCP: 1, AppKind.FILEZILLA: 1, AppKind.NPPFTP: 1}
    for store in stores:
        (account,) = store.load()
        assert (account.host, account.user, account.password) == ("f.example", "fred", "f@pw")
    # Second run: everything found, nothing created, no menu needed.
    monkeypatch.setattr("ftp_sync.menu.show_menu", lambda *_a, **_k: pytest.fail("asked"))
    assert not SyncRunner(stores).run(AppKind.FMAN).created
