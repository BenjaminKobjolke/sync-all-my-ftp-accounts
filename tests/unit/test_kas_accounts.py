import json
from pathlib import Path

import pytest

from ftp_sync.config.kas_accounts import KasAccountConfig, load_kas_accounts


def _write(tmp_path: Path, accounts: object) -> Path:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"kas_accounts": accounts}), encoding="utf-8")
    return path


def test_missing_file_means_no_accounts(tmp_path: Path) -> None:
    assert load_kas_accounts(tmp_path / "nope.json") == ()


def test_valid_file(tmp_path: Path) -> None:
    path = _write(tmp_path, [{"name": "Main", "login": "w1", "password": "pw"}])
    assert load_kas_accounts(path) == (KasAccountConfig("Main", "w1", "pw"),)


@pytest.mark.parametrize(
    "accounts, message",
    [
        ([{"name": "Main", "login": "", "password": "pw"}], "login"),
        ([{"name": "Main", "login": "w1"}], "password"),
        (
            [
                {"name": "Main", "login": "w1", "password": "pw"},
                {"name": "Main", "login": "w2", "password": "pw"},
            ],
            "Duplicate",
        ),
        ("not a list", "kas_accounts"),
    ],
)
def test_invalid_entries_rejected(tmp_path: Path, accounts: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_kas_accounts(_write(tmp_path, accounts))
