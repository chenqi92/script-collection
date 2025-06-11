#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import subprocess
import shutil
import time
import re
import fnmatch
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
                'port': port
            }
            
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
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    stat_info = os.stat(item_path)
                    items.append({
                        'path': item_path,
                        'name': item,
                        'size': stat_info.st_size,
                        'is_dir': os.path.isdir(item_path),
                        'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            else:
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
        return jsonify({
            'success': True,
            'items': items,
            'current_path': path
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

if __name__ == '__main__':
    print("启动文件管理器服务器...")
    print("访问 http://localhost:5000 开始使用")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG) 