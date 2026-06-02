@echo off
setlocal

chcp 65001 >nul

echo ========================================
echo    TraeCacheCleaner
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8 or higher
    echo Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [INFO] Python detected, checking dependencies...
echo.

REM Check PyQt5 (仅检测，不自动安装)
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyQt5 not detected, will use CLI mode.
    echo [INFO] For GUI mode, install: pip install PyQt5
    echo.
) else (
    echo [OK] PyQt5 detected, starting GUI mode...
    echo.
)

REM Launch app
cd /d "%~dp0"
python trae_cache_cleaner.py

echo.
if %errorlevel% neq 0 (
    echo [ERROR] Program exited with error code %errorlevel%
    echo.
    pause
)
