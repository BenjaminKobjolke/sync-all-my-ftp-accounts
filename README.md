# sync-all-my-ftp-accounts

CLI tool that keeps stored FTP/SFTP accounts in sync between:

- **WinSCP** (registry, `HKCU\Software\Martin Prikryl\WinSCP 2\Sessions`)
- **FileZilla** (`%APPDATA%\FileZilla\sitemanager.xml`)
- **Notepad++ NppFTP** (`%APPDATA%\Notepad++\plugins\config\NppFTP\NppFTP.xml`)
- **fman FTP plugin** (`%APPDATA%\fman\Plugins\User\Settings\FTP Bookmarks (Windows).json`)

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

Before the first write to a store in a run, a backup is written to `backups/<timestamp>/`
(files copied, WinSCP sessions exported as `.reg`).

**Close FileZilla and Notepad++ before syncing** — both overwrite their config file on exit.

## Requirements

- Windows, Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Dependencies: `pick[blessed]` (menus), `pycryptodome` (NppFTP password DES)

## Setup

```bat
install.bat
```

## Usage

```bat
start.bat
start.bat --source winscp
```

`--source` accepts `winscp`, `filezilla`, `nppftp`, `fman`.

## Configuration

Environment overrides (see `src/ftp_sync/config/settings.py`):

| Variable | Default |
|---|---|
| `FTP_SYNC_FILEZILLA_PATH` | `%APPDATA%\FileZilla\sitemanager.xml` |
| `FTP_SYNC_NPPFTP_PATH` | `%APPDATA%\Notepad++\plugins\config\NppFTP\NppFTP.xml` |
| `FTP_SYNC_FMAN_PATH` | `%APPDATA%\fman\Plugins\User\Settings\FTP Bookmarks (Windows).json` |
| `FTP_SYNC_WINSCP_KEY` | `Software\Martin Prikryl\WinSCP 2\Sessions` (under HKCU) |
| `FTP_SYNC_BACKUP_DIR` | `backups` |
| `FTP_SYNC_LOG_LEVEL` | `INFO` |

Master passwords (WinSCP / FileZilla) are not supported.

## Development

```bat
tools\run_tests.bat              :: unit tests
tools\run_integration_tests.bat  :: real stores on temp files + throwaway registry key
tools\menu_smoke.bat             :: manual menu check
tools\graphify_update.bat        :: refresh code graph
update.bat
```

Architecture, store formats and password schemes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
