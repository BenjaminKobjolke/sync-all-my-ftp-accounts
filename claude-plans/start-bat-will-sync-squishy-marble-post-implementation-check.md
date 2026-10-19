# Post-implementation DRY check

## SUMMARY

DRY opportunities found: 4.

## Findings

### 1. Centralize enum-to-menu selection

Affected files:

- `src/ftp_sync/sync_runner.py` (`_pick_source`, `_select_accounts`, `_ask`)

The runner repeatedly converts enum members into menu labels, calls `menu.show_menu`, and converts the returned index back into an enum member. A small local helper for selecting an enum value would keep menu ordering and index conversion consistent and reduce repeated menu-selection code.

### 2. Centralize interactive cancellation handling

Affected files:

- `src/ftp_sync/menu.py` (`show_menu`, `ask_text`, `show_multiselect`)

All three public menu functions repeat the same `_require_tty()` plus `try/except KeyboardInterrupt` pattern. A private wrapper for interactive operations could own the common cancellation-to-exit behavior while preserving each operation's specific call and return conversion.

### 3. Reduce repeated account-runner test setup

Affected files:

- `tests/unit/test_sync_runner.py` (`test_create_all_remaining_stops_asking`, `test_skip_and_quit`, `test_add_error_is_counted_and_run_continues`, `test_duplicate_source_account_created_once`)

Several tests independently create an empty target store, construct a source store, patch the action menu, run `SyncRunner`, and inspect the target or summary. A focused test helper or fixture for “run accounts against one target with queued actions” would make these tests shorter and keep setup behavior consistent.

### 4. Share queued-menu mocking helpers in tests

Affected files:

- `tests/unit/test_sync_runner.py` (`_patch_menu`, `test_source_picked_from_menu`, `_search_run`)

The tests define multiple variants of a `show_menu` monkeypatch that consume queued indexes and optionally capture options or titles. A single configurable helper for queued menu responses would remove this repeated mocking structure and make the intent of each test clearer.

## DELEGATE QUESTIONS

None.
