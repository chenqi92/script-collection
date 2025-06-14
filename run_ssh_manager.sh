#!/bin/bash

echo "========================================"
echo "     SSH 文件管理器启动脚本"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python3安装。请先安装Python 3.7+"
    exit 1
fi

echo "检查并安装依赖包..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "警告: 依赖包安装可能失败，但仍尝试启动应用..."
fi

echo
echo "启动SSH文件管理器..."
echo "应用将在 http://localhost:5001 启动"
echo "按 Ctrl+C 停止服务器"
echo

python3 ssh_file_manager.py