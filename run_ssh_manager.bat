@echo off
echo ========================================
echo      SSH 文件管理器启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python安装。请先安装Python 3.7+
    pause
    exit /b 1
)

echo 检查并安装依赖包...
pip install -r requirements.txt

if errorlevel 1 (
    echo 警告: 依赖包安装可能失败，但仍尝试启动应用...
)

echo.
echo 启动SSH文件管理器...
echo 应用将在 http://localhost:5000 启动
echo 按 Ctrl+C 停止服务器
echo.

python ssh_file_manager.py

pause 