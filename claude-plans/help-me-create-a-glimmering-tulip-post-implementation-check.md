# Post-Implementation DRY Check

## SUMMARY

Found 3 DRY opportunities in the files listed by `help-me-create-a-glimmering-tulip-changed-files.md`. No code was modified.

## Findings

### 1. Share the repeated batch-script dependency and test-runner flow

Affected files:

- `install.bat`
- `update.bat`
- `tools/run_tests.bat`
- `tools/run_integration_tests.bat`

Rationale: These scripts independently check whether `uv` is installed, print nearly identical error messages, invoke `uv`, capture `%ERRORLEVEL%`, and print success/failure banners. A shared batch helper or a single parameterized test runner would keep the setup and failure behavior consistent and reduce maintenance duplication.

### 2. Consolidate the common backup-once bookkeeping

Affected files:

- `src/ftp_sync/backup.py`

Rationale: `backup_file()` and `backup_registry()` both check `_done`, create the timestamped directory, mark the source as backed up, and log the target. A small private helper for the common once-per-source lifecycle could centralize that behavior while leaving the file-copy and registry-export operations as separate callbacks or operations.

### 3. Extract shared file-backed store scaffolding

Affected files:

- `src/ftp_sync/stores/filezilla_store.py`
- `src/ftp_sync/stores/nppftp_store.py`
- `src/ftp_sync/stores/fman_store.py`

Rationale: Each store repeats the same path/backup constructor state and the `Path.is_file()` availability check; the XML stores also repeat the pattern of backing up before parsing, loading the file, and writing it back. A narrowly scoped file-store base/helper could own only this common lifecycle and keep each format-specific parser and serializer independent. Avoid forcing the differing JSON/XML data models into one abstraction.

## Scope and validation

Only the files listed in `claude-plans/help-me-create-a-glimmering-tulip-changed-files.md` were reviewed. The repository graph was absent at `graphify-out/graph.json`, so no graph query result was available. No tests or linters were run because this check requested suggestions only and made no code changes.
