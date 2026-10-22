"""Deploy-tool folder from settings.json; its export_ftp.php reads deploy configs for us."""

import json
from pathlib import Path

from ftp_sync import constants


def load_deploy_tool_path(path: Path) -> Path | None:
    """None when the file or the key is missing. Raises ValueError."""
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or constants.DEPLOY_TOOL_PATH_KEY not in data:
        return None
    value = data[constants.DEPLOY_TOOL_PATH_KEY]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: '{constants.DEPLOY_TOOL_PATH_KEY}' must be a non-empty string")
    return Path(value)
