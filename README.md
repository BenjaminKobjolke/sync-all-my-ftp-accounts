# sync-all-my-ftp-accounts

CLI tool that keeps stored FTP/SFTP accounts in sync between:

- **WinSCP** (registry, `HKCU\Software\Martin Prikryl\WinSCP 2\Sessions`)
- **FileZilla** (`%APPDATA%\FileZilla\sitemanager.xml`)
- **Notepad++ NppFTP** (`%APPDATA%\Notepad++\plugins\config\NppFTP\NppFTP.xml`)
- **fman FTP plugin** (`%APPDATA%\fman\Plugins\User\Settings\FTP Bookmarks (Windows).json`)

Additional source (read only): **All-Inkl** — the FTP users of every KAS account listed in
`settings.json`, read via the KAS API ([kas-api-python](../../Intern/kas-api-python)).

## Feature: sync from one source

Pick a source app, then **Sync all accounts** or **Search accounts...**. Search takes a text
(e.g. `blocker`, or several words in any order) and lists every source account whose folder,
name, user or host contains all words (case-insensitive); pick one match or all matches.
With `--source` there is no such menu — all accounts are synced.

For every selected account stored there the tool shows whether each other app
already has it (matched by host + user name):

- `found` — present, same password
- `DIFFERENT PASSWORD` — present, password differs (only reported, never overwritten)
- `missing` — not present; you are asked whether to create it
- `unsupported` — target cannot store that protocol (fman has no SFTP)

For an account with missing apps you choose: create in all missing apps, choose apps
(multiselect), skip, create in all missing apps for this and all remaining accounts, or quit.
Existing entries are never overwritten; a name clash gets a `(2)` suffix.

### All-Inkl as source

All-Inkl accounts are imported as FTPS (port 21) on `<server>.kasserver.com`, one folder per
KAS account, named after the FTP user's comment (or its login). The KAS API never returns FTP
passwords, so an account already present in an app counts as `found` by host + user. Before
creating a missing account you choose its password:

- **Enter the password already set on All-Inkl**
- **Leave empty** — set it later in the FTP apps
- **Set a new password** — type it or let the tool generate one (20 letters/digits, shown
  once); it is set on All-Inkl via `update_ftpuser`, then stored in the apps. This changes the
  live password — other clients using the old one stop working.

All-Inkl is never a target. A KAS login that fails is logged and skipped.
Details: [docs/ALL_INKL_SOURCE.md](docs/ALL_INKL_SOURCE.md).

Before the first write to a store in a run, a backup is written to `backups/<timestamp>/`
(files copied, WinSCP sessions exported as `.reg`).

**Close the target apps before syncing** — they keep their site list in memory and write it
back on exit. The tool checks this (via `tasklist`) after you pick the source: if a target app
is still running it asks to retry, continue anyway, or quit. A scripted `--source` run aborts
instead. The source app may stay open; it is only read.

## Requirements

- Windows, Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Dependencies: `pick[blessed]` (menus), `pycryptodome` (NppFTP password DES),
  `kas-api-python` (All-Inkl KAS API, local path dependency `../../Intern/kas-api-python`)

## Setup

```bat
install.bat
```

## Usage

```bat
start.bat
start.bat --source winscp
```

`--source` accepts `winscp`, `filezilla`, `nppftp`, `fman`, `allinkl`.

## Configuration

All-Inkl KAS logins live in `settings.json` in the project root (gitignored; copy
`settings.example.json`). One entry per KAS account or subaccount; `name` becomes the folder:

```json
{
  "kas_accounts": [
    { "name": "Main account", "login": "w0123456", "password": "kas-password" }
  ]
}
```

No `settings.json` = All-Inkl is not offered as a source.

Environment overrides (see `src/ftp_sync/config/settings.py`):

| Variable | Default |
|---|---|
| `FTP_SYNC_FILEZILLA_PATH` | `%APPDATA%\FileZilla\sitemanager.xml` |
| `FTP_SYNC_NPPFTP_PATH` | `%APPDATA%\Notepad++\plugins\config\NppFTP\NppFTP.xml` |
| `FTP_SYNC_FMAN_PATH` | `%APPDATA%\fman\Plugins\User\Settings\FTP Bookmarks (Windows).json` |
| `FTP_SYNC_WINSCP_KEY` | `Software\Martin Prikryl\WinSCP 2\Sessions` (under HKCU) |
| `FTP_SYNC_BACKUP_DIR` | `backups` |
| `FTP_SYNC_LOG_LEVEL` | `INFO` |
| `FTP_SYNC_SETTINGS_PATH` | `settings.json` |

Master passwords (WinSCP / FileZilla) are not supported.

## Development

```bat
tools\run_tests.bat              :: unit tests
tools\run_integration_tests.bat  :: real stores on temp files + throwaway registry key
tools\menu_smoke.bat             :: manual menu check
tools\graphify_update.bat        :: refresh code graph
update.bat
```

Every test has a 120 s limit (`timeout` in `pyproject.toml`). A test that genuinely needs longer
sets its own: `@pytest.mark.timeout(300)` on the test, `pytestmark = pytest.mark.timeout(300)`
for a whole module, or `timeout(0)` for no limit. Keep it below the Tickets Watcher's test command
limit (`analysis_test_timeout_seconds`, default 540 s), which stops the whole run.

Architecture, store formats and password schemes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
