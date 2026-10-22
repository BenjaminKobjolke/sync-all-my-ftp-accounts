"""The wrapper itself: pick is faked, so no terminal is needed."""

import pytest

from ftp_sync import menu


@pytest.fixture(autouse=True)
def tty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ftp_sync.menu._require_tty", lambda: None)


def test_menu_ends_its_line_so_the_next_prompt_starts_fresh(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("ftp_sync.menu.pick", lambda **_kw: ("Quit", 2))
    assert menu.show_menu(["a", "b", "Quit"], "title") == 2
    assert capsys.readouterr().out == "\n"


def test_multiselect_ends_its_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("ftp_sync.menu.pick", lambda **_kw: [("a", 0), ("c", 2)])
    assert menu.show_multiselect(["a", "b", "c"], "title") == [0, 2]
    assert capsys.readouterr().out == "\n"
