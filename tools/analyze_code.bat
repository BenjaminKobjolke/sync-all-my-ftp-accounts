@echo off
setlocal
pushd "%CD%" || exit /b 1

if not exist "%~dp0analyze_code_config.bat" goto config_error
call "%~dp0analyze_code_config.bat"
cd /d "%~dp0.." || goto setup_error

if exist ".venv\Scripts" set "PATH=%CD%\.venv\Scripts;%PATH%"
set "ANALYZER_MODE="
set "ANALYZER_LIMIT=--maxamountoferrors 50"
if /i "%~1"=="--only-changed" set "ANALYZER_MODE=--only-changed"
if /i "%~1"=="--only-changed" set "ANALYZER_LIMIT="

"%CLI_ANALYZER_PATH%\venv\Scripts\python.exe" "%CLI_ANALYZER_PATH%\main.py" --language "%LANGUAGE%" --path . %ANALYZER_MODE% --verbosity minimal --output code_analysis_results %ANALYZER_LIMIT% --rules code_analysis_rules.json --fail-on-findings
set "RC=%ERRORLEVEL%"
goto cleanup

:config_error
echo ERROR: analyze_code_config.bat not found.
echo Copy analyze_code_config.example.bat to analyze_code_config.bat and set CLI_ANALYZER_PATH and LANGUAGE.
set "RC=1"
goto cleanup

:setup_error
echo ERROR: Could not change to the repository root.
set "RC=1"

:cleanup
popd
endlocal & exit /b %RC%
