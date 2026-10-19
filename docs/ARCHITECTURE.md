# Architecture

Python package in `src/ftp_sync/`. Entry point `ftp_sync.main:main` (`start.bat`, `uv run ftp-sync`).

## Modules

| Module | Role |
|---|---|
| `main.py` | CLI args (`--source`), central error handler (logs error, exit code 1) |
| `config/settings.py` | `Settings` — store paths, WinSCP key, backup dir, log level, KAS accounts; env overrides |
| `config/kas_accounts.py` | `load_kas_accounts(path)` — validated `KasAccountConfig` list from `settings.json` |
| `constants.py` | All string/number constants (paths, XML tags, registry value names, protocol codes) |
| `models.py` | `FtpAccount` (frozen), `FtpProtocol` (FTP/FTPS/SFTP), `AppKind` |
| `app_logger.py` | `AppLogger` — only logging entry point; never receives passwords |
| `backup.py` | `BackupCoordinator` — backs up each store once per run before its first write |
| `account_matcher.py` | `AccountIndex` + `MatchStatus` — is a source account present in a target? |
| `menu.py` | Only `pick` call site (`backend="blessed"`); refuses to run without a console |
| `sync_runner.py` | Feature flow: pick source, ensure targets closed, report per account, create where missing, summary |
| `password_prompt.py` | `ask_password` — password for a source account without one (existing / empty / new on the server) |
| `running_apps.py` | `running_process_names()` — lowercased exe names from `tasklist /FO CSV /NH`; empty set on failure |
| `stores/account_store.py` | `AccountStore` + `PasswordChangingStore` Protocols, helpers (`unique_name`, `join_folder`, `parse_port`) |
| `stores/kas_store.py` | `KasStore` — All-Inkl FTP users via `kas_api.KasClient`; source only |
| `stores/registry.py` | `build_stores(settings, backup)` — the list of all stores |
| `stores/*_store.py` | One store per app (load + add) |
| `stores/*_password.py` | Password codecs (WinSCP, NppFTP) |
| `stores/xml_file.py` | Shared XML helpers for FileZilla/NppFTP |

## Store contract

```python
class AccountStore(Protocol):
    kind: AppKind
    def is_available(self) -> bool: ...          # file / registry key exists
    def load(self) -> list[FtpAccount]: ...
    def add(self, account: FtpAccount) -> None: ...  # backup first, never overwrites
    def supports(self, protocol: FtpProtocol) -> bool: ...
```

`add` never replaces an existing entry: a name clash becomes `name (2)`, `name (3)`, ...

`FtpAccount.folder` uses `/` between nesting levels. It maps to the WinSCP session path,
FileZilla `<Folder>` elements and the NppFTP `parent` attribute. fman has no folders.

### Source-only stores

`AppKind.is_writable` is False for `ALL_INKL`. `SyncRunner` never uses such a store as a
target (never loads it, never asks for its process), `supports()` is False and `add()` raises.
`KasStore` also implements `PasswordChangingStore.change_password` (KAS `update_ftpuser`),
which `password_prompt.ask_password` offers as "Set a new password".

## Matching

`FtpAccount.match_key()` = `(host.lower(), user.lower())`. Port and protocol are ignored,
because the same login is often saved as FTP in one app and FTPS in another.

| Status | Meaning |
|---|---|
| `found` | Key matches and one match has the same password, or the source has no password (All-Inkl) |
| `DIFFERENT PASSWORD` | Key matches, password differs — reported only |
| `missing` | No match, target supports the protocol — offered for creation |
| `unsupported` | No match, target cannot store the protocol (SFTP to fman) |

## Running target apps

The apps keep their site list in memory and write it back on exit, wiping accounts added
while they run. After the source pick, `SyncRunner._ensure_closed` compares each target's
`AppKind.process_name` (`constants.APP_PROCESS_NAMES`) with `running_apps.running_process_names()`.

- Interactive: warning + menu `RunningAction` — Retry (check again), Continue anyway, Quit
  (returns an empty summary, nothing written).
