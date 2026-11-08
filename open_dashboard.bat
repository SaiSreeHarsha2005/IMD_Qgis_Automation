@echo off
title IMD Dashboard Server

set "ROOT=%~dp0"
cd /d "%ROOT%"

rem Detect QGIS Python runner (has openpyxl, pandas, and QGIS libs pre-installed)
set "PY_RUNNER="
if defined IMD_QGIS_ROOT (
    if exist "%IMD_QGIS_ROOT%\bin\python-qgis-ltr.bat" set "PY_RUNNER=%IMD_QGIS_ROOT%\bin\python-qgis-ltr.bat"
    if not defined PY_RUNNER if exist "%IMD_QGIS_ROOT%\bin\python-qgis.bat" set "PY_RUNNER=%IMD_QGIS_ROOT%\bin\python-qgis.bat"
)
if not defined PY_RUNNER if exist "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" set "PY_RUNNER=C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat"
if not defined PY_RUNNER (
    for /d %%D in ("C:\Program Files\QGIS*") do (
        if exist "%%D\bin\python-qgis-ltr.bat" set "PY_RUNNER=%%D\bin\python-qgis-ltr.bat"
        if not defined PY_RUNNER if exist "%%D\bin\python-qgis.bat" set "PY_RUNNER=%%D\bin\python-qgis.bat"
    )
)
if not defined PY_RUNNER (
    where python >nul 2>&1
    if %errorlevel% equ 0 set "PY_RUNNER=python"
)

if not defined PY_RUNNER (
    echo [ERROR] Python not found. Please install QGIS or Python 3.x.
    pause
    exit /b 1
)

set PORT=8765

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /R ":%PORT%.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [OK] Using Python runner: %PY_RUNNER%
echo [OK] Starting dashboard server on http://localhost:%PORT%
echo [OK] Dashboard URL: http://localhost:%PORT%/
echo Press Ctrl+C to stop the server.

start "" /B timeout /T 1 /NOBREAK >nul && start "" "http://localhost:%PORT%/"
"%PY_RUNNER%" serve_dashboard.py %PORT%

pause
