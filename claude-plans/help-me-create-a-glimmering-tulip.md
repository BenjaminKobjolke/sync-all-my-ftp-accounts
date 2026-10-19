# sync-all-my-ftp-accounts — initial tool

## Context

User keeps FTP credentials in four apps (WinSCP, FileZilla, Notepad++ NppFTP, and
the fman FTP plugin); their account data drifts apart. Build a Python CLI that lets
the user pick one source app, walks its stored accounts, reports whether each other
app already has each account, and offers to create missing accounts.

This is a greenfield project. There is no application source yet, so the plan follows
the repository conventions supplied by `CODING_RULES.md` and `IMPLEMENTATION_FLOW.md`.

Decisions already made: scaffold from `python_setup_files` rather than a template,
use Codex delegation, enable the graphify addon, and use `pick[blessed]` menus.

## Convention findings applied

- Use a `src/ftp_sync/` package, `tests/unit/` and `tests/integration/`, `uv` with
  `pyproject.toml`, and Windows `.bat` wrappers, matching the available Python setup
  files and the project rules.
- Keep public module boundaries typed: `Settings`, `FtpAccount`, enums, result/status
  objects, and the `AccountStore` Protocol. Do not pass untyped dictionaries between
  stores, matching the root rule against bag-of-keys APIs.
- Keep platform/file-format details inside store modules; shared paths belong to
  `Settings`, shared labels/tags/registry strings to `constants.py`, and interactive
  behavior behind the single `menu.py` wrapper.
- Run graphify commands from the repository root. The initial graph is intentionally
  absent; build it after scaffolding and refresh it after later code changes.

## Setup and project structure

1. Apply the already selected rules with `/coding-rules:apply` through `apply.py`:
   `COMMON_RULES.md`, `IMPLEMENTATION_FLOW.md`, `PYTHON_RULES.md`,
   `implementation_flow_addons/graphify.md`, and `implementation_flow_addons/graphify_flow.md`,
   with `--delegation codex`. Do not add `DESIGN_RULES` or optional Python files.
2. Scaffold using the reusable files in
   `D:/GIT/BenjaminKobjolke/claude-coding-rules/plugins/coding-rules/rules/python_setup_files/`:
   `install.bat`, `update.bat`, and the test-runner templates. Add `start.bat`,
   `README.md`, `.gitignore`, and a `pyproject.toml` using `uv`, `requires-python >=3.12`,
   Ruff, mypy, and pytest. Keep `ruff`'s `extend-exclude = ["*.md"]`.
3. Add the Codex wrapper files/permissions required by the applied rules.
4. Configure graphify according to `graphify_setup_files/SETUP.md`, scan `src/`, and
   record that scan root in `CLAUDE.md`. Keep `graphify-out/` ignored.
5. Add runtime dependencies `pick[blessed]` and, only if the verified NppFTP scheme
   needs it, `pycryptodome`; add dev dependencies `pytest`, `ruff`, and `mypy`.
   Resolve current compatible versions during implementation and record them in the lockfile.

## Shared domain and infrastructure

- `src/ftp_sync/models.py`: `FtpProtocol` (FTP, FTPS, SFTP), `AppKind` (WINSCP,
  FILEZILLA, NPPFTP, FMAN), and frozen `FtpAccount(name, folder, host, port, user,
  password, protocol, remote_dir)`. `match_key()` returns `(host.lower(), user.lower())`.
- `src/ftp_sync/constants.py`: store labels, XML tags, and registry path constants;
  do not duplicate these literals in individual stores.
- `src/ftp_sync/config/settings.py`: frozen `Settings` containing all four store paths
  and the backup directory, with environment-variable overrides. Store modules receive
  this object instead of reading environment variables themselves.
- `src/ftp_sync/app_logger.py`: the `AppLogger` wrapper and one level toggle. Never log
  passwords or full credential URLs.
- `src/ftp_sync/stores/account_store.py`: `AccountStore` Protocol with `kind`,
  `is_available()`, `load() -> list[FtpAccount]`, `add(account)`, and
  `supports(protocol)`.
- `src/ftp_sync/backup.py`: one backup coordinator that performs the first backup per
  store per run, copying file stores to `backups/<timestamp>/` and using `reg export`
  for the WinSCP Sessions key. Store writers call this shared coordinator rather than
  implementing their own backup guards.

## Credential stores

All paths come from `Settings`; no store hardcodes an application path.