- Scripted (`--source`): raises `RuntimeError`, reported by the central handler.
- The source app is ignored (only read). Target stores are loaded after the check, so an app
  closed during Retry contributes its freshly flushed list.
- `tasklist` failure logs a warning and the check passes — it is a safety net, not a gate.

## Store formats

### WinSCP

- Registry `HKCU\Software\Martin Prikryl\WinSCP 2\Sessions\<name>`; `Default Settings` skipped.
- Session names are %-escaped; `/` separates folders.
- Values: `HostName`, `PortNumber` (DWORD), `UserName`, `Password`, `FSProtocol`
  (5 = FTP, absent/other = SFTP), `Ftps` (0 = none, 3 = explicit TLS), `RemoteDirectory`.
- Password: WinSCP's reversible obfuscation (`winscp_password.py`, port of `Security.cpp`).
  Each byte stored as hex of `~byte ^ 0xA3`, plaintext prefixed with `user + host`, padded with
  random bytes. Only valid without a WinSCP master password.
- Backup: `reg export` of the Sessions key to `winscp_sessions.reg`.

### FileZilla

- `%APPDATA%\FileZilla\sitemanager.xml`, `<Servers>` with nested `<Folder>`/`<Server>`.
- Protocol: 0 = FTP, 1 = SFTP, 3/4 = FTPS (implicit/explicit). New entries: FTP 0, FTPS 4, SFTP 1.
- Password: `<Pass encoding="base64">`. Master-password (`encoding="crypt"`) not supported.
- `RemoteDir` format: `1 0 <len> <segment> <len> <segment>...` (`/www/html` = `1 0 3 www 4 html`).

### Notepad++ NppFTP

- `%APPDATA%\Notepad++\plugins\config\NppFTP\NppFTP.xml`, `<Profiles><Profile .../>`.
- `securityMode`: 0 = FTP, 1/2 = FTPS (implicit/explicit), 3 = SFTP. New FTPS entries use 2.
- Password: DES-CFB64, key `NppFTP00` with odd parity, IV = the same key, hex upper case
  (`nppftp_password.py`, mirrors NppFTP `Encryption.cpp`). A custom NppFTP master password
  is not supported; such profiles load with an empty password and a warning.

### fman FTP plugin

- `%APPDATA%\fman\Plugins\User\Settings\FTP Bookmarks (Windows).json`.
- `{"ftp://<name>": ["<scheme>://<user>:<password>@<host>:<port>", "<path>", <optional web url>]}`.
- User and password are percent-encoded in the URL (the plugin unquotes them). FTP/FTPS only.

### All-Inkl (KAS API)

- KAS logins from `settings.json` (`kas_accounts`), one `KasClient` per entry.
- `get_ftpusers` → `FtpAccount(name=comment or login, host=<ftp_hostname>.kasserver.com,
  user=login, password="", FTPS, port 21, folder=<KAS account name>)`. No `remote_dir`:
  sub-users are chrooted to their `ftp_path`.
- The API never returns FTP passwords; `SyncRunner` asks per created account.

## Adding a new app

1. Add an `AppKind` member, its label in `constants.APP_LABELS` and its lowercased
   executable name in `constants.APP_PROCESS_NAMES`.
2. Add the default location to `constants.py` and a field + env override to `Settings`.
3. Write `stores/<app>_store.py` implementing `AccountStore`; call the `BackupCoordinator`
   before the first write.
4. Register it in `stores/registry.py`.
5. Add load/add tests (see `tests/unit/test_file_stores.py`) and extend the integration test.

## Tests

- `tests/unit/` — codecs, file stores on `tmp_path`, matcher, runner with patched menu,
  `running_apps` with patched `subprocess.run`.
- `tests/conftest.py` autouse fixture `no_running_apps` patches the process check to "nothing
  running", so tests never see the developer's open apps. `test_running_apps.py` overrides it.
- `tests/integration/` — real stores on temp files plus a throwaway registry key
  `HKCU\Software\ftp-sync-test` (deleted afterwards). Never touches real app config.
- `tools/menu_smoke.bat` — manual check that arrow keys still work after a subprocess.
