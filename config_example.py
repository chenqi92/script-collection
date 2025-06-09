# SSH文件管理器配置示例
# 复制此文件为 config.py 并根据需要修改设置

class Config:
    # Flask应用配置
    SECRET_KEY = 'your-secret-key-change-this-in-production'
    
    # 服务器配置
    HOST = '0.0.0.0'  # 监听所有IP地址，改为 '127.0.0.1' 只允许本地访问
    PORT = 5000       # Web服务端口
    DEBUG = True      # 开发模式，生产环境请设为 False
    
    # SSH连接配置
    SSH_TIMEOUT = 10          # SSH连接超时时间（秒）
    SSH_BANNER_TIMEOUT = 30   # SSH横幅超时时间（秒）
    SSH_AUTH_TIMEOUT = 30     # SSH认证超时时间（秒）
    
    # 文件处理配置
    MAX_FILE_SIZE_FOR_HASH = 100 * 1024 * 1024  # 最大哈希计算文件大小（100MB）
    CHUNK_SIZE = 4096                            # 文件读取块大小
    
    # 安全配置
    ALLOWED_EXTENSIONS = {'.txt', '.log', '.conf', '.py', '.js', '.html', '.css', '.json', '.xml', '.yml', '.yaml'}
    DANGEROUS_PATHS = {'/boot', '/sys', '/proc', '/dev'}  # 危险路径列表（仅警告）
    
    # UI配置
    ITEMS_PER_PAGE = 50       # 每页显示的文件数量
    MAX_PATH_DISPLAY = 80     # 路径显示最大长度
    
    # 日志配置
    ENABLE_LOGGING = True
    LOG_LEVEL = 'INFO'        # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE = 'ssh_manager.log'

# 预设服务器配置（可选）
PRESET_SERVERS = [
    {
        'name': '本地测试服务器',
        'hostname': '127.0.0.1',
        'username': 'testuser',
        'port': 22,
        'description': '用于本地测试的SSH服务器'
    },
    {
        'name': '开发服务器',
        'hostname': 'dev.example.com',
        'username': 'developer',
        'port': 22,
        'description': '开发环境服务器'
    }
]

# 常用路径配置（可选）
COMMON_PATHS = [
    '/home',
    '/var/log',
    '/opt',
    '/tmp',
    '/usr/local',
    '/etc'
]

# 文件类型图标映射
FILE_ICONS = {
    'directory': 'bi-folder',
    'file': 'bi-file-earmark',
    '.txt': 'bi-file-text',
    '.log': 'bi-file-text',
    '.py': 'bi-file-code',
    '.js': 'bi-file-code',
    '.html': 'bi-file-code',
    '.css': 'bi-file-code',
    '.json': 'bi-file-code',
    '.xml': 'bi-file-code',
    '.yml': 'bi-file-code',
    '.yaml': 'bi-file-code',
    '.conf': 'bi-gear',
    '.cfg': 'bi-gear',
    '.ini': 'bi-gear',
    '.zip': 'bi-file-zip',
    '.tar': 'bi-file-zip',
    '.gz': 'bi-file-zip',
    '.pdf': 'bi-file-pdf',
    '.doc': 'bi-file-word',
    '.docx': 'bi-file-word',
    '.xls': 'bi-file-excel',
    '.xlsx': 'bi-file-excel',
    '.ppt': 'bi-file-ppt',
    '.pptx': 'bi-file-ppt',
    '.jpg': 'bi-file-image',
    '.jpeg': 'bi-file-image',
    '.png': 'bi-file-image',
    '.gif': 'bi-file-image',
    '.mp3': 'bi-file-music',
    '.wav': 'bi-file-music',
    '.mp4': 'bi-file-play',
    '.avi': 'bi-file-play',
    '.mov': 'bi-file-play'
} 