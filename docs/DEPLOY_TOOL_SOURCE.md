# Deploy Tool Config as Sync Source

Reads the FTP logins of **one** deploy-tool config file (`config_*.php`, e.g.
`D:\wamp64\www\animate-web-interface\deploy\config_animate-web.php`) and creates them in
WinSCP, FileZilla, Notepad++ NppFTP and fman. The deploy tool is a **source only**; nothing
is ever written to it.

The config is not parsed in Python. The deploy tool reads it with its own
`XDDeploy\Config` classes through `export_ftp.php`, so presets, defaults (`transferType` FTP,
port 0 = protocol default) and validation are exactly those of a real deploy.

## Setup

1. The deploy tool must contain `export_ftp.php` and its bundled `php\php.exe`.
2. Add its folder to `settings.json` (gitignored; see `settings.example.json`):

   ```json
   {
     "deploy_tool_path": "D:/wamp64/www/deploy-tool"
   }
   ```

   - Missing key, or no `export_ftp.php` there → **Deploy tool config** is not offered.
   - Present but not a non-empty string → the run stops with an error.
   - Other settings location: `FTP_SYNC_SETTINGS_PATH`.

## Usage

```bat
start.bat
:: pick "Deploy tool config", then enter the config path when asked:
:: Deploy config file: "D:\wamp64\www\animate-web-interface\deploy\config_animate-web.php"

start.bat --source deploytool --deploy-config D:\path\to\deploy\config_site.php
```

The prompt accepts the surrounding quotes from Explorer's "Copy as path" and asks again
while the file does not exist.

## Imported accounts

`export_ftp.php` prints one JSON entry per config in the file:

| Field | Value |
|---|---|
| name | `name` of the config entry |
| folder | none — created at top level |
| host / user / password | `ftp.server` / `ftp.username` / `ftp.password` |
| protocol | `ftp.transferType` (`FTP`, `FTPS`, `SFTP`; default FTP) |
| port | `ftp.port`, or the protocol default (21 / 22) when 0 or missing |
| remote dir | `ftp.root` without trailing `/` (`/` → none) |

A file with two entries (e.g. `/` and `/vendor`) on the same host + user yields two accounts;
the second is reported `found` once the first was created (matching ignores the remote dir).

An invalid config (e.g. an empty `*_example.php`) makes the deploy tool print its validation
errors without a JSON line; the run stops and shows that output.

SFTP configs with a `keyFile` and an empty password get the usual password prompt
(enter existing / leave empty) before creation.

## Deploy-tool side

| File | Role |
|---|---|
| `export_ftp.php` | CLI: same bootstrap as `deploy.php` (+ `Translations::setPath`), prints the JSON line; missing file → exit 1 |
| `XDDeploy/Config/Manager.php` | `getConfigsFromFile($file)` — load a config from any path; shared `createConfigs()` also used by `getConfigByIndex` / `getConfigByName` |
| `XDDeploy/Config/FtpExport.php` | `toJson(Config[])` — serializes the resolved `Ftp` getters |
| `Tests/offline/ftp_export_tests.php` | Offline tests: defaults, single config, invalid config (`php Tests/offline/run.php`) |

## Implementation (this repo)

| File | Role |
|---|---|
| `src/ftp_sync/config/deploy_tool.py` | `load_deploy_tool_path(path)` |
| `src/ftp_sync/config/settings.py` | `Settings.deploy_tool_path` |
| `src/ftp_sync/stores/deploy_tool_store.py` | `DeployToolStore` — prompt, subprocess, JSON → `FtpAccount`; `add` raises |
| `src/ftp_sync/stores/registry.py` | `build_stores(..., deploy_config)` adds the store |
| `src/ftp_sync/main.py` | `--deploy-config PATH` |
| `src/ftp_sync/models.py` | `AppKind.DEPLOY_TOOL` (not writable) |

## Tests

- `tests/unit/test_deploy_tool_store.py` — mapping, explicit port, missing JSON / failed exit,
  unknown `transferType`, path prompt with quotes and retry, availability, source-only contract.
- `tests/unit/test_deploy_tool_config.py` — `deploy_tool_path` missing / valid / invalid.
- `tests/integration/test_deploy_tool_export.py` — real deploy tool on a temp config; runs only
  with `FTP_SYNC_TEST_DEPLOY_TOOL` set to the deploy-tool folder.

## Not supported

- Importing several config files at once.
- Using the config file name as a folder.
