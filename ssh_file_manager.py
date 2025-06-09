#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import paramiko
from datetime import datetime
import stat
import difflib
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

class SSHFileManager:
    def __init__(self):
        self.ssh = None
        self.sftp = None
        self.connected = False
        
    def connect(self, hostname, username, password, port=22):
        """连接到SSH服务器"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname, port=port, username=username, password=password, timeout=10)
            self.sftp = self.ssh.open_sftp()
            self.connected = True
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def disconnect(self):
        """断开SSH连接"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        self.connected = False
    
    def is_connected(self):
        """检查SSH连接状态"""
        if not self.connected:
            return False
        if not self.ssh or not self.sftp:
            self.connected = False
            return False
        try:
            # 尝试执行一个简单的操作来验证连接
            self.ssh.exec_command('echo test', timeout=5)
            return True
        except:
            self.connected = False
            return False
    
    def get_file_info(self, path):
        """获取文件或目录信息"""
        try:
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
            with self.sftp.open(filepath, 'rb') as f:
                hash_md5 = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
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
            stat_info = self.sftp.stat(path)
            if stat.S_ISDIR(stat_info.st_mode):
                # 递归删除目录
                self._remove_dir_recursive(path)
            else:
                # 删除文件
                self.sftp.remove(path)
            return True, f"成功删除: {path}"
        except Exception as e:
            return False, f"删除失败: {str(e)}"
    
    def _remove_dir_recursive(self, path):
        """递归删除目录"""
        for item in self.sftp.listdir_attr(path):
            item_path = os.path.join(path, item.filename).replace('\\', '/')
            if stat.S_ISDIR(item.st_mode):
                self._remove_dir_recursive(item_path)
            else:
                self.sftp.remove(item_path)
        self.sftp.rmdir(path)

    def batch_rename(self, path, rename_type, pattern=None, replacement=None):
        """批量重命名文件和文件夹"""
        try:
            items = self.list_directory(path)
            results = []
            success_count = 0
            failed_count = 0

            for item in items:
                old_name = item['name']
                new_name = None
                
                if rename_type == 'regex':
                    # 正则表达式重命名
                    if pattern and replacement is not None:
                        new_name = re.sub(pattern, replacement, old_name)
                elif rename_type == 'remove_number_prefix':
                    # 移除数字前缀和空格
                    new_name = re.sub(r'^\d+\s*', '', old_name)
                elif rename_type == 'add_sequence':
                    # 添加序号前缀
                    index = items.index(item) + 1
                    ext = os.path.splitext(old_name)[1]
                    base = os.path.splitext(old_name)[0]
                    new_name = f"{index:03d}_{base}{ext}"
                elif rename_type == 'remove_special_chars':
                    # 移除特殊字符
                    new_name = re.sub(r'[^\w\s.-]', '', old_name)
                elif rename_type == 'to_lowercase':
                    # 转为小写
                    new_name = old_name.lower()
                elif rename_type == 'to_uppercase':
                    # 转为大写
                    new_name = old_name.upper()
                elif rename_type == 'space_to_underscore':
                    # 空格替换为下划线
                    new_name = old_name.replace(' ', '_')
                
                if new_name and new_name != old_name:
                    old_path = item['path']
                    new_path = os.path.join(path, new_name).replace('\\', '/')
                    
                    try:
                        self.sftp.rename(old_path, new_path)
                        results.append({
                            'old_name': old_name,
                            'new_name': new_name,
                            'success': True,
                            'message': '重命名成功'
                        })
                        success_count += 1
                    except Exception as e:
                        results.append({
                            'old_name': old_name,
                            'new_name': new_name,
                            'success': False,
                            'message': f'重命名失败: {str(e)}'
                        })
                        failed_count += 1
                else:
                    results.append({
                        'old_name': old_name,
                        'new_name': old_name,
                        'success': True,
                        'message': '无需重命名'
                    })
            
            return True, results, f"重命名完成: {success_count} 成功, {failed_count} 失败"
        except Exception as e:
            return False, [], f"批量重命名失败: {str(e)}"

    def create_folders_for_files(self, path):
        """为目录下的文件创建同名文件夹并移入"""
        try:
            items = self.list_directory(path)
            results = []
            success_count = 0
            failed_count = 0

            # 只处理文件，不处理文件夹
            files = [item for item in items if not item['is_dir']]
            
            for file_item in files:
                filename = file_item['name']
                file_path = file_item['path']
                
                # 获取文件名（不包括扩展名）作为文件夹名
                folder_name = os.path.splitext(filename)[0]
                folder_path = os.path.join(path, folder_name).replace('\\', '/')
                new_file_path = os.path.join(folder_path, filename).replace('\\', '/')
                
                try:
                    # 创建文件夹
                    self.sftp.mkdir(folder_path)
                    
                    # 移动文件到新文件夹
                    self.sftp.rename(file_path, new_file_path)
                    
                    results.append({
                        'filename': filename,
                        'folder_name': folder_name,
                        'success': True,
                        'message': '创建文件夹并移动成功'
                    })
                    success_count += 1
                except Exception as e:
                    results.append({
                        'filename': filename,
                        'folder_name': folder_name,
                        'success': False,
                        'message': f'操作失败: {str(e)}'
                    })
                    failed_count += 1
            
            return True, results, f"文件夹创建完成: {success_count} 成功, {failed_count} 失败"
        except Exception as e:
            return False, [], f"创建文件夹失败: {str(e)}"

    def organize_directory(self, path, organize_type):
        """整理目录"""
        try:
            if organize_type == 'create_folders_for_files':
                return self.create_folders_for_files(path)
            elif organize_type == 'remove_empty_dirs':
                return self.remove_empty_directories(path)
            else:
                return False, [], "未知的整理类型"
        except Exception as e:
            return False, [], f"目录整理失败: {str(e)}"

    def remove_empty_directories(self, path):
        """移除空目录"""
        try:
            items = self.list_directory(path)
            results = []
            success_count = 0
            failed_count = 0

            # 只处理目录
            dirs = [item for item in items if item['is_dir']]
            
            for dir_item in dirs:
                dir_path = dir_item['path']
                dir_items = self.list_directory(dir_path)
                
                if not dir_items:  # 空目录
                    try:
                        self.sftp.rmdir(dir_path)
                        results.append({
                            'dir_name': dir_item['name'],
                            'success': True,
                            'message': '空目录已删除'
                        })
                        success_count += 1
                    except Exception as e:
                        results.append({
                            'dir_name': dir_item['name'],
                            'success': False,
                            'message': f'删除失败: {str(e)}'
                        })
                        failed_count += 1
                else:
                    results.append({
                        'dir_name': dir_item['name'],
                        'success': True,
                        'message': '目录非空，跳过'
                    })
            
            return True, results, f"空目录清理完成: {success_count} 成功, {failed_count} 失败"
        except Exception as e:
            return False, [], f"空目录清理失败: {str(e)}"

