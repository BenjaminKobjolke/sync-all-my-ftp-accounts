import subprocess
from unittest.mock import MagicMock

import pytest

from ftp_sync import running_apps


@pytest.fixture
def no_running_apps() -> None:
    """Overrides the conftest autouse patch: these tests exercise the real function."""


def _patch_tasklist(monkeypatch: pytest.MonkeyPatch, returncode: int, stdout: str) -> None:
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: result)


def test_parses_tasklist_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_tasklist(
        monkeypatch,
        0,
        '"FileZilla.exe","1234","Console","1","50.000 K"\n'
        '"notepad++.exe","42","Console","1","9.000 K"\n',
    )
    assert running_apps.running_process_names() == {"filezilla.exe", "notepad++.exe"}


def test_tasklist_failure_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_: object, **__: object) -> None:
        raise OSError("no tasklist")

    monkeypatch.setattr(subprocess, "run", fail)
    assert running_apps.running_process_names() == set()


def test_nonzero_exit_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_tasklist(monkeypatch, 1, "")
    assert running_apps.running_process_names() == set()
