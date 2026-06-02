@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo    TraeCacheCleaner - Build
echo ========================================
echo.

REM Use system default Python
set "BUILD_PYTHON=python"

echo [1/2] Building with: %BUILD_PYTHON%

REM Clean old files
if exist "output" rmdir /s /q output

if exist "TraeCacheCleaner.ico" (
    "%BUILD_PYTHON%" -m PyInstaller --onefile --console --name "TraeCacheCleaner" --icon "TraeCacheCleaner.ico" --add-data "TraeCacheCleaner.ico;." --distpath "output" --workpath "build_tmp" "trae_cache_cleaner.py"
) else (
    "%BUILD_PYTHON%" -m PyInstaller --onefile --console --name "TraeCacheCleaner" --distpath "output" --workpath "build_tmp" "trae_cache_cleaner.py"
)

if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

REM Clean temp files
if exist "build_tmp" rmdir /s /q build_tmp
if exist "TraeCacheCleaner.spec" del /f TraeCacheCleaner.spec

echo [2/2] Done

for %%f in ("output\TraeCacheCleaner.exe") do (
    set /a SIZE=%%~zf / 1048576
    echo Output: !SIZE! MB  output\TraeCacheCleaner.exe
)

echo.
echo Run: output\TraeCacheCleaner.exe
pause
