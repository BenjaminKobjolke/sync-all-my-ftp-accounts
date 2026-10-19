"""Feature 1: walk every account of one source store and create it where it is missing."""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from enum import Enum

from ftp_sync import menu, password_prompt, running_apps
from ftp_sync.account_matcher import AccountIndex, MatchStatus
from ftp_sync.app_logger import AppLogger
from ftp_sync.models import AppKind, FtpAccount
from ftp_sync.stores.account_store import AccountStore


class SyncAction(Enum):
    """Menu shown per account with missing targets; menu order = definition order."""

    CREATE_MISSING = "Create in all missing apps"
    CHOOSE = "Choose apps..."
    SKIP = "Skip this account"
    CREATE_ALL_REMAINING = "Create in all missing apps - for this and ALL remaining accounts"
    QUIT = "Quit"


class RunningAction(Enum):
    """Menu shown while a target app is still open; menu order = definition order."""

    RETRY = "Retry - I closed them"
    CONTINUE = "Continue anyway (changes may be lost)"
    QUIT = "Quit"


class AccountScope(Enum):
    """Menu shown after the source pick; menu order = definition order."""

    ALL = "Sync all accounts"
    SEARCH = "Search accounts..."


@dataclass
class SyncSummary:
    created: Counter[AppKind] = field(default_factory=Counter)
    errors: Counter[AppKind] = field(default_factory=Counter)
    skipped: int = 0


@dataclass
class _Target:
    store: AccountStore
    index: AccountIndex


class SyncRunner:
    def __init__(self, stores: Sequence[AccountStore]) -> None:
        self._stores = [s for s in stores if s.is_available()]

    def run(self, source_kind: AppKind | None) -> SyncSummary:
        source = self._pick_source(source_kind)
        target_stores = [s for s in self._stores if s is not source and s.kind.is_writable]
        if not self._ensure_closed([s.kind for s in target_stores], source_kind is None):
            AppLogger.info("Aborted - nothing written.")
            return SyncSummary()
        # Loaded after the check: closing an app is what flushes its latest site list.
        targets = [_Target(s, AccountIndex(s.load())) for s in target_stores]
        accounts = source.load()
        if source_kind is None:  # --source given = scripted run, always syncs all
            accounts = self._select_accounts(accounts)
        summary = SyncSummary()
        create_all = False
        for account in accounts:
            missing = self._report(account, targets)
            if not missing:
                continue
            action = SyncAction.CREATE_MISSING if create_all else self._ask(account, missing)
            if action is SyncAction.QUIT:
                break
            if action is SyncAction.SKIP:
                summary.skipped += 1
                continue
            if action is SyncAction.CHOOSE:
                missing = self._choose(account, missing)
            create_all = create_all or action is SyncAction.CREATE_ALL_REMAINING
            if not account.password:  # asked per account: passwords differ per account
                account = replace(account, password=password_prompt.ask_password(account, source))
            self._create(account, missing, summary)
        self._log_summary(summary)
        return summary

    def _pick_source(self, source_kind: AppKind | None) -> AccountStore:
        if not self._stores:
            raise RuntimeError("No supported FTP app with stored accounts found")
        if source_kind is None:
            labels = [s.kind.label for s in self._stores]
            return self._stores[menu.show_menu(labels, "Sync FROM which app?")]
        for store in self._stores:
            if store.kind is source_kind:
                return store
        raise RuntimeError(f"{source_kind.label} is not installed or has no stored accounts")

    @staticmethod
    def _ensure_closed(kinds: list[AppKind], interactive: bool) -> bool:
        """True when no target app runs or the user accepts the risk; False = quit."""
        while True:
            names = running_apps.running_process_names()
            running = ", ".join(k.label for k in kinds if k.process_name in names)
            if not running:
                return True
            message = f"Close {running} first - they overwrite their site list on exit"
            if not interactive:
                raise RuntimeError(message)
            AppLogger.warning(message)
            actions = list(RunningAction)
            action = actions[menu.show_menu([a.value for a in actions], f"{running} still open")]
            if action is not RunningAction.RETRY:
                return action is RunningAction.CONTINUE

    @staticmethod
    def _select_accounts(accounts: list[FtpAccount]) -> list[FtpAccount]:
        scopes = list(AccountScope)
        if scopes[menu.show_menu([s.value for s in scopes], "Which accounts?")] is AccountScope.ALL:
            return accounts
        while True:
            query = menu.ask_text("Search: ")
            # A blank query splits into no terms and would match every account.
            hits = [a for a in accounts if a.matches(query)] if query.strip() else []
            if hits:
                break
            AppLogger.warning(f"No account matches '{query}'")
        options = [f"All {len(hits)} matches", *(a.describe() for a in hits)]
        index = menu.show_menu(options, f"Matches for '{query}':")
        return hits if index == 0 else [hits[index - 1]]

    @staticmethod
    def _report(account: FtpAccount, targets: list[_Target]) -> list[_Target]:
        AppLogger.info(f"\n{account.describe()}")
        missing = []
        for target in targets:
            status = target.index.status_of(account, target.store.supports(account.protocol))
            AppLogger.info(f"    {target.store.kind.label:<20} {status.value}")
            if status is MatchStatus.MISSING:
                missing.append(target)
        return missing

    @staticmethod
    def _ask(account: FtpAccount, missing: list[_Target]) -> SyncAction:
        names = ", ".join(t.store.kind.label for t in missing)
        title = f"{account.describe()}\nMissing in: {names}"
        actions = list(SyncAction)
        return actions[menu.show_menu([a.value for a in actions], title)]

    @staticmethod
    def _choose(account: FtpAccount, missing: list[_Target]) -> list[_Target]:
        labels = [t.store.kind.label for t in missing]
        title = f"{account.describe()}\nCreate in (Space = toggle, Enter = confirm):"
        return [missing[i] for i in menu.show_multiselect(labels, title)]

    @staticmethod
    def _create(account: FtpAccount, targets: list[_Target], summary: SyncSummary) -> None:
        for target in targets:
            kind = target.store.kind
            try:
                target.store.add(account)
            except Exception as error:  # noqa: BLE001 - one failing app must not stop the run
                summary.errors[kind] += 1
                AppLogger.error(f"{kind.label}: could not create {account.describe()}: {error}")
                continue
            target.index.add(account)
            summary.created[kind] += 1
            AppLogger.info(f"    -> created in {kind.label}")

    @staticmethod
    def _log_summary(summary: SyncSummary) -> None:
        AppLogger.info("\n=== Summary ===")
        for kind in AppKind:
            if summary.created[kind] or summary.errors[kind]:
                AppLogger.info(
                    f"{kind.label:<20} created {summary.created[kind]}, "
                    f"errors {summary.errors[kind]}"
                )
        AppLogger.info(f"Skipped accounts: {summary.skipped}")