| App | Location | Format | Password |
|---|---|---|---|
| WinSCP | Registry `HKCU\\Software\\Martin Prikryl\\WinSCP 2\\Sessions\\<name>` (`/` denotes folders) | `HostName, PortNumber, UserName, Password, FSProtocol (5=FTP, absent=SFTP), Ftps, RemoteDirectory` | WinSCP simple obfuscation (magic `0xA3`, key = user + host), reversible both ways |
| FileZilla | `%APPDATA%\\FileZilla\\sitemanager.xml` | Nested `<Folder>` and `<Server>` records under `<Servers>` | Base64 |
| NppFTP | `%APPDATA%\\Notepad++\\plugins\\config\\NppFTP\\NppFTP.xml` | `<Profiles><Profile ...>` | Hex plus NppFTP's fixed-key encryption |
| fman | `%APPDATA%\\fman\\Plugins\\User\\Settings\\FTP Bookmarks (Windows).json` | URL-keyed JSON bookmark values | Plaintext in URL; FTP/FTPS only |

Implement:

- `stores/winscp_store.py` and `stores/winscp_password.py` using `winreg`.
- `stores/filezilla_store.py` using `xml.etree`, creating missing folder paths.
- `stores/nppftp_store.py` and `stores/nppftp_password.py`. Verify the scheme from
  NppFTP's `Encryption.cpp` first; prove it by decrypting a profile whose host also
  exists in FileZilla and comparing passwords in code without printing them. Stop and
  report a mismatch instead of writing data.
- `stores/fman_store.py` using `json` and `urllib.parse`, quoting user/password in URLs;
  reject SFTP through `supports()`.

Carry folders through the shared `FtpAccount` where supported: WinSCP `folder/name`,
FileZilla `<Folder>`, and NppFTP `parent`. fman has no folder field; its key is the URL.

## Matching and CLI flow

- `account_matcher.py`: for one source account and loaded targets, return typed per-target
  results with `MatchStatus`: `MISSING`, `FOUND`, `FOUND_DIFFERENT_PASSWORD`, or
  `UNSUPPORTED` (for example SFTP to fman). Matching uses `FtpAccount.match_key()`;
  password comparison is separate from identity matching.
- `menu.py`: the only `pick` integration (`backend="blessed"`), refusing non-TTY use.
- `sync_runner.py` and `main.py`: support the interactive flow and `--source <app>` for
  non-interactive start.

Flow:

1. Detect available stores and warn that FileZilla and Notepad++ should be closed because
   they overwrite their files on exit; let the user choose a source app.
2. Load the source and all targets once.
3. For each source account, display `name host user` and every target status. If any
   target is `MISSING`, show a multiselect menu defaulting to all missing targets plus
   `skip` and `quit`; create selected accounts through the shared backup coordinator.
   Report `FOUND_DIFFERENT_PASSWORD` only; do not overwrite it in this feature.
4. Print created/skipped/error totals per app. Passwords never appear in logs or output.

## TDD and verification

Create shared test fixtures/builders for `FtpAccount`, sample store data, and fake
`AccountStore` objects so store and runner tests do not duplicate setup. Keep format-
specific samples in the owning store's tests.

- `tests/unit/`: WinSCP password roundtrip plus known vector; NppFTP roundtrip;
  FileZilla parse/add with `tmp_path`; fman parse/add; matcher statuses; and runner
  behavior using patched `menu.show_menu` and `MagicMock(spec=AccountStore)`.
- `tests/integration/`: real roundtrips for each store on temporary files; WinSCP against
  the throwaway key `HKCU\\Software\\ftp-sync-test\\Sessions` with `Settings` overrides;
  clean all created state afterward.
- Add `tools/menu_smoke.py` and its `.bat` wrapper per `PYTHON_RULES`.
- Verify with `tools/run_tests.bat`, `tools/run_integration_tests.bat`, `ruff check`,
  `ruff format --check`, and `mypy src`.
- Manual check: run `start.bat`, choose WinSCP, inspect statuses for known accounts,
  create one account in a target, verify it in that app, and confirm a backup exists.
- Finish with the required Codex plan-DRY/post-implementation checks and the graphify
  refresh from the repository root.

## Out of scope

Password-mismatch fixing, delete/rename synchronization, and master-password support
(none is currently in use). Add these as later features.

## SUMMARY CONVENTION CHECK

Reused the repository's `src/` Python layout, `uv`/Ruff/mypy/pytest toolchain, setup
templates, Windows test wrappers, typed boundary objects, and root graphify/delegation
workflow. No existing application utilities or source naming conventions were available
because this is a greenfield repository.

## SUMMARY DRY

Centralized shared account identity and status types in the domain model, configuration
in `Settings`, constants in `constants.py`, menu integration in `menu.py`, and backup-
once behavior in `backup.py`. Added shared test fixtures/fakes to prevent repeated
credential and runner setup. No other consolidation was justified before source code
exists.
