"""KAS (All-Inkl) logins from settings.json. Kept out of env vars: there are several."""

import json
from dataclasses import dataclass
from pathlib import Path

from ftp_sync import constants


@dataclass(frozen=True)
class KasAccountConfig:
    name: str
    login: str
    password: str


def load_kas_accounts(path: Path) -> tuple[KasAccountConfig, ...]:
    """All configured KAS accounts; none when the file does not exist. Raises ValueError."""
    if not path.exists():
        return ()
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get(constants.KAS_ACCOUNTS_KEY, []) if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"{path}: '{constants.KAS_ACCOUNTS_KEY}' must be a list")
    accounts = tuple(_parse(path, index, entry) for index, entry in enumerate(entries))
    names = [a.name for a in accounts]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"{path}: Duplicate KAS account name(s): {', '.join(duplicates)}")
    return accounts


def _parse(path: Path, index: int, entry: object) -> KasAccountConfig:
    if not isinstance(entry, dict):
        raise ValueError(f"{path}: {constants.KAS_ACCOUNTS_KEY}[{index}] must be an object")
    for field in constants.KAS_ACCOUNT_FIELDS:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{path}: {constants.KAS_ACCOUNTS_KEY}[{index}] needs a non-empty '{field}'"
            )
    return KasAccountConfig(entry["name"], entry["login"], entry["password"])