# 全局SSH管理器实例
ssh_manager = SSHFileManager()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html', connected=ssh_manager.connected)

@app.route('/connect', methods=['POST'])
def connect():
    """连接SSH服务器"""
    data = request.get_json()
    hostname = data.get('hostname')
    username = data.get('username')
    password = data.get('password')
    port = int(data.get('port', 22))
    
    success, message = ssh_manager.connect(hostname, username, password, port)
    
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """断开SSH连接"""
    ssh_manager.disconnect()
    return jsonify({
        'success': True,
        'message': '已断开连接'
    })

@app.route('/connection_status')
def connection_status():
    """检查连接状态"""
    return jsonify({
        'connected': ssh_manager.is_connected()
    })

@app.route('/compare', methods=['POST'])
def compare():
    """比较两个目录"""
    if not ssh_manager.is_connected():
        return jsonify({
            'success': False,
            'message': '请先连接SSH服务器'
        })
    
    data = request.get_json()
    path1 = data.get('path1')
    path2 = data.get('path2')
    similarity_threshold = data.get('similarity_threshold', 0.8)
    
    if not path1 or not path2:
        return jsonify({
            'success': False,
            'message': '请输入两个有效的路径'
        })
    
    try:
        duplicates = ssh_manager.compare_directories(path1, path2, similarity_threshold)
        exact_count = len([d for d in duplicates if d.get('match_type') == 'exact'])
        similar_count = len([d for d in duplicates if d.get('match_type') == 'similar'])
        
        return jsonify({
            'success': True,
            'duplicates': duplicates,
            'message': f'找到 {exact_count} 个完全重复项和 {similar_count} 个相似项'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'比较失败: {str(e)}'
        })

