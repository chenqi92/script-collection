#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH文件管理器启动脚本
包含重复文件检测、批量重命名、目录整理等功能
"""

import os
import sys
import subprocess

def check_requirements():
    """检查必要的依赖包"""
    try:
        import flask
        import paramiko
        print("✅ 依赖包检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少必要的依赖包: {e}")
        print("请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False

def start_server():
    """启动SSH文件管理器服务"""
    if not check_requirements():
        return False
    
    print("🚀 启动SSH文件管理器...")
    print("📋 功能包括:")
    print("   • 重复文件检测与删除")
    print("   • 批量重命名 (支持正则表达式)")
    print("   • 目录整理 (文件自动建文件夹)")
    print("   • SSH远程文件管理")
    print("")
    print("🌐 访问地址: http://localhost:5001")
    print("⏹️  停止服务: 按 Ctrl+C")
    print("=" * 50)
    
    try:
        # 运行SSH文件管理器
        os.system("python3 ssh_file_manager.py")
    except KeyboardInterrupt:
        print("\n👋 SSH文件管理器已停止")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

if __name__ == "__main__":
    start_server()