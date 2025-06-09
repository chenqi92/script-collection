#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSH文件管理器测试脚本
用于验证应用的基本功能和依赖是否正确安装
"""

import sys
import subprocess
import importlib.util

def test_python_version():
    """测试Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro} (符合要求)")
        return True
    else:
        print(f"❌ Python版本: {version.major}.{version.minor}.{version.micro} (需要3.7+)")
        return False

def test_dependencies():
    """测试依赖包是否安装"""
    print("\n🔍 检查依赖包...")
    required_packages = {
        'flask': 'Flask',
        'paramiko': 'paramiko',
        'werkzeug': 'Werkzeug',
        'jinja2': 'Jinja2',
        'markupsafe': 'MarkupSafe',
        'itsdangerous': 'itsdangerous',
        'click': 'click',
        'cryptography': 'cryptography'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name.lower())
            print(f"✅ {import_name}: 已安装")
        except ImportError:
            print(f"❌ {import_name}: 未安装")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n⚠️  需要安装的包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def test_file_structure():
    """测试文件结构"""
    print("\n🔍 检查文件结构...")
    required_files = [
        'ssh_file_manager.py',
        'requirements.txt',
        'templates/index.html',
        'run_ssh_manager.bat',
        'run_ssh_manager.sh'
    ]
    
    import os
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: 存在")
        else:
            print(f"❌ {file_path}: 不存在")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  缺失文件: {', '.join(missing_files)}")
        return False
    
    return True

def test_ssh_connection_mock():
    """测试SSH连接类的基本功能（模拟）"""
    print("\n🔍 测试SSH管理器类...")
    try:
        # 导入SSH管理器类进行基本测试
        sys.path.append('.')
        from ssh_file_manager import SSHFileManager
        
        # 创建实例
        manager = SSHFileManager()
        print("✅ SSHFileManager类: 可以实例化")
        
        # 测试基本方法存在
        methods = ['connect', 'disconnect', 'list_directory', 'compare_directories', 'delete_file_or_dir']
        for method in methods:
            if hasattr(manager, method):
                print(f"✅ 方法 {method}: 存在")
            else:
                print(f"❌ 方法 {method}: 不存在")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ SSH管理器测试失败: {str(e)}")
        return False

def test_flask_app():
    """测试Flask应用是否可以导入"""
    print("\n🔍 测试Flask应用...")
    try:
        sys.path.append('.')
        from ssh_file_manager import app
        print("✅ Flask应用: 可以导入")
        
        # 测试路由是否注册
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/connect', '/disconnect', '/compare', '/delete', '/browse']
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ 路由 {route}: 已注册")
            else:
                print(f"❌ 路由 {route}: 未注册")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flask应用测试失败: {str(e)}")
        return False

def run_basic_server_test():
    """运行基本服务器测试"""
    print("\n🔍 测试服务器启动...")
    try:
        import threading
        import time
        import requests
        
        # 在新线程中启动服务器
        def start_server():
            sys.path.append('.')
            from ssh_file_manager import app
            app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # 等待服务器启动
        time.sleep(3)
        
        # 测试主页
        response = requests.get('http://127.0.0.1:5001/', timeout=5)
        if response.status_code == 200:
            print("✅ 服务器启动: 成功")
            print("✅ 主页访问: 正常")
            return True
        else:
            print(f"❌ 主页访问失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 服务器测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("🚀 SSH文件管理器 - 系统测试")
    print("=" * 50)
    
    tests = [
        ("Python版本检查", test_python_version),
        ("依赖包检查", test_dependencies),
        ("文件结构检查", test_file_structure),
        ("SSH管理器类测试", test_ssh_connection_mock),
        ("Flask应用测试", test_flask_app),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}发生异常: {str(e)}")
            results.append((test_name, False))
    
    # 显示测试结果摘要
    print("\n" + "=" * 50)
    print("📊 测试结果摘要")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！应用准备就绪。")
        print("💡 运行以下命令启动应用:")
        print("   Windows: run_ssh_manager.bat")
        print("   Linux/macOS: ./run_ssh_manager.sh")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查并修复问题。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 