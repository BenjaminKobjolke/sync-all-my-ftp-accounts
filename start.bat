@echo off
pushd "%~dp0"
uv run ftp-sync %*
set RESULT=%ERRORLEVEL%
popd
exit /b %RESULT%
