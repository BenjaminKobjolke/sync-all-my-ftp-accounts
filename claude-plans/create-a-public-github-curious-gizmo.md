# Public GitHub repo for sync-all-my-ftp-accounts

## Context
Project not yet git repo. User wants public repo `BenjaminKobjolke/sync-all-my-ftp-accounts` (name free, `gh` logged in as BenjaminKobjolke).

Tool reads/writes FTP credentials, so leak check matters before public push.

## Secret check (done, read-only)
- `backups/` (real sitemanager.xml, NppFTP.xml, fman bookmarks with credentials) already in `.gitignore`. Stays ignored.
- `graphify-out/`, caches, `.venv`, `coding-rules.json` ignored.
- Scan of remaining files (src, tests, docs, tools, claude-plans, .claude): only `example.com` hosts, no real hosts/passwords.

## Steps
1. Invoke `github:create-repo` skill (XIDA standard flow); follow it with these inputs:
   - name `sync-all-my-ftp-accounts`, visibility **public**, description from README first line.
2. Before first commit: `git init`, `git add -A`, then `git status` + re-grep staged files for `backups/`, `.xml`, `Bookmarks` — abort if any credential file staged.
3. First commit (with Co-Authored-By line), `gh repo create BenjaminKobjolke/sync-all-my-ftp-accounts --public --source . --push`.

## Verification
- `gh repo view BenjaminKobjolke/sync-all-my-ftp-accounts` shows public.
- `git ls-files | grep -iE "backups|\.xml$"` empty.
