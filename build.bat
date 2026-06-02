@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    TraeCacheCleaner - 打包脚本
echo ========================================
echo.

REM 使用当前 Python 环境
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 未找到
    pause
    exit /b 1
)

echo [1/3] 检查依赖...

REM 检测当前环境是否有 PyQt5
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 当前环境缺少 PyQt5，正在安装...
    pip install PyQt5 pyinstaller -q
    if !errorlevel! neq 0 (
        echo [ERROR] 安装失败
        pause
        exit /b 1
    )
) else (
    echo [OK] PyQt5 已就绪
)

REM 检测 PyInstaller
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    pip install pyinstaller -q
    if !errorlevel! neq 0 (
        echo [ERROR] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

echo [2/3] 正在打包...

REM 清理旧的打包文件
if exist "output" rmdir /s /q "output" >nul 2>&1
if exist "build_tmp" rmdir /s /q "build_tmp" >nul 2>&1
if exist "TraeCacheCleaner.spec" del "TraeCacheCleaner.spec" >nul 2>&1

REM 执行打包
if exist "TraeCacheCleaner.ico" (
    pyinstaller --onefile --console --name "TraeCacheCleaner" --icon "TraeCacheCleaner.ico" --add-data "TraeCacheCleaner.ico;." --distpath "output" --workpath "build_tmp" "trae_cache_cleaner.py"
) else (
    pyinstaller --onefile --console --name "TraeCacheCleaner" --distpath "output" --workpath "build_tmp" "trae_cache_cleaner.py"
)

if %errorlevel% neq 0 (
    echo [ERROR] 打包失败！
    pause
    exit /b 1
)

echo [3/3] 打包成功！

for %%f in ("output\TraeCacheCleaner.exe") do (
    set "FILESIZE=%%~zf"
    set /a "SIZE_MB=!FILESIZE! / 1048576"
    echo 输出: !SIZE_MB! MB  output\TraeCacheCleaner.exe
)

REM 清理临时文件
if exist "build_tmp" rmdir /s /q "build_tmp" >nul 2>&1
if exist "TraeCacheCleaner.spec" del "TraeCacheCleaner.spec" >nul 2>&1

echo.
echo GUI: 双击 output\TraeCacheCleaner.exe
echo CLI: output\TraeCacheCleaner.exe --cli
echo.
pause
