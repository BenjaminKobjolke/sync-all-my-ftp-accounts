@echo off
if /I "%TICKETS_WATCHER_COMMAND_RUN%"=="1" (
  echo This arrow-key menu smoke check requires a real terminal; skipping in Tickets Watcher.
  exit /b 0
)
pushd "%~dp0.."
uv run python tools\menu_smoke.py
set RESULT=%ERRORLEVEL%
popd
exit /b %RESULT%
