import json
from pathlib import Path

import pytest

from ftp_sync.config.deploy_tool import load_deploy_tool_path


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_missing_file_or_key_means_none(tmp_path: Path) -> None:
    assert load_deploy_tool_path(tmp_path / "nope.json") is None
    assert load_deploy_tool_path(_write(tmp_path, {"kas_accounts": []})) is None


def test_path_is_read(tmp_path: Path) -> None:
    path = _write(tmp_path, {"deploy_tool_path": "D:/wamp64/www/deploy-tool"})
    assert load_deploy_tool_path(path) == Path("D:/wamp64/www/deploy-tool")


@pytest.mark.parametrize("value", ["", "  ", 5, ["a"]])
def test_invalid_value_rejected(tmp_path: Path, value: object) -> None:
    with pytest.raises(ValueError, match="deploy_tool_path"):
        load_deploy_tool_path(_write(tmp_path, {"deploy_tool_path": value}))
