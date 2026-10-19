# Plan: "Sync all" or "Search" after picking the source

## Context
`start.bat` walks every account of the chosen source app. User wants, right after the
"Sync FROM which app?" menu, a second menu: **Sync all** or **Search**. Search asks for a
text query (e.g. `blocker`), lists every source account that matches, and lets the user
pick one account or "all matches". The existing per-account sync flow then runs only for
that selection.

"Fuzzy" = the project rule *Search Across Partial Words* (CODING_RULES.md): split query on
whitespace, every term must be a case-insensitive substring, any order. `block prod` finds
`clients/prod-blocker`.

## Changes

### `src/ftp_sync/models.py`
Add to `FtpAccount` (self-describing: the account owns what is searchable):
```py
def matches(self, query: str) -> bool:
    """Every whitespace-separated term is a case-insensitive substring of describe()."""
    text = self.describe().lower()
    return all(term in text for term in query.lower().split())
```
`describe()` already holds folder, name, protocol, user, host, port — no password. Keep
the matching rule exactly aligned with `CODING_RULES.md`; reject a blank search query in
the menu flow so `split()` cannot accidentally match every account.

### `src/ftp_sync/menu.py`
Add `ask_text(prompt: str) -> str` beside `show_menu` — `_require_tty()`, `input(prompt)`,
Ctrl-C -> `sys.exit(1)`, using the same try/except pattern as the existing menu functions.
Keep `menu.py` the only interactive-IO module, so tests patch it rather than `pick` or
`input` directly.

### `src/ftp_sync/sync_runner.py`
- New enum next to `SyncAction`:
  ```py
  class AccountScope(Enum):
      ALL = "Sync all accounts"
      SEARCH = "Search accounts..."
  ```
- `run()`: `accounts = source.load()`; if `source_kind is None` (interactive path) then
  `accounts = self._select_accounts(accounts)`; loop over `accounts` instead of `source.load()`.
  `--source` given = unchanged behaviour (sync all, stays scriptable; existing tests untouched).
- `_select_accounts(accounts)`: show a `menu.show_menu` scope menu using the enum's definition
  order; ALL returns the already-loaded list. SEARCH loops on `menu.ask_text("Search: ")`,
  rejects blank input, filters with `FtpAccount.matches`, and uses `AppLogger.warning` before
  retrying when there are no hits. For hits, reuse `FtpAccount.describe()` in
  `menu.show_menu([f"All {n} matches", *(a.describe() for a in hits)], title)`; index 0
  returns all hits, otherwise return `[hits[index - 1]]`.
- Load the source once before selection and pass the resulting list through the existing
  per-account flow; this avoids a second store read and keeps the `--source` path unchanged.

### Tests (TDD — write first, see them fail)
- `tests/unit/test_sync_runner.py`:
  - `FtpAccount.matches`: single term, multi-term any order, case-insensitive, no match.
  - search -> pick one: only that account reaches `target.add`.
  - search -> "All matches": all hits created, non-matching account not.
  - blank/no-hit queries re-prompt (`ask_text` called again); include the blank case because
    an empty `split()` otherwise matches every account.
  - Update `test_source_picked_from_menu`: make the existing `show_menu` fake return source=1
    for the source menu and `AccountScope.ALL` for the scope menu, then assert titles count 2.
    Reuse `_patch_menu`/`fake_store`; do not introduce a second store or picker abstraction.
- `tests/integration/test_sync_end_to_end.py`: check whether it uses `run(None)`; adjust only if so.

### `README.md`
One usage line on the new Sync all / Search menu.

## Reuse
- `menu.show_menu`, `menu._require_tty` (`src/ftp_sync/menu.py`)
- `FtpAccount.describe()` (`src/ftp_sync/models.py`) as search text and list label
- `SyncAction`'s definition-order/index convention in `src/ftp_sync/sync_runner.py`
- `AppLogger.warning()` for recoverable interactive input problems
- `_patch_menu` / `fake_store` helpers in `tests/unit/test_sync_runner.py`

## Skipped
- Multiselect of several hits (one or all was asked). Add when needed: swap the result menu
  for `menu.show_multiselect`.
- `--search` CLI flag. Add when scripted search is needed.
- Integration-test changes, because the existing integration flow passes an explicit source kind
  rather than `None`.

## Verification
- `tools/run_tests.bat`, `tools/run_integration_tests.bat`, `uv run ruff check`, `uv run mypy`.
- Manual: `start.bat` -> pick source -> Search -> `blocker` -> list shows only matching
  accounts -> pick one -> only its per-account sync menu appears -> summary.

## SUMMARY CONVENTION CHECK

Reused `FtpAccount.describe()` for password-free search/display text, `menu.py` as the sole
interactive-IO boundary, its `_require_tty()` and Ctrl-C handling pattern, enum definition
order for menu indices, `AppLogger.warning()` for retryable input, and the existing unit-test
helpers. These match the established model, menu, runner, and test conventions.

## SUMMARY DRY

The plan now loads accounts once and passes the list into selection and the existing sync flow,
avoiding a second store read. It reuses `describe()`, the current menu helpers, and existing
test fixtures instead of adding parallel formatting, picker, store, or test abstractions. The
unnecessary file-length constraint and conditional integration-test work were removed.
