@echo off
chcp 65001 >nul
echo ========================================
echo      SSH 文件管理器启动脚本
echo ========================================
echo.

REM 获取当前脚本所在目录
cd /d "%~dp0"

REM 检查Python是否安装
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到Python安装
    echo    请先安装Python 3.7+ 从: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python版本: %PYTHON_VERSION%

REM 检查pip是否可用
echo.
echo [2/4] 检查pip包管理器...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: pip不可用，请重新安装Python并确保包含pip
    pause
    exit /b 1
)
echo ✅ pip可用

REM 检查requirements.txt是否存在
echo.
echo [3/4] 检查并安装依赖包...
if not exist "requirements.txt" (
    echo ❌ 错误: requirements.txt文件不存在
    echo    请确保在正确的目录运行此脚本
    pause
    exit /b 1
)

echo 📦 安装依赖包...
pip install -r requirements.txt --quiet --disable-pip-version-check

if errorlevel 1 (
    echo ⚠️  警告: 部分依赖包安装可能失败，但仍尝试启动应用...
    echo.
) else (
    echo ✅ 依赖包安装完成
)

REM 检查主程序文件
echo.
echo [4/4] 启动应用程序...
if not exist "ssh_file_manager.py" (
    echo ❌ 错误: ssh_file_manager.py文件不存在
    echo    请确保在正确的目录运行此脚本
    pause
    exit /b 1
)

echo.
echo 🚀 启动SSH文件管理器...
echo 📍 应用地址: http://localhost:5000
echo 📖 使用说明: 
echo    - 本地模式: 直接使用本地文件管理功能
echo    - 远程模式: 需要先连接SSH服务器
echo.
echo ⏹️  按 Ctrl+C 停止服务器
echo ========================================
echo.

python ssh_file_manager.py

echo.
echo 程序已退出，按任意键关闭窗口...
pause >nul 