@app.route('/delete', methods=['POST'])
def delete():
    """删除文件或目录"""
    if not ssh_manager.is_connected():
        return jsonify({
            'success': False,
            'message': '请先连接SSH服务器'
        })
    
    data = request.get_json()
    path = data.get('path')
    
    if not path:
        return jsonify({
            'success': False,
            'message': '请指定要删除的路径'
        })
    
    success, message = ssh_manager.delete_file_or_dir(path)
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/batch_delete', methods=['POST'])
def batch_delete():
    """批量删除文件或目录"""
    if not ssh_manager.is_connected():
        return jsonify({
            'success': False,
            'message': '请先连接SSH服务器'
        })
    
    data = request.get_json()
    paths = data.get('paths', [])
    
    if not paths:
        return jsonify({
            'success': False,
            'message': '请指定要删除的路径列表'
        })
    
    results = []
    success_count = 0
    failed_count = 0
    
    for path in paths:
        try:
            success, message = ssh_manager.delete_file_or_dir(path)
            results.append({
                'path': path,
                'success': success,
                'message': message
            })
            if success:
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            results.append({
                'path': path,
                'success': False,
                'message': f'删除失败: {str(e)}'
            })
            failed_count += 1
    
    return jsonify({
        'success': True,
        'results': results,
        'summary': {
            'total': len(paths),
            'success': success_count,
            'failed': failed_count
        },
        'message': f'批量删除完成: {success_count} 成功, {failed_count} 失败'
    })

@app.route('/browse')
def browse():
    """浏览目录"""
    if not ssh_manager.is_connected():
        return jsonify({
            'success': False,
            'message': '请先连接SSH服务器'
        })
    
    path = request.args.get('path', '/')
    try:
        items = ssh_manager.list_directory(path)
        return jsonify({
            'success': True,
            'items': items,
            'current_path': path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'浏览失败: {str(e)}'
        })

@app.route('/batch_rename', methods=['POST'])
def batch_rename():
    """批量重命名文件和文件夹"""
    if not ssh_manager.is_connected():
        return jsonify({
            'success': False,
            'message': '请先连接SSH服务器'
        })
    
    data = request.get_json()
    path = data.get('path')
    rename_type = data.get('rename_type')
    pattern = data.get('pattern')
    replacement = data.get('replacement')
    
    if not path or not rename_type:
        return jsonify({
            'success': False,
            'message': '请指定目录路径和重命名类型'
        })
    
    success, results, message = ssh_manager.batch_rename(path, rename_type, pattern, replacement)
    
    return jsonify({
        'success': success,
        'results': results,
        'message': message
    })

@app.route('/organize_directory', methods=['POST'])
def organize_directory():
    """整理目录"""
    if not ssh_manager.is_connected():
        return jsonify({
            'success': False,
            'message': '请先连接SSH服务器'
        })
    
    data = request.get_json()
    path = data.get('path')
    organize_type = data.get('organize_type')
    
    if not path or not organize_type:
        return jsonify({
            'success': False,
            'message': '请指定目录路径和整理类型'
        })
    
    success, results, message = ssh_manager.organize_directory(path, organize_type)
    
    return jsonify({
        'success': success,
        'results': results,
        'message': message
    })

if __name__ == '__main__':
    # 确保模板目录存在
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    
    app.run(debug=True, host='0.0.0.0', port=5000) 