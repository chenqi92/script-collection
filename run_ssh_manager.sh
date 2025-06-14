#!/bin/bash

# 设置错误时退出
set -e

echo "========================================"
echo "     SSH 文件管理器启动脚本"
echo "========================================"
echo

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查Python是否安装
echo "[1/4] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未检测到Python3安装"
    echo "   请先安装Python 3.7+ 从: https://www.python.org/downloads/"
    echo "   或使用包管理器安装: sudo apt install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d ' ' -f2)
echo "✅ Python版本: $PYTHON_VERSION"

# 检查pip是否可用
echo
echo "[2/4] 检查pip包管理器..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: pip3不可用"
    echo "   请安装pip: sudo apt install python3-pip"
    exit 1
fi
echo "✅ pip3可用"

# 检查requirements.txt是否存在
echo
echo "[3/4] 检查并安装依赖包..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: requirements.txt文件不存在"
    echo "   请确保在正确的目录运行此脚本"
    exit 1
fi

echo "📦 安装依赖包..."
pip3 install -r requirements.txt --quiet --disable-pip-version-check --user

if [ $? -ne 0 ]; then
    echo "⚠️  警告: 部分依赖包安装可能失败，但仍尝试启动应用..."
    echo
else
    echo "✅ 依赖包安装完成"
fi

# 检查主程序文件
echo
echo "[4/4] 启动应用程序..."
if [ ! -f "ssh_file_manager.py" ]; then
    echo "❌ 错误: ssh_file_manager.py文件不存在"
    echo "   请确保在正确的目录运行此脚本"
    exit 1
fi

echo
echo "🚀 启动SSH文件管理器..."
echo "📍 应用地址: http://localhost:5000"
echo "📖 使用说明: "
echo "   - 本地模式: 直接使用本地文件管理功能"
echo "   - 远程模式: 需要先连接SSH服务器"
echo
echo "⏹️  按 Ctrl+C 停止服务器"
echo "========================================"
echo

# 捕获中断信号，优雅退出
trap 'echo -e "\n程序已停止"; exit 0' INT

python3 ssh_file_manager.py 