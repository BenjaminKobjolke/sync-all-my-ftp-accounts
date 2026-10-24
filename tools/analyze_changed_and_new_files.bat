@echo off
call "%~dp0analyze_code.bat" --only-changed
exit /b %ERRORLEVEL%
