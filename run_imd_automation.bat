@echo off
title Automated Spatial Data Processing and Thematic Map Generation in QGIS using Python

rem Auto-detect QGIS installation
if defined IMD_QGIS_ROOT if exist "%IMD_QGIS_ROOT%" set "QGIS_ROOT=%IMD_QGIS_ROOT%"
if not defined QGIS_ROOT if exist "C:\Program Files\QGIS 3.44.14" set "QGIS_ROOT=C:\Program Files\QGIS 3.44.14"
if not defined QGIS_ROOT (
    for /d %%D in ("C:\Program Files\QGIS*") do (
        if exist "%%D\bin" set "QGIS_ROOT=%%D"
    )
)
if not defined QGIS_ROOT if exist "C:\OSGeo4W" set "QGIS_ROOT=C:\OSGeo4W"
if not defined QGIS_ROOT if exist "C:\OSGeo4W64" set "QGIS_ROOT=C:\OSGeo4W64"

set QGIS_PROCESS=
if exist "%QGIS_ROOT%\bin\qgis_process-qgis-ltr.bat" set "QGIS_PROCESS=%QGIS_ROOT%\bin\qgis_process-qgis-ltr.bat"
if not defined QGIS_PROCESS if exist "%QGIS_ROOT%\bin\qgis_process.exe" set "QGIS_PROCESS=%QGIS_ROOT%\bin\qgis_process.exe"

set QGIS_PYTHON=
if exist "%QGIS_ROOT%\bin\python-qgis-ltr.bat" set "QGIS_PYTHON=%QGIS_ROOT%\bin\python-qgis-ltr.bat"
if not defined QGIS_PYTHON if exist "%QGIS_ROOT%\bin\python-qgis.bat" set "QGIS_PYTHON=%QGIS_ROOT%\bin\python-qgis.bat"
if not defined QGIS_PYTHON if exist "%QGIS_ROOT%\bin\python3.exe" set "QGIS_PYTHON=%QGIS_ROOT%\bin\python3.exe"

set QGIS_BIN=
if exist "%QGIS_ROOT%\bin\qgis-ltr-bin.exe" set "QGIS_BIN=%QGIS_ROOT%\bin\qgis-ltr-bin.exe"
if not defined QGIS_BIN if exist "%QGIS_ROOT%\bin\qgis-bin.exe" set "QGIS_BIN=%QGIS_ROOT%\bin\qgis-bin.exe"

set BASEDIR=%~dp0
set SCRIPT=%BASEDIR%scripts\imd_automation.py
set LOGDIR=%BASEDIR%logs
set LOG=%LOGDIR%\automation_log.txt
set IMD_BASE_DIR=%BASEDIR%

if not exist "%LOGDIR%\" mkdir "%LOGDIR%"

echo. >> "%LOG%"
echo ================================================================ >> "%LOG%"
echo Vector Automation -- %DATE% %TIME% >> "%LOG%"
echo Base Dir: %BASEDIR% >> "%LOG%"
echo ================================================================ >> "%LOG%"

if not exist "%SCRIPT%" (
    echo ERROR: Script not found: %SCRIPT%
    echo ERROR: Script not found >> "%LOG%"
    pause
    exit /b 1
)

if not exist "%QGIS_PROCESS%" if not exist "%QGIS_PYTHON%" if not exist "%QGIS_BIN%" (
    echo ERROR: QGIS not found at %QGIS_ROOT%
    pause
    exit /b 1
)

echo Running vector map automation... >> "%LOG%"
echo Running vector map automation...

if exist "%QGIS_PYTHON%" (
    call "%QGIS_PYTHON%" "%SCRIPT%" %* >> "%LOG%" 2>&1
    goto :done
)

if exist "%QGIS_PROCESS%" (
    call "%QGIS_PROCESS%" run script "%SCRIPT%" >> "%LOG%" 2>&1
    goto :done
)

if exist "%QGIS_BIN%" (
    "%QGIS_BIN%" --nologo --noplugins --code "%SCRIPT%" >> "%LOG%" 2>&1
    goto :done
)

:done
echo Run finished: %DATE% %TIME% >> "%LOG%"
echo ================================================================ >> "%LOG%"
echo Vector Automation Complete
echo Output: %BASEDIR%output\
echo Log:    %LOG%
exit /b 0