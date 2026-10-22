"""FTP logins of one deploy-tool config file. Source only: accounts are never written here.

The deploy tool reads the file itself (export_ftp.php), so presets, defaults and validation
stay in one place instead of a second PHP parser here.
"""

import json
import subprocess
from pathlib import Path

from ftp_sync import constants, menu
from ftp_sync.app_logger import AppLogger
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol
from ftp_sync.stores.account_store import parse_port


class DeployToolStore:
    kind = AppKind.DEPLOY_TOOL

    def __init__(self, tool_path: Path | None, config_path: Path | None = None) -> None:
        """`config_path` None = ask for it when loading (interactive runs)."""
        self._tool_path = tool_path
        self._config_path = config_path

    def is_available(self) -> bool:
        tool = self._tool_path
        return tool is not None and (tool / constants.DEPLOY_TOOL_EXPORT).is_file()

    def load(self) -> list[FtpAccount]:
        assert self._tool_path is not None  # SyncRunner only loads available stores
        config = self._config_path or _ask_config_path()
        result = subprocess.run(
            [
                str(self._tool_path / constants.DEPLOY_TOOL_PHP),
                str(self._tool_path / constants.DEPLOY_TOOL_EXPORT),
                str(config),
            ],
            cwd=self._tool_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        return [_to_account(entry) for entry in _parse_output(result)]

    def add(self, account: FtpAccount) -> None:
        raise NotImplementedError(f"{self.kind.label} is a source only")

    def supports(self, protocol: FtpProtocol) -> bool:
        return False


def _ask_config_path() -> Path:
    while True:
        # Explorer's "Copy as path" wraps the path in quotes.
        path = Path(menu.ask_text(constants.DEPLOY_CONFIG_PROMPT).strip().strip('"'))
        if path.is_file():
            return path
        AppLogger.warning(f"File not found: {path}")


def _parse_output(result: subprocess.CompletedProcess[str]) -> list[dict[str, object]]:
    lines = result.stdout.strip().splitlines()
    try:
        entries = json.loads(lines[-1]) if result.returncode == 0 and lines else None
    except json.JSONDecodeError:
        entries = None
    if not isinstance(entries, list):
        output = (result.stdout + result.stderr).strip()
        raise RuntimeError(f"Deploy tool could not read the config:\n{output}")
    return entries


def _to_account(entry: dict[str, object]) -> FtpAccount:
    transfer_type = str(entry["transferType"])
    try:
        protocol = FtpProtocol(transfer_type.lower())
    except ValueError:
        raise RuntimeError(f"Deploy tool: unknown transferType '{transfer_type}'") from None
    port = entry["port"]
    return FtpAccount(
        name=str(entry["name"]),
        host=str(entry["server"]),
        user=str(entry["user"]),
        password=str(entry["password"] or ""),
        # The deploy tool reports 0 for "protocol default".
        port=parse_port(port if isinstance(port, int) and port else None, protocol),
        protocol=protocol,
        remote_dir=str(entry["root"]).rstrip("/"),
    )
