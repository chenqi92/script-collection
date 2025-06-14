#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import subprocess
import shutil
import time
import re
import fnmatch
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import paramiko
from datetime import datetime
import stat
import difflib

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# 配置类
class Config:
    SECRET_KEY = 'your-secret-key-change-this-in-production'
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True
    SSH_TIMEOUT = 30
    SSH_BANNER_TIMEOUT = 60
    SSH_AUTH_TIMEOUT = 30
    MAX_FILE_SIZE_FOR_HASH = 100 * 1024 * 1024
    CHUNK_SIZE = 4096
    SSH_KEEPALIVE_INTERVAL = 30  # 保持连接活跃间隔
    SSH_MAX_RETRY = 3  # 最大重试次数

class TreeGenerator:
    """Python实现的目录树生成器"""
    
    def __init__(self):
        self.gitignore_rules = []
        self.tree_output = []
    
    def read_gitignore(self, directory):
        """读取.gitignore文件"""
        gitignore_file = os.path.join(directory, '.gitignore')
        self.gitignore_rules = []
        
        if os.path.exists(gitignore_file):
            try:
                with open(gitignore_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.gitignore_rules.append(line)
            except:
                pass
    
    def is_excluded(self, path, base_path):
        """检查文件或目录是否应该被排除"""
        if not self.gitignore_rules:
            return False
        
        relative_path = os.path.relpath(path, base_path)
        relative_path = relative_path.replace('\\', '/')
        
        for rule in self.gitignore_rules:
            if rule.startswith('!'):
                # 排除规则的例外
                continue
            
            # 简单的通配符匹配
            if fnmatch.fnmatch(relative_path, rule) or fnmatch.fnmatch(os.path.basename(path), rule):
                return True
            
            # 目录匹配
            if rule.endswith('/') and os.path.isdir(path):
                rule = rule.rstrip('/')
                if fnmatch.fnmatch(relative_path, rule) or fnmatch.fnmatch(os.path.basename(path), rule):
                    return True
        
        return False
    
    def generate_tree(self, directory, apply_gitignore=True, exclude_files=False, max_level=None):
        """生成目录树"""
        self.tree_output = []
        
        if not os.path.exists(directory):
            return False, f"目录不存在: {directory}"
        
        if not os.path.isdir(directory):
            return False, f"路径不是目录: {directory}"
        
        if apply_gitignore:
            self.read_gitignore(directory)
        else:
            self.gitignore_rules = []
        
        # 添加根目录名称
        self.tree_output.append(os.path.basename(directory) or directory)
        
        try:
            self._build_tree(directory, "", exclude_files, 0, max_level, directory)
            return True, '\n'.join(self.tree_output)
        except Exception as e:
            return False, f"生成目录树失败: {str(e)}"
    
    def _build_tree(self, directory, prefix, exclude_files, level, max_level, base_path):
        """递归构建目录树"""
        if max_level is not None and level >= max_level:
            return
        
        try:
            items = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                # 检查是否应该排除
                if self.is_excluded(item_path, base_path):
                    continue
                
                # 如果排除文件且当前项是文件，跳过
                if exclude_files and os.path.isfile(item_path):
                    continue
                
                items.append((item, item_path))
            
            # 排序：目录在前，文件在后
            items.sort(key=lambda x: (os.path.isfile(x[1]), x[0].lower()))
            
            for i, (item, item_path) in enumerate(items):
                is_last = i == len(items) - 1
                
                if is_last:
                    current_prefix = prefix + "└── " + item
                    new_prefix = prefix + "    "
                else:
                    current_prefix = prefix + "├── " + item
                    new_prefix = prefix + "│   "
                
                self.tree_output.append(current_prefix)
                
                # 如果是目录，递归处理
                if os.path.isdir(item_path):
                    self._build_tree(item_path, new_prefix, exclude_files, level + 1, max_level, base_path)
        
        except PermissionError:
            self.tree_output.append(prefix + "└── [权限拒绝]")
        except Exception as e:
            self.tree_output.append(prefix + f"└── [错误: {str(e)}]")

class RemoteTreeGenerator:
    """远程SSH目录树生成器"""
    
    def __init__(self, sftp, ssh):
        self.sftp = sftp
        self.ssh = ssh
        self.tree_output = []
    
    def generate_tree(self, directory, exclude_files=False, max_level=None):
        """生成远程目录树"""
        self.tree_output = []
        
        try:
            # 检查目录是否存在
            try:
                stat_info = self.sftp.stat(directory)
                if not stat.S_ISDIR(stat_info.st_mode):
                    return False, f"路径不是目录: {directory}"
            except:
                return False, f"目录不存在或无法访问: {directory}"
            
            # 添加根目录名称
            self.tree_output.append(os.path.basename(directory) or directory)
            
            self._build_tree(directory, "", exclude_files, 0, max_level)
            return True, '\n'.join(self.tree_output)
        except Exception as e:
            return False, f"生成目录树失败: {str(e)}"
    
    def _build_tree(self, directory, prefix, exclude_files, level, max_level):
        """递归构建目录树"""
        if max_level is not None and level >= max_level:
            return
        
        try:
            items = []
            for item in self.sftp.listdir_attr(directory):
                item_path = directory.rstrip('/') + '/' + item.filename
                
                # 如果排除文件且当前项是文件，跳过
                if exclude_files and not stat.S_ISDIR(item.st_mode):
                    continue
                
                items.append((item.filename, item_path, stat.S_ISDIR(item.st_mode)))
            
            # 排序：目录在前，文件在后
            items.sort(key=lambda x: (not x[2], x[0].lower()))
            
            for i, (name, path, is_dir) in enumerate(items):
                is_last = i == len(items) - 1
                
                if is_last:
                    current_prefix = prefix + "└── " + name
                    new_prefix = prefix + "    "
                else:
                    current_prefix = prefix + "├── " + name
                    new_prefix = prefix + "│   "
                
                self.tree_output.append(current_prefix)
                
                # 如果是目录，递归处理
                if is_dir:
                    self._build_tree(path, new_prefix, exclude_files, level + 1, max_level)
        
        except Exception as e:
            self.tree_output.append(prefix + f"└── [错误: {str(e)}]")

class RemoteEmptyDirCleaner:
    """远程SSH空目录清理器"""
    
    def __init__(self, sftp, ssh):
        self.sftp = sftp
        self.ssh = ssh
        self.removed_dirs = []
    
    def clean_empty_directories(self, directory):
        """清理远程空目录"""
        try:
            # 检查目录是否存在
            try:
                stat_info = self.sftp.stat(directory)
                if not stat.S_ISDIR(stat_info.st_mode):
                    return False, f"路径不是目录: {directory}", []
            except:
                return False, f"目录不存在或无法访问: {directory}", []
            
            self.removed_dirs = []
            self._clean_recursive(directory)
            
            if self.removed_dirs:
                message = f"成功删除 {len(self.removed_dirs)} 个空目录:\n" + '\n'.join(self.removed_dirs)
                return True, message, self.removed_dirs
            else:
                return True, "没有找到空目录", []
        
        except Exception as e:
            return False, f"清理空目录失败: {str(e)}", []
    
    def _clean_recursive(self, directory):
        """递归清理空目录"""
        try:
            # 先处理子目录
            subdirs = []
            for item in self.sftp.listdir_attr(directory):
                item_path = directory.rstrip('/') + '/' + item.filename
                if stat.S_ISDIR(item.st_mode):
                    subdirs.append(item_path)
            
            # 递归清理子目录
            for subdir in subdirs:
                self._clean_recursive(subdir)
            
            # 检查当前目录是否为空
            if not self.sftp.listdir(directory):
                try:
                    self.sftp.rmdir(directory)
                    self.removed_dirs.append(directory)
                except Exception:
                    # 忽略无法删除的目录
                    pass
        
        except Exception:
            pass

class EmptyDirCleaner:
    """Python实现的空目录清理器"""
    
    def __init__(self):
        self.removed_dirs = []
    
    def clean_empty_directories(self, directory):
        """清理空目录"""
        if not os.path.exists(directory):
            return False, f"目录不存在: {directory}", []
        
        if not os.path.isdir(directory):
            return False, f"路径不是目录: {directory}", []
        
        self.removed_dirs = []
        
        try:
            self._clean_recursive(directory)
            
            if self.removed_dirs:
                message = f"成功删除 {len(self.removed_dirs)} 个空目录:\n" + '\n'.join(self.removed_dirs)
                return True, message, self.removed_dirs
            else:
                return True, "没有找到空目录", []
        
        except Exception as e:
            return False, f"清理空目录失败: {str(e)}", []
    
    def _clean_recursive(self, directory):
        """递归清理空目录"""
        try:
            # 先处理子目录
            subdirs = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    subdirs.append(item_path)
            
            # 递归清理子目录
            for subdir in subdirs:
                self._clean_recursive(subdir)
            
            # 检查当前目录是否为空
            if not os.listdir(directory):
                try:
                    os.rmdir(directory)
                    self.removed_dirs.append(directory)
                except OSError as e:
                    # 忽略无法删除的目录
                    pass
        
        except PermissionError:
            pass
        except Exception:
            pass

class FileManager:
    def __init__(self):
        self.ssh = None
        self.sftp = None
        self.connected = False
        self.mode = 'local'  # 'local' 或 'remote'
        self.tree_generator = TreeGenerator()
        self.empty_dir_cleaner = EmptyDirCleaner()
        self.connection_info = {}  # 存储连接信息用于重连
        self.connection_history_file = 'connection_history.json'  # 连接历史文件
        
    def set_mode(self, mode):
        """设置工作模式：本地或远程"""
        if mode not in ['local', 'remote']:
            return False, "无效的模式"
        
        self.mode = mode
        if mode == 'local':
            self.disconnect()  # 切换到本地模式时断开SSH连接
        return True, f"已切换到{'本地' if mode == 'local' else '远程'}模式"
    
    def get_mode(self):
        """获取当前工作模式"""
        return self.mode
        
    def connect(self, hostname, username, password, port=22):
        """连接到SSH服务器"""
        if self.mode != 'remote':
            return False, "请先切换到远程模式"
            
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 设置更健壮的连接参数
            self.ssh.connect(
                hostname=hostname, 
                port=port, 
                username=username, 
                password=password, 
                timeout=Config.SSH_TIMEOUT,
                banner_timeout=Config.SSH_BANNER_TIMEOUT,
                auth_timeout=Config.SSH_AUTH_TIMEOUT,
                look_for_keys=False,
                allow_agent=False
            )
            
            # 设置保持连接活跃
            transport = self.ssh.get_transport()
            transport.set_keepalive(Config.SSH_KEEPALIVE_INTERVAL)
            
            self.sftp = self.ssh.open_sftp()
            self.connected = True
            
            # 存储连接信息用于重连
            self.connection_info = {
                'hostname': hostname,
                'username': username, 
                'password': password,
                'port': port,
                'auth_type': 'password'
            }
            
            # 添加到连接历史
            self.add_connection_to_history(hostname, username, port, 'password')
            
            return True, "连接成功"
        except Exception as e:
            self.connected = False
            return False, f"连接失败: {str(e)}"
    
    def disconnect(self):
        """断开SSH连接"""
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None
            if self.ssh:
                self.ssh.close()
                self.ssh = None
        except:
            pass
        finally:
            self.connected = False
            self.connection_info = {}
    
    def is_connected(self):
        """检查连接状态"""
        if self.mode == 'local':
            return True  # 本地模式总是"连接"的
            
        if not self.connected:
            return False
        if not self.ssh or not self.sftp:
            self.connected = False
            return False
        try:
            # 尝试执行一个简单的操作来验证连接
            transport = self.ssh.get_transport()
            if transport is None or not transport.is_active():
                self.connected = False
                return False
            
            # 使用轻量级命令测试连接
            stdin, stdout, stderr = self.ssh.exec_command('echo test', timeout=5)
            stdout.read()  # 读取输出确保命令执行完成
            return True
        except:
            self.connected = False
            return False
    
    def reconnect(self):
        """重新连接SSH服务器"""
        if not self.connection_info:
            return False, "没有可用的连接信息"
        
        self.disconnect()  # 先断开现有连接
        
        for attempt in range(Config.SSH_MAX_RETRY):
            try:
                success, message = self.connect(**self.connection_info)
                if success:
                    return True, f"重连成功（尝试 {attempt + 1}/{Config.SSH_MAX_RETRY}）"
                else:
                    if attempt < Config.SSH_MAX_RETRY - 1:
                        time.sleep(2)  # 等待2秒后重试
                    continue
            except Exception as e:
                if attempt < Config.SSH_MAX_RETRY - 1:
                    time.sleep(2)
                continue
        
        return False, f"重连失败（已尝试 {Config.SSH_MAX_RETRY} 次）"
    
    def ensure_connected(self):
        """确保连接可用，如果断开则尝试重连"""
        if self.mode == 'local':
            return True, "本地模式"
        
        if self.is_connected():
            return True, "连接正常"
        
        if self.connection_info:
            return self.reconnect()
        else:
            return False, "请先建立连接"
    
    def get_file_info(self, path):
        """获取文件或目录信息"""
        try:
            if self.mode == 'local':
                stat_info = os.stat(path)
                return {
                    'path': path,
                    'name': os.path.basename(path),
                    'size': stat_info.st_size,
                    'is_dir': os.path.isdir(path),
                    'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                stat_info = self.sftp.stat(path)
                return {
                    'path': path,
                    'name': os.path.basename(path),
                    'size': stat_info.st_size,
                    'is_dir': stat.S_ISDIR(stat_info.st_mode),
                    'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
        except:
            return None
    
    def list_directory(self, path):
        """列出目录内容"""
        try:
            items = []
            if self.mode == 'local':
                # Windows系统特殊处理
                if os.name == 'nt':
                    # 如果路径是根目录或空，显示所有磁盘驱动器
                    if path in ['/', '', '.', 'drives']:
                        import string
                        for letter in string.ascii_uppercase:
                            drive = f"{letter}:\\"
                            if os.path.exists(drive):
                                items.append({
                                    'path': drive.replace('\\', '/'),
                                    'name': f"{letter}: 驱动器",
                                    'size': 0,
                                    'is_dir': True,
                                    'modified': '系统驱动器'
                                })
                        return items
                    
                    # 标准化Windows路径
                    if path.startswith('/') and len(path) > 1:
                        # 将类Unix路径转换为Windows路径
                        path = path.replace('/', '\\')
                        if not path.endswith('\\') and len(path) == 2 and path[1] == ':':
                            path += '\\'
                
                # 正常目录列表
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    stat_info = os.stat(item_path)
                    
                    # 为Windows系统标准化路径显示
                    display_path = item_path
                    if os.name == 'nt':
                        display_path = item_path.replace('\\', '/')
                    
                    items.append({
                        'path': display_path,
                        'name': item,
                        'size': stat_info.st_size,
                        'is_dir': os.path.isdir(item_path),
                        'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            else:
                # 远程模式保持原逻辑
                for item in self.sftp.listdir_attr(path):
                    item_path = os.path.join(path, item.filename).replace('\\', '/')
                    items.append({
                        'path': item_path,
                        'name': item.filename,
                        'size': item.st_size,
                        'is_dir': stat.S_ISDIR(item.st_mode),
                        'modified': datetime.fromtimestamp(item.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            return items
        except Exception as e:
            return []
    
    def get_file_hash(self, filepath):
        """获取文件的MD5哈希值"""
        try:
            hash_md5 = hashlib.md5()
            if self.mode == 'local':
                with open(filepath, 'rb') as f:
                    for chunk in iter(lambda: f.read(Config.CHUNK_SIZE), b""):
                        hash_md5.update(chunk)
            else:
                with self.sftp.open(filepath, 'rb') as f:
                    for chunk in iter(lambda: f.read(Config.CHUNK_SIZE), b""):
                        hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
    
    def compare_directories(self, path1, path2, similarity_threshold=0.8):
        """比较两个目录，找出重复的文件和文件夹"""
        items1 = self.list_directory(path1)
        items2 = self.list_directory(path2)
        
        duplicates = []
        similar_items = []
        
        # 按名称和类型进行初步匹配
        for item1 in items1:
            for item2 in items2:
                # 完全匹配检查
                if item1['name'] == item2['name'] and item1['is_dir'] == item2['is_dir']:
                    # 如果是文件，进一步比较大小和哈希
                    if not item1['is_dir']:
                        if item1['size'] == item2['size']:
                            hash1 = self.get_file_hash(item1['path'])
                            hash2 = self.get_file_hash(item2['path'])
                            if hash1 and hash2 and hash1 == hash2:
                                duplicates.append({
                                    'name': item1['name'],
                                    'type': 'file',
                                    'match_type': 'exact',
                                    'path1': item1['path'],
                                    'path2': item2['path'],
                                    'size': item1['size'],
                                    'modified1': item1['modified'],
                                    'modified2': item2['modified'],
                                    'similarity': 1.0
                                })
                    else:
                        # 如果是目录，直接认为是重复的
                        duplicates.append({
                            'name': item1['name'],
                            'type': 'directory',
                            'match_type': 'exact',
                            'path1': item1['path'],
                            'path2': item2['path'],
                            'size': '-',
                            'modified1': item1['modified'],
                            'modified2': item2['modified'],
                            'similarity': 1.0
                        })
                
                # 模糊匹配检查（仅当不是完全匹配时）
                elif item1['is_dir'] == item2['is_dir']:
                    similarity = self.calculate_name_similarity(item1['name'], item2['name'])
                    if similarity >= similarity_threshold:
                        # 如果是文件，还要检查大小是否相近
                        if not item1['is_dir']:
                            size_similarity = self.calculate_size_similarity(item1['size'], item2['size'])
                            if size_similarity >= 0.9:  # 大小相似度阈值
                                similar_items.append({
                                    'name': f"{item1['name']} ≈ {item2['name']}",
                                    'type': 'file',
                                    'match_type': 'similar',
                                    'path1': item1['path'],
                                    'path2': item2['path'],
                                    'size': f"{item1['size']} / {item2['size']}",
                                    'modified1': item1['modified'],
                                    'modified2': item2['modified'],
                                    'similarity': similarity
                                })
                        else:
                            # 目录只需要名称相似
                            similar_items.append({
                                'name': f"{item1['name']} ≈ {item2['name']}",
                                'type': 'directory',
                                'match_type': 'similar',
                                'path1': item1['path'],
                                'path2': item2['path'],
                                'size': '-',
                                'modified1': item1['modified'],
                                'modified2': item2['modified'],
                                'similarity': similarity
                            })
        
        return duplicates + similar_items
    
    def calculate_name_similarity(self, name1, name2):
        """计算两个文件名的相似度"""
        # 移除扩展名进行比较
        base1 = os.path.splitext(name1)[0].lower()
        base2 = os.path.splitext(name2)[0].lower()
        
        # 使用difflib计算相似度
        similarity = difflib.SequenceMatcher(None, base1, base2).ratio()
        
        # 检查是否有共同的数字模式（如版本号）
        digits1 = re.findall(r'\d+', base1)
        digits2 = re.findall(r'\d+', base2)
        
        # 如果有数字且数字不同，降低相似度
        if digits1 and digits2 and digits1 != digits2:
            similarity *= 0.8
        
        return similarity
    
    def calculate_size_similarity(self, size1, size2):
        """计算两个文件大小的相似度"""
        if size1 == 0 and size2 == 0:
            return 1.0
        if size1 == 0 or size2 == 0:
            return 0.0
        
        larger = max(size1, size2)
        smaller = min(size1, size2)
        return smaller / larger
    
    def delete_file_or_dir(self, path):
        """删除文件或目录"""
        try:
            if self.mode == 'local':
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            else:
                file_info = self.get_file_info(path)
                if file_info and file_info['is_dir']:
                    self._remove_dir_recursive(path)
                else:
                    self.sftp.remove(path)
            return True, "删除成功"
        except Exception as e:
            return False, f"删除失败: {str(e)}"
    
    def _remove_dir_recursive(self, path):
        """递归删除目录（仅用于远程模式）"""
        try:
            for item in self.sftp.listdir_attr(path):
                item_path = os.path.join(path, item.filename).replace('\\', '/')
                if stat.S_ISDIR(item.st_mode):
                    self._remove_dir_recursive(item_path)
                else:
                    self.sftp.remove(item_path)
            self.sftp.rmdir(path)
        except Exception as e:
            raise e
    
    def run_tree_command(self, directory=None, apply_gitignore=True, exclude_files=False, max_level=None):
        """运行tree命令生成目录树"""
        if directory is None:
            directory = os.getcwd() if self.mode == 'local' else '/'
        
        # 确保连接可用
        connected, message = self.ensure_connected()
        if not connected:
            return False, message
        
        if self.mode == 'local':
            return self.tree_generator.generate_tree(directory, apply_gitignore, exclude_files, max_level)
        else:
            # 远程模式不支持gitignore，因为需要额外的文件传输
            remote_tree_gen = RemoteTreeGenerator(self.sftp, self.ssh)
            return remote_tree_gen.generate_tree(directory, exclude_files, max_level)
    
    def clean_empty_directories(self, directory=None):
        """清理空目录"""
        if directory is None:
            directory = os.getcwd() if self.mode == 'local' else '/'
        
        # 确保连接可用
        connected, message = self.ensure_connected()
        if not connected:
            return False, message, []
        
        if self.mode == 'local':
            return self.empty_dir_cleaner.clean_empty_directories(directory)
        else:
            remote_cleaner = RemoteEmptyDirCleaner(self.sftp, self.ssh)
            return remote_cleaner.clean_empty_directories(directory)
    
    def restore_directories(self, directories):
        """恢复已删除的目录"""
        if not directories:
            return False, "没有目录需要恢复"
        
        # 确保连接可用
        connected, message = self.ensure_connected()
        if not connected:
            return False, message
        
        restored_count = 0
        failed_dirs = []
        
        # 按路径长度排序，先创建父目录
        sorted_dirs = sorted(directories, key=len)
        
        for dir_path in sorted_dirs:
            try:
                if self.mode == 'local':
                    os.makedirs(dir_path, exist_ok=True)
                else:
                    # 远程模式下创建目录
                    try:
                        self.sftp.mkdir(dir_path)
                    except IOError:
                        # 目录可能已存在或父目录不存在，尝试递归创建
                        self._create_remote_directory(dir_path)
                
                restored_count += 1
            except Exception as e:
                failed_dirs.append(f"{dir_path}: {str(e)}")
        
        if failed_dirs:
            return False, f"部分恢复失败：成功 {restored_count} 个，失败 {len(failed_dirs)} 个。失败详情：{'; '.join(failed_dirs)}"
        else:
            return True, f"成功恢复 {restored_count} 个目录"
    
    def _create_remote_directory(self, path):
        """递归创建远程目录"""
        path = path.rstrip('/')
        if not path or path == '/':
            return
        
        try:
            self.sftp.mkdir(path)
        except IOError:
            # 父目录不存在，递归创建
            parent = '/'.join(path.split('/')[:-1])
            if parent and parent != path:
                self._create_remote_directory(parent)
                self.sftp.mkdir(path)
    
    def batch_rename(self, directory, rename_type, pattern=None, replacement=None, custom_text=None, sequence_position='prefix'):
        """批量重命名文件和文件夹"""
        if not directory:
            return False, "请指定目录路径", []
        
        # 确保连接可用
        connected, message = self.ensure_connected()
        if not connected:
            return False, message, []
        
        try:
            items = self.list_directory(directory)
            results = []
            success_count = 0
            failed_count = 0
            
            # 对文件进行排序，确保重命名顺序一致
            items.sort(key=lambda x: (x['is_dir'], x['name'].lower()))
            
            # 为序号功能准备计数器
            sequence_counter = 1
            
            for item in items:
                old_name = item['name']
                old_path = item['path']
                
                # 跳过 . 和 .. 目录
                if old_name in ['.', '..']:
                    continue
                
                try:
                    new_name = self._apply_rename_rule(old_name, rename_type, pattern, replacement, custom_text, sequence_counter, sequence_position)
                    
                    if new_name and new_name != old_name:
                        # 构建新路径
                        if self.mode == 'local':
                            new_path = os.path.join(directory, new_name)
                            os.rename(old_path, new_path)
                        else:
                            new_path = os.path.join(directory, new_name).replace('\\', '/')
                            self.sftp.rename(old_path, new_path)
                        
                        results.append({
                            'success': True,
                            'old_name': old_name,
                            'new_name': new_name,
                            'message': '重命名成功'
                        })
                        success_count += 1
                        sequence_counter += 1
                    else:
                        results.append({
                            'success': True,
                            'old_name': old_name, 
                            'new_name': old_name,
                            'message': '无需重命名'
                        })
                
                except Exception as e:
                    results.append({
                        'success': False,
                        'old_name': old_name,
                        'new_name': old_name,
                        'message': f'重命名失败: {str(e)}'
                    })
                    failed_count += 1
            
            overall_success = failed_count == 0
            summary_message = f'批量重命名完成：成功 {success_count} 个，失败 {failed_count} 个'
            
            return overall_success, summary_message, results
            
        except Exception as e:
            return False, f"批量重命名操作失败: {str(e)}", []
    
    def _apply_rename_rule(self, filename, rename_type, pattern=None, replacement=None, custom_text=None, sequence_num=1, sequence_position='prefix'):
        """应用重命名规则"""
        original_name = filename
        name, ext = os.path.splitext(filename)
        
        try:
            if rename_type == 'remove_number_prefix':
                # 移除数字前缀：例如 "01 文件.txt" -> "文件.txt"
                new_name = re.sub(r'^\d+\s*[-_]?\s*', '', name)
                return new_name + ext
            
            elif rename_type == 'add_sequence_prefix':
                # 添加序号前缀：例如 "文件.txt" -> "001_文件.txt"
                return f"{sequence_num:03d}_{filename}"
            
            elif rename_type == 'add_sequence_suffix':
                # 添加序号后缀：例如 "文件.txt" -> "文件_001.txt"
                return f"{name}_{sequence_num:03d}{ext}"
            
            elif rename_type == 'add_custom_prefix':
                # 添加自定义前缀：例如 "文件.txt" -> "前缀_文件.txt"
                if custom_text:
                    return f"{custom_text}_{filename}"
                return filename
            
            elif rename_type == 'add_custom_suffix':
                # 添加自定义后缀：例如 "文件.txt" -> "文件_后缀.txt"
                if custom_text:
                    return f"{name}_{custom_text}{ext}"
                return filename
            
            elif rename_type == 'remove_special_chars':
                # 移除特殊字符：保留字母、数字、中文、下划线、连字符和点
                clean_name = re.sub(r'[^\w\u4e00-\u9fff.-]', '', name)
                return clean_name + ext
            
            elif rename_type == 'to_lowercase':
                # 转为小写
                return filename.lower()
            
            elif rename_type == 'to_uppercase':
                # 转为大写
                return filename.upper()
            
            elif rename_type == 'space_to_underscore':
                # 空格替换为下划线
                return filename.replace(' ', '_')
            
            elif rename_type == 'underscore_to_space':
                # 下划线替换为空格
                return filename.replace('_', ' ')
            
            elif rename_type == 'regex':
                # 正则表达式替换
                if pattern:
                    repl = replacement if replacement is not None else ''
                    return re.sub(pattern, repl, filename)
                return filename
            
            elif rename_type == 'date_prefix':
                # 添加日期前缀：例如 "文件.txt" -> "20231201_文件.txt"
                from datetime import datetime
                date_str = datetime.now().strftime('%Y%m%d')
                return f"{date_str}_{filename}"
            
            elif rename_type == 'capitalize_words':
                # 首字母大写：例如 "hello world.txt" -> "Hello World.txt"
                capitalized_name = ' '.join(word.capitalize() for word in name.split())
                return capitalized_name + ext
            
            else:
                return filename
                
        except Exception as e:
            # 如果重命名规则应用失败，返回原文件名
            return original_name
    
    def read_file_content(self, file_path):
        """读取文件内容"""
        # 确保连接可用
        connected, message = self.ensure_connected()
        if not connected:
            return False, message, ""
        
        try:
            if self.mode == 'local':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                with self.sftp.open(file_path, 'r') as f:
                    content = f.read().decode('utf-8')
            
            return True, "读取成功", content
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                if self.mode == 'local':
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                else:
                    with self.sftp.open(file_path, 'r') as f:
                        content = f.read().decode('gbk')
                return True, "读取成功", content
            except:
                return False, "文件编码不支持，无法读取", ""
        except Exception as e:
            return False, f"读取文件失败: {str(e)}", ""
    
    def write_file_content(self, file_path, content):
        """写入文件内容"""
        # 确保连接可用
        connected, message = self.ensure_connected()
        if not connected:
            return False, message
        
        try:
            if self.mode == 'local':
                # 创建备份
                backup_path = file_path + '.backup'
                if os.path.exists(file_path):
                    shutil.copy2(file_path, backup_path)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # 远程模式下的备份处理
                backup_path = file_path + '.backup'
                try:
                    # 创建备份
                    with self.sftp.open(file_path, 'r') as src:
                        with self.sftp.open(backup_path, 'w') as dst:
                            dst.write(src.read())
                except:
                    pass  # 如果备份失败，继续执行写入操作
                
                with self.sftp.open(file_path, 'w') as f:
                    f.write(content.encode('utf-8'))
            
            return True, "保存成功"
        except Exception as e:
            return False, f"保存文件失败: {str(e)}"
    
    def organize_directory(self, directory, organize_type):
        """目录整理功能"""
        if not directory:
            return False, "请指定目录路径", []
        
        # 确保连接可用
        connected, message = self.ensure_connected()
        if not connected:
            return False, message, []
        
        try:
            if organize_type == 'create_folders_for_files':
                return self._create_folders_for_files(directory)
            elif organize_type == 'remove_empty_dirs':
                success, result, cleaned_dirs = self.clean_empty_directories(directory)
                results = []
                for dir_path in cleaned_dirs:
                    results.append({
                        'success': True,
                        'dir_name': dir_path,
                        'message': '空目录已删除'
                    })
                return success, result, results
            else:
                return False, "不支持的整理类型", []
        
        except Exception as e:
            return False, f"目录整理失败: {str(e)}", []
    
    def _create_folders_for_files(self, directory):
        """为文件创建同名文件夹并移入"""
        try:
            items = self.list_directory(directory)
            results = []
            success_count = 0
            failed_count = 0
            
            # 只处理文件，跳过目录
            files = [item for item in items if not item['is_dir']]
            
            for file_item in files:
                filename = file_item['name']
                file_path = file_item['path']
                
                # 获取不含扩展名的文件名作为文件夹名
                folder_name = os.path.splitext(filename)[0]
                
                if self.mode == 'local':
                    folder_path = os.path.join(directory, folder_name)
                    new_file_path = os.path.join(folder_path, filename)
                else:
                    folder_path = os.path.join(directory, folder_name).replace('\\', '/')
                    new_file_path = os.path.join(folder_path, filename).replace('\\', '/')
                
                try:
                    # 创建文件夹
                    if self.mode == 'local':
                        os.makedirs(folder_path, exist_ok=True)
                        # 移动文件
                        shutil.move(file_path, new_file_path)
                    else:
                        # 远程模式
                        try:
                            self.sftp.mkdir(folder_path)
                        except IOError:
                            # 文件夹可能已存在
                            pass
                        # 移动文件
                        self.sftp.rename(file_path, new_file_path)
                    
                    results.append({
                        'success': True,
                        'filename': filename,
                        'folder_name': folder_name,
                        'message': '已创建文件夹并移入文件'
                    })
                    success_count += 1
                    
                except Exception as e:
                    results.append({
                        'success': False,
                        'filename': filename,
                        'folder_name': folder_name,
                        'message': f'操作失败: {str(e)}'
                    })
                    failed_count += 1
            
            overall_success = failed_count == 0
            summary_message = f'文件整理完成：成功 {success_count} 个，失败 {failed_count} 个'
            
            return overall_success, summary_message, results
            
        except Exception as e:
            return False, f"创建文件夹失败: {str(e)}", []
    
    def load_connection_history(self):
        """加载连接历史"""
        try:
            if os.path.exists(self.connection_history_file):
                with open(self.connection_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"加载连接历史失败: {e}")
            return []
    
    def save_connection_history(self, connections):
        """保存连接历史"""
        try:
            with open(self.connection_history_file, 'w', encoding='utf-8') as f:
                json.dump(connections, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存连接历史失败: {e}")
            return False
    
    def add_connection_to_history(self, hostname, username, port=22, auth_type='password', description=''):
        """添加连接到历史记录"""
        connections = self.load_connection_history()
        
        # 检查是否已存在相同连接
        connection_id = f"{username}@{hostname}:{port}"
        existing_index = -1
        for i, conn in enumerate(connections):
            if conn.get('id') == connection_id:
                existing_index = i
                break
        
        connection_data = {
            'id': connection_id,
            'hostname': hostname,
            'username': username,
            'port': port,
            'auth_type': auth_type,  # 'password' 或 'key'
            'description': description,
            'last_connected': datetime.now().isoformat(),
            'connect_count': 1
        }
        
        if existing_index >= 0:
            # 更新现有连接
            connections[existing_index]['last_connected'] = connection_data['last_connected']
            connections[existing_index]['connect_count'] = connections[existing_index].get('connect_count', 0) + 1
            connections[existing_index]['auth_type'] = auth_type
            connections[existing_index]['description'] = description
        else:
            # 添加新连接到开头
            connections.insert(0, connection_data)
        
        # 限制历史记录数量
        if len(connections) > 20:
            connections = connections[:20]
        
        self.save_connection_history(connections)
        return True
    
    def remove_connection_from_history(self, connection_id):
        """从历史记录中移除连接"""
        connections = self.load_connection_history()
        connections = [conn for conn in connections if conn.get('id') != connection_id]
        self.save_connection_history(connections)
        return True
    
    def connect_with_key(self, hostname, username, private_key_path, port=22, passphrase=None):
        """使用SSH私钥连接到服务器"""
        if self.mode != 'remote':
            return False, "请先切换到远程模式"
            
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 加载私钥
            try:
                if passphrase:
                    key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)
                else:
                    key = paramiko.RSAKey.from_private_key_file(private_key_path)
            except paramiko.PasswordRequiredException:
                return False, "私钥需要密码"
            except Exception as e:
                # 尝试其他密钥格式
                try:
                    if passphrase:
                        key = paramiko.Ed25519Key.from_private_key_file(private_key_path, password=passphrase)
                    else:
                        key = paramiko.Ed25519Key.from_private_key_file(private_key_path)
                except:
                    try:
                        if passphrase:
                            key = paramiko.ECDSAKey.from_private_key_file(private_key_path, password=passphrase)
                        else:
                            key = paramiko.ECDSAKey.from_private_key_file(private_key_path)
                    except:
                        return False, f"无法加载私钥文件: {str(e)}"
            
            # 连接服务器
            self.ssh.connect(
                hostname=hostname,
                port=port,
                username=username,
                pkey=key,
                timeout=Config.SSH_TIMEOUT,
                banner_timeout=Config.SSH_BANNER_TIMEOUT,
                auth_timeout=Config.SSH_AUTH_TIMEOUT,
                look_for_keys=False,
                allow_agent=False
            )
            
            # 设置保持连接活跃
            transport = self.ssh.get_transport()
            transport.set_keepalive(Config.SSH_KEEPALIVE_INTERVAL)
            
            self.sftp = self.ssh.open_sftp()
            self.connected = True
            
            # 存储连接信息用于重连
            self.connection_info = {
                'hostname': hostname,
                'username': username,
                'private_key_path': private_key_path,
                'passphrase': passphrase,
                'port': port,
                'auth_type': 'key'
            }
            
            # 添加到连接历史
            self.add_connection_to_history(hostname, username, port, 'key')
            
            return True, "连接成功"
        except Exception as e:
            self.connected = False
            return False, f"连接失败: {str(e)}"

# 全局文件管理器实例
file_manager = FileManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_mode', methods=['POST'])
def set_mode():
    """设置工作模式"""
    mode = request.json.get('mode')
    success, message = file_manager.set_mode(mode)
    return jsonify({
        'success': success,
        'message': message,
        'current_mode': file_manager.get_mode()
    })

@app.route('/get_mode')
def get_mode():
    """获取当前工作模式"""
    return jsonify({
        'mode': file_manager.get_mode(),
        'connected': file_manager.is_connected()
    })

@app.route('/connect', methods=['POST'])
def connect():
    """连接SSH服务器"""
    hostname = request.json.get('hostname')
    username = request.json.get('username') 
    password = request.json.get('password')
    port = request.json.get('port', 22)
    
    success, message = file_manager.connect(hostname, username, password, port)
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """断开SSH连接"""
    file_manager.disconnect()
    return jsonify({
        'success': True,
        'message': '已断开连接'
    })

@app.route('/connection_status')
def connection_status():
    """获取连接状态"""
    return jsonify({
        'connected': file_manager.is_connected(),
        'mode': file_manager.get_mode()
    })

@app.route('/compare', methods=['POST'])
def compare():
    """比较两个目录"""
    # 确保连接可用
    connected, conn_message = file_manager.ensure_connected()
    if not connected:
        return jsonify({
            'success': False,
            'message': f'连接检查失败: {conn_message}'
        })
    
    path1 = request.json.get('path1')
    path2 = request.json.get('path2')
    threshold = float(request.json.get('threshold', 0.8))
    
    if not path1 or not path2:
        return jsonify({
            'success': False,
            'message': '请输入两个有效的路径'
        })
    
    try:
        duplicates = file_manager.compare_directories(path1, path2, threshold)
        return jsonify({
            'success': True,
            'duplicates': duplicates,
            'message': f'找到 {len(duplicates)} 个重复或相似项'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'比较失败: {str(e)}'
        })

@app.route('/delete', methods=['POST'])
def delete():
    """删除文件或目录"""
    if not file_manager.is_connected():
        return jsonify({
            'success': False,
            'message': f'请先{"连接SSH服务器" if file_manager.get_mode() == "remote" else "确保本地模式正常"}'
        })
    
    path = request.json.get('path')
    if not path:
        return jsonify({
            'success': False,
            'message': '请指定要删除的路径'
        })
    
    success, message = file_manager.delete_file_or_dir(path)
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/batch_delete', methods=['POST'])
def batch_delete():
    """批量删除文件"""
    if not file_manager.is_connected():
        return jsonify({
            'success': False,
            'message': f'请先{"连接SSH服务器" if file_manager.get_mode() == "remote" else "确保本地模式正常"}'
        })
    
    paths = request.json.get('paths', [])
    if not paths:
        return jsonify({
            'success': False,
            'message': '请选择要删除的文件'
        })
    
    results = []
    success_count = 0
    failed_count = 0
    
    for path in paths:
        success, message = file_manager.delete_file_or_dir(path)
        results.append({
            'path': path,
            'success': success,
            'message': message
        })
        
        if success:
            success_count += 1
        else:
            failed_count += 1
    
    overall_success = failed_count == 0
    summary_message = f'批量删除完成：成功 {success_count} 个，失败 {failed_count} 个'
    
    return jsonify({
        'success': overall_success,
        'message': summary_message,
        'results': results,
        'summary': {
            'success': success_count,
            'failed': failed_count,
            'total': len(paths)
        }
    })

@app.route('/browse')
def browse():
    """浏览目录"""
    if not file_manager.is_connected():
        return jsonify({
            'success': False,
            'message': f'请先{"连接SSH服务器" if file_manager.get_mode() == "remote" else "确保本地模式正常"}'
        })
    
    path = request.args.get('path', '/' if file_manager.get_mode() == 'remote' else os.getcwd())
    
    try:
        items = file_manager.list_directory(path)
        
        # 获取标准化的当前路径
        if file_manager.get_mode() == 'local':
            # 对于Windows系统，标准化路径显示
            if os.name == 'nt':
                current_path = os.path.abspath(path).replace('\\', '/')
            else:
                current_path = os.path.abspath(path)
        else:
            current_path = path
            
        return jsonify({
            'success': True,
            'items': items,
            'current_path': current_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'浏览目录失败: {str(e)}'
        })

@app.route('/tree', methods=['POST'])
def tree():
    """生成目录树"""
    directory = request.json.get('directory')
    apply_gitignore = request.json.get('apply_gitignore', True)
    exclude_files = request.json.get('exclude_files', False)
    max_level = request.json.get('max_level')
    
    if not directory:
        return jsonify({
            'success': False,
            'message': '请先选择一个目录'
        })
    
    # 确保连接可用
    connected, conn_message = file_manager.ensure_connected()
    if not connected:
        return jsonify({
            'success': False,
            'message': f'连接检查失败: {conn_message}'
        })
    
    success, result = file_manager.run_tree_command(directory, apply_gitignore, exclude_files, max_level)
    return jsonify({
        'success': success,
        'result': result
    })

@app.route('/clean_empty_dirs', methods=['POST'])
def clean_empty_dirs():
    """清理空目录"""
    directory = request.json.get('directory')
    
    if not directory:
        return jsonify({
            'success': False,
            'message': '请先选择一个目录',
            'cleaned_directories': []
        })
    
    # 确保连接可用
    connected, conn_message = file_manager.ensure_connected()
    if not connected:
        return jsonify({
            'success': False,
            'message': f'连接检查失败: {conn_message}',
            'cleaned_directories': []
        })
    
    success, result, cleaned_dirs = file_manager.clean_empty_directories(directory)
    return jsonify({
        'success': success,
        'result': result,
        'cleaned_directories': cleaned_dirs
    })

@app.route('/restore_directories', methods=['POST'])
def restore_directories():
    """恢复已删除的目录"""
    directories = request.json.get('directories', [])
    mode = request.json.get('mode', file_manager.get_mode())
    
    if not directories:
        return jsonify({
            'success': False,
            'message': '没有目录需要恢复'
        })
    
    # 设置模式（如果需要）
    if mode != file_manager.get_mode():
        file_manager.set_mode(mode)
    
    success, message = file_manager.restore_directories(directories)
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/batch_rename', methods=['POST'])
def batch_rename():
    """批量重命名文件"""
    if not file_manager.is_connected():
        return jsonify({
            'success': False,
            'message': f'请先{"连接SSH服务器" if file_manager.get_mode() == "remote" else "确保本地模式正常"}'
        })
    
    directory = request.json.get('path')
    rename_type = request.json.get('rename_type')
    pattern = request.json.get('pattern')
    replacement = request.json.get('replacement')
    custom_text = request.json.get('custom_text')
    sequence_position = request.json.get('sequence_position', 'prefix')
    
    if not directory:
        return jsonify({
            'success': False,
            'message': '请指定目录路径'
        })
    
    if not rename_type:
        return jsonify({
            'success': False,
            'message': '请选择重命名类型'
        })
    
    success, message, results = file_manager.batch_rename(
        directory, rename_type, pattern, replacement, custom_text, sequence_position
    )
    
    return jsonify({
        'success': success,
        'message': message,
        'results': results
    })

@app.route('/organize_directory', methods=['POST'])
def organize_directory():
    """目录整理"""
    if not file_manager.is_connected():
        return jsonify({
            'success': False,
            'message': f'请先{"连接SSH服务器" if file_manager.get_mode() == "remote" else "确保本地模式正常"}'
        })
    
    directory = request.json.get('path')
    organize_type = request.json.get('organize_type')
    
    if not directory:
        return jsonify({
            'success': False,
            'message': '请指定目录路径'
        })
    
    if not organize_type:
        return jsonify({
            'success': False,
            'message': '请选择整理类型'
        })
    
    success, message, results = file_manager.organize_directory(directory, organize_type)
    
    return jsonify({
        'success': success,
        'message': message,
        'results': results
    })

@app.route('/read_file', methods=['POST'])
def read_file():
    """读取文件内容"""
    if not file_manager.is_connected():
        return jsonify({
            'success': False,
            'message': f'请先{"连接SSH服务器" if file_manager.get_mode() == "remote" else "确保本地模式正常"}'
        })
    
    file_path = request.json.get('file_path')
    
    if not file_path:
        return jsonify({
            'success': False,
            'message': '请指定文件路径'
        })
    
    success, message, content = file_manager.read_file_content(file_path)
    
    return jsonify({
        'success': success,
        'message': message,
        'content': content
    })

@app.route('/write_file', methods=['POST'])
def write_file():
    """写入文件内容"""
    if not file_manager.is_connected():
        return jsonify({
            'success': False,
            'message': f'请先{"连接SSH服务器" if file_manager.get_mode() == "remote" else "确保本地模式正常"}'
        })
    
    file_path = request.json.get('file_path')
    content = request.json.get('content')
    
    if not file_path:
        return jsonify({
            'success': False,
            'message': '请指定文件路径'
        })
    
    if content is None:
        return jsonify({
            'success': False,
            'message': '请提供文件内容'
        })
    
    success, message = file_manager.write_file_content(file_path, content)
    
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/connection_history')
def get_connection_history():
    """获取连接历史"""
    try:
        connections = file_manager.load_connection_history()
        return jsonify({
            'success': True,
            'connections': connections
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取连接历史失败: {str(e)}',
            'connections': []
        })

@app.route('/remove_connection_history', methods=['POST'])
def remove_connection_history():
    """移除连接历史记录"""
    connection_id = request.json.get('connection_id')
    
    if not connection_id:
        return jsonify({
            'success': False,
            'message': '请提供连接ID'
        })
    
    try:
        file_manager.remove_connection_from_history(connection_id)
        return jsonify({
            'success': True,
            'message': '连接历史已移除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'移除连接历史失败: {str(e)}'
        })

@app.route('/connect_with_key', methods=['POST'])
def connect_with_key():
    """使用SSH密钥连接服务器"""
    hostname = request.json.get('hostname')
    username = request.json.get('username')
    private_key_path = request.json.get('private_key_path')
    port = request.json.get('port', 22)
    passphrase = request.json.get('passphrase')
    
    if not all([hostname, username, private_key_path]):
        return jsonify({
            'success': False,
            'message': '请提供主机名、用户名和私钥路径'
        })
    
    success, message = file_manager.connect_with_key(hostname, username, private_key_path, port, passphrase)
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/update_connection_description', methods=['POST'])
def update_connection_description():
    """更新连接描述"""
    connection_id = request.json.get('connection_id')
    description = request.json.get('description', '')
    
    if not connection_id:
        return jsonify({
            'success': False,
            'message': '请提供连接ID'
        })
    
    try:
        connections = file_manager.load_connection_history()
        for conn in connections:
            if conn.get('id') == connection_id:
                conn['description'] = description
                break
        
        file_manager.save_connection_history(connections)
        return jsonify({
            'success': True,
            'message': '连接描述已更新'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新连接描述失败: {str(e)}'
        })

if __name__ == '__main__':
    print("启动文件管理器服务器...")
    print("访问 http://localhost:5000 开始使用")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG) 