"""Asks which password to store for an account its source returned without one."""

import secrets
import string
from enum import Enum

from ftp_sync import menu
from ftp_sync.app_logger import AppLogger
from ftp_sync.models import FtpAccount
from ftp_sync.stores.account_store import AccountStore, PasswordChangingStore

GENERATED_LENGTH = 20
_ALPHABET = string.ascii_letters + string.digits


class PasswordAction(Enum):
    """Menu order = definition order; `{source}` is the source app's label."""

    EXISTING = "Enter the password already set on {source}"
    EMPTY = "Leave empty - set it later in the FTP apps"
    NEW = "Set a new password (updates {source})"


class NewPasswordAction(Enum):
    TYPE = "Type it"
    GENERATE = "Generate one"


def ask_password(account: FtpAccount, source: AccountStore) -> str:
    label = source.kind.label
    changer = source if isinstance(source, PasswordChangingStore) else None
    actions = [a for a in PasswordAction if changer or a is not PasswordAction.NEW]
    options = [a.value.format(source=label) for a in actions]
    title = f"{account.describe()}\nNo password from {label} - which one to store?"
    while True:
        action = actions[menu.show_menu(options, title)]
        if action is PasswordAction.EMPTY:
            return ""
        if action is PasswordAction.EXISTING:
            return menu.ask_secret("Password: ")
        assert changer is not None  # NEW is only offered for a PasswordChangingStore
        password = _new_password()
        try:
            changer.change_password(account, password)
        except Exception as error:  # noqa: BLE001 - let the user pick another way
            AppLogger.error(f"{label}: could not set the new password: {error}")
            continue
        AppLogger.info(f"    -> new password set on {label}")
        return password


def generate_password() -> str:
    """Letters and digits only: safe in every app's storage and in fman's ftp:// URLs."""
    while True:
        password = "".join(secrets.choice(_ALPHABET) for _ in range(GENERATED_LENGTH))
        if any(c.isdigit() for c in password) and any(c.isalpha() for c in password):
            return password


def _new_password() -> str:
    actions = list(NewPasswordAction)
    action = actions[menu.show_menu([a.value for a in actions], "New password:")]
    if action is NewPasswordAction.GENERATE:
        password = generate_password()
        menu.show_secret("Generated password", password)
        return password
    while True:
        password = menu.ask_secret("New password: ")
        if password and password == menu.ask_secret("Repeat: "):
            return password
        AppLogger.warning("Empty or not matching - try again")
