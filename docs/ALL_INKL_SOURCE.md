# All-Inkl (KAS) as Sync Source

Reads the FTP users of one or more All-Inkl KAS accounts via the KAS API and creates them in
WinSCP, FileZilla, Notepad++ NppFTP and fman. All-Inkl is a **source only**: nothing is ever
written to All-Inkl except an optional new FTP password chosen by the user.

## Setup

1. The KAS API client is the sibling library `kas-api-python`, referenced as an editable path
   dependency in `pyproject.toml`:

   ```toml
   [tool.uv.sources]
   kas-api-python = { path = "../../Intern/kas-api-python", editable = true }
   ```

   `install.bat` / `uv sync` installs it. The repo must exist at that path.

2. Create `settings.json` in the project root (gitignored) from `settings.example.json`:

   ```json
   {
     "kas_accounts": [
       { "name": "Main account", "login": "w0123456", "password": "kas-password" },
       { "name": "Customer B", "login": "w0234567", "password": "kas-password-b" }
     ]
   }
   ```

   - One entry per KAS login. Subaccounts are separate logins with their own password.
   - `name` must be unique; it becomes the folder of the imported accounts.
   - Every field must be a non-empty string; otherwise the run stops with an error naming
     the entry.
   - Other location: set `FTP_SYNC_SETTINGS_PATH`.
   - No `settings.json` → All-Inkl is not offered as a source.

KAS logins are deliberately kept out of environment variables, because there are several.

## Usage

```bat
start.bat                    :: pick "All-Inkl (KAS)" in the source menu
start.bat --source allinkl   :: scripted: all accounts, no scope menu
```

## Imported accounts

`get_ftpusers` per KAS account, mapped to:

| Field | Value |
|---|---|
| name | FTP user comment, or its login when the comment is empty |
| host | `<ftp_hostname>.kasserver.com` |
| user | `ftp_login` |
| protocol / port | FTPS (explicit) / 21 |
| folder | `name` from `settings.json` |
| remote dir | none — sub-users are already chrooted to their `ftp_path` |
| password | empty — the KAS API never returns FTP passwords |

A KAS login that fails (wrong password, API error) is logged and skipped; the other accounts
still load.

## Matching

Accounts are matched by host + user as usual. Because the source has no password, an account
already present in a target counts as `found` — never `DIFFERENT PASSWORD`. Re-running a sync
therefore asks nothing for accounts that already exist.

## Password prompt

For each account that is about to be created (after choosing a create action, also in
"for this and ALL remaining accounts" mode) the tool asks:

| Option | Result |
|---|---|
| Enter the password already set on All-Inkl (KAS) | Hidden input; stored in the target apps as typed |
| Leave empty - set it later in the FTP apps | Account created without password |
| Set a new password (updates All-Inkl (KAS)) | Sub-menu **Type it** (entered twice, must match, not empty) or **Generate one** (20 letters + digits, shown once on the console). The password is set on All-Inkl via KAS `update_ftpuser`, then stored in the apps. |

Setting a new password changes the **live** FTP password — every other client still using the
old one stops working. If the KAS call fails, the error is logged and the menu is shown again.

Passwords never pass through `AppLogger`; the generated one is printed once by
`menu.show_secret`.

## Implementation

| File | Role |
|---|---|
| `src/ftp_sync/config/kas_accounts.py` | `KasAccountConfig` + `load_kas_accounts(path)` with validation |
| `src/ftp_sync/config/settings.py` | `Settings.kas_accounts`, path from `FTP_SYNC_SETTINGS_PATH` |
| `src/ftp_sync/stores/kas_store.py` | `KasStore` — load via `KasClient.get_ftp_users`, `change_password` via `set_ftp_password`; `add` raises |
| `src/ftp_sync/stores/account_store.py` | `PasswordChangingStore` Protocol (runtime checkable) |
| `src/ftp_sync/stores/registry.py` | One `KasClient` per `settings.json` entry |
| `src/ftp_sync/models.py` | `AppKind.ALL_INKL`, `AppKind.is_writable` |
| `src/ftp_sync/sync_runner.py` | Excludes non-writable stores from targets; asks for a password when the account has none |
| `src/ftp_sync/password_prompt.py` | `ask_password`, `generate_password` |
| `src/ftp_sync/account_matcher.py` | Empty source password + host/user match → `found` |
| `src/ftp_sync/menu.py` | `ask_secret` (getpass), `show_secret` |

Because All-Inkl is never a target, its store is never loaded unless picked as source (no API
call) and has no process name to check.

## Tests

- `tests/unit/test_kas_accounts.py` — settings file: missing, valid, empty field, duplicate name.
- `tests/unit/test_kas_store.py` — mapping, failing login skipped, source-only contract,
  `change_password` routed to the right KAS account.
- `tests/unit/test_password_prompt.py` — all menu paths, mismatch retry, failed change,
  generator charset.
- `tests/unit/test_sync_runner.py` — never a target, empty password counts as found, prompt
  result used for creation.
- `tests/integration/test_sync_end_to_end.py` — fake `KasClient`, real stores: created
  everywhere with the entered password, second run creates nothing.

The library's own tests (including a live read-only API test) live in `kas-api-python`.

## Not supported

- Automatic subaccount discovery (`get_accounts`) — list every login in `settings.json`.
- Checking an entered password with a real FTP login.
- SFTP/SSH users.
