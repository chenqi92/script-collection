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

if __name__ == '__main__':
    # 确保模板目录存在
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    
    app.run(debug=True, host='0.0.0.0', port=5000) 