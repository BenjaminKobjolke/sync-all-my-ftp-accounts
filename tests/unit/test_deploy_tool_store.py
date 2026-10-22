import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ftp_sync.models import AppKind, FtpProtocol
from ftp_sync.stores.deploy_tool_store import DeployToolStore
from tests.conftest import make_account

WEB = {
    "name": "Web",
    "server": "ftp.example.com",
    "user": "bob",
    "password": "p'w",
    "port": 0,
    "transferType": "FTP",
    "root": "/",
}
VENDOR = {
    "name": "Vendor",
    "server": "sftp.example.com",
    "user": "sam",
    "password": "",
    "port": 0,
    "transferType": "SFTP",
    "root": "/vendor/",
}


@pytest.fixture
def tool(tmp_path: Path) -> Path:
    path = tmp_path / "deploy-tool"
    path.mkdir()
    (path / "export_ftp.php").write_text("<?php", encoding="utf-8")
    return path


@pytest.fixture
def config(tmp_path: Path) -> Path:
    path = tmp_path / "config_animate-web.php"
    path.write_text("<?php", encoding="utf-8")
    return path


def _php(monkeypatch: pytest.MonkeyPatch, stdout: str, returncode: int = 0) -> MagicMock:
    result = subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")
    run = MagicMock(return_value=result)
    monkeypatch.setattr("ftp_sync.stores.deploy_tool_store.subprocess.run", run)
    return run


def test_load_maps_exported_entries(
    monkeypatch: pytest.MonkeyPatch, tool: Path, config: Path
) -> None:
    run = _php(monkeypatch, "12:00 - loading\n" + json.dumps([WEB, VENDOR]) + "\n")

    web, vendor = DeployToolStore(tool, config).load()

    assert web == make_account(
        name="Web",
        host="ftp.example.com",
        user="bob",
        password="p'w",
        port=21,
        protocol=FtpProtocol.FTP,
        folder="",
    )
    assert (vendor.protocol, vendor.port, vendor.remote_dir) == (FtpProtocol.SFTP, 22, "/vendor")
    command = run.call_args.args[0]
    assert command == [str(tool / "php" / "php.exe"), str(tool / "export_ftp.php"), str(config)]
    assert run.call_args.kwargs["cwd"] == tool


def test_explicit_port_is_kept(monkeypatch: pytest.MonkeyPatch, tool: Path, config: Path) -> None:
    _php(monkeypatch, json.dumps([{**WEB, "port": 2121, "transferType": "FTPS"}]))
    (account,) = DeployToolStore(tool, config).load()
    assert (account.protocol, account.port) == (FtpProtocol.FTPS, 2121)


@pytest.mark.parametrize("stdout, returncode", [("Exit: [Config] Invalid!\n", 0), ("[]", 1)])
def test_missing_json_or_failed_exit_raises_with_output(
    monkeypatch: pytest.MonkeyPatch, tool: Path, config: Path, stdout: str, returncode: int
) -> None:
    _php(monkeypatch, stdout, returncode)
    with pytest.raises(RuntimeError, match="Deploy tool"):
        DeployToolStore(tool, config).load()


def test_unknown_transfer_type_raises(
    monkeypatch: pytest.MonkeyPatch, tool: Path, config: Path
) -> None:
    _php(monkeypatch, json.dumps([{**WEB, "transferType": "SCP"}]))
    with pytest.raises(RuntimeError, match="SCP"):
        DeployToolStore(tool, config).load()


def test_asks_for_the_config_path_until_it_exists(
    monkeypatch: pytest.MonkeyPatch, tool: Path, config: Path
) -> None:
    _php(monkeypatch, json.dumps([WEB]))
    answers = iter(["  D:/does/not/exist.php", f' "{config}" '])
    monkeypatch.setattr("ftp_sync.menu.ask_text", lambda _prompt: next(answers))

    (account,) = DeployToolStore(tool).load()

    assert account.name == "Web"


def test_available_only_with_export_script(tmp_path: Path, tool: Path) -> None:
    assert DeployToolStore(tool).is_available()
    assert not DeployToolStore(tmp_path).is_available()
    assert not DeployToolStore(None).is_available()


def test_source_only_contract(tool: Path) -> None:
    store = DeployToolStore(tool)
    assert store.kind is AppKind.DEPLOY_TOOL and not store.kind.is_writable
    assert not store.supports(FtpProtocol.FTP)
    with pytest.raises(NotImplementedError):
        store.add(make_account())
