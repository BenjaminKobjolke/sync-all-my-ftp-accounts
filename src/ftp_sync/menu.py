"""The only place that talks to `pick`. Tests patch these functions, never pick itself."""

import getpass
import sys

from pick import pick


def _require_tty() -> None:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise RuntimeError("Interactive menu needs a console - run start.bat in a terminal")


def show_menu(options: list[str], title: str, default_index: int = 0) -> int:
    """Arrow-key menu; return the selected index. Ctrl-C exits."""
    _require_tty()
    try:
        _, index = pick(
            options=options,
            title=title,
            indicator="*",
            default_index=default_index,
            backend="blessed",  # curses breaks arrow keys on Windows after subprocesses
        )
        return int(index)
    except KeyboardInterrupt:
        sys.exit(1)


def ask_text(prompt: str) -> str:
    """Free-text line input; Ctrl-C exits."""
    _require_tty()
    try:
        return input(prompt)
    except KeyboardInterrupt:
        sys.exit(1)


def show_multiselect(options: list[str], title: str) -> list[int]:
    """Space toggles, Enter confirms; return the selected indices."""
    _require_tty()
    try:
        selected = pick(
            options=options,
            title=title,
            indicator="*",
            multiselect=True,
            min_selection_count=0,
            backend="blessed",
        )
        return [int(index) for _, index in selected]
    except KeyboardInterrupt:
        sys.exit(1)


def ask_secret(prompt: str) -> str:
    """Hidden line input for passwords; Ctrl-C exits."""
    _require_tty()
    try:
        return getpass.getpass(prompt)
    except KeyboardInterrupt:
        sys.exit(1)


def show_secret(label: str, value: str) -> None:
    """Show a secret once on the console. Deliberately not via AppLogger, which never
    receives passwords."""
    sys.stdout.write(f"{label}: {value}\n")
    sys.stdout.flush()
