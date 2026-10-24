Before writing or editing a batch file here, read [TICKETS_WATCHER_COMMANDS.md](TICKETS_WATCHER_COMMANDS.md): it lists what works as a Tickets Watcher command.

## Post-Implementation Code Analysis

After implementing a feature, finishing a plan, or fixing a bug, run the changed-files analyzer and fix every reported issue in the changed files before considering the work complete:

```powershell
cmd /c ".\tools\analyze_changed_and_new_files.bat"
```

The script uses the analyzer's `--only-changed` mode and returns a non-zero exit code when it finds any reported issue. Use `tools\analyze_code.bat` for a full-project audit.
