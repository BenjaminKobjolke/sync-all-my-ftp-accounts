"""Central settings; every store location can be overridden via environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

from ftp_sync import constants


@dataclass(frozen=True)
class Settings:
    filezilla_path: Path
    nppftp_path: Path
    fman_path: Path
    winscp_key: str
    backup_dir: Path
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        appdata = Path(os.getenv(constants.ENV_APPDATA, ""))
        return cls(
            filezilla_path=_path(
                constants.ENV_FILEZILLA_PATH, appdata / constants.FILEZILLA_RELATIVE_PATH
            ),
            nppftp_path=_path(constants.ENV_NPPFTP_PATH, appdata / constants.NPPFTP_RELATIVE_PATH),
            fman_path=_path(constants.ENV_FMAN_PATH, appdata / constants.FMAN_RELATIVE_PATH),
            winscp_key=os.getenv(constants.ENV_WINSCP_KEY, constants.WINSCP_SESSIONS_KEY),
            backup_dir=_path(constants.ENV_BACKUP_DIR, Path(constants.DEFAULT_BACKUP_DIR)),
            log_level=os.getenv(constants.ENV_LOG_LEVEL, "INFO"),
        )


def _path(env_name: str, default: Path) -> Path:
    value = os.getenv(env_name)
    return Path(value) if value else default
