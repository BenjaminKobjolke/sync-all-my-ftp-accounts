@echo off
pushd "%~dp0.."
uv run python tools\menu_smoke.py
set RESULT=%ERRORLEVEL%
popd
exit /b %RESULT%
