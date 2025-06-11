# 统一文件管理器 / Unified File Manager

[English](#english) | [中文](#chinese)

---

<a name="chinese"></a>
## 🇨🇳 中文版本

### 📋 项目简介

统一文件管理器是一个基于 Web 的文件管理工具，支持本地文件系统和远程 SSH 服务器的统一管理。通过现代化的 Web 界面，您可以轻松地在本地和远程文件系统之间进行各种文件操作。

### ✨ 核心功能

#### 🔗 连接管理
- **本地模式**：直接操作本地文件系统
- **远程模式**：通过 SSH 连接管理远程服务器文件
- **双重认证**：支持密码认证和 SSH 密钥认证
- **连接历史**：保存常用连接配置，快速重连

#### 📊 目录比较
- 比较两个目录的文件差异
- 智能检测重复文件和相似文件
- 可调节相似度阈值（60%-100%）
- 批量删除重复文件
- 详细的比较结果展示

#### 🌳 目录树生成
- 生成目录的树形结构图
- 支持 .gitignore 规则过滤
- 可选择显示文件或仅显示目录
- 限制显示层级深度
- 清晰的目录结构可视化

#### 🧹 空目录清理
- 自动扫描并清理空目录
- 递归清理深层嵌套的空目录
- 支持撤销操作
- 详细的清理日志

#### 📝 批量重命名
- **预设重命名规则**：
  - 移除数字前缀
  - 添加序号前缀/后缀
  - 添加自定义前缀/后缀
  - 移除特殊字符
  - 大小写转换
  - 空格与下划线互换
  - 添加日期前缀
  - 首字母大写
- **正则表达式**：支持复杂的模式匹配和替换
- **批量处理**：一次性重命名多个文件

#### 📁 目录整理
- **为文件创建同名文件夹**：自动为每个文件创建独立文件夹
- **移除空目录**：清理整理过程中产生的空目录
- 批量操作结果统计

#### ✏️ 文件编辑器
- **多格式支持**：
  - 纯文本、YAML、JSON、XML
  - INI/Config、Shell Script
  - Python、JavaScript、CSS、HTML
  - SQL、Markdown
- **自动检测**：根据文件扩展名自动识别类型
- **语法高亮**：基于文件类型提供语法着色
- **格式化功能**：JSON、YAML 等格式的自动格式化
- **实时状态**：显示光标位置和文件加载状态

#### 📋 操作日志
- **详细记录**：所有操作的完整日志
- **可视化状态**：成功、警告、错误状态图标
- **撤销功能**：支持部分操作的撤销
- **浮动显示**：便捷的日志查看面板

### 🚀 快速开始

#### 环境要求
- Python 3.7+
- Flask 及相关依赖
- 现代浏览器（Chrome、Firefox、Safari、Edge）

#### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/unified-file-manager.git
   cd unified-file-manager
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动服务**
   ```bash
   python ssh_file_manager.py
   ```
   或使用启动脚本：
   ```bash
   python start_file_manager.py
   ```

4. **访问应用**
   - 打开浏览器访问：http://localhost:5000
   - 默认端口为 5000，可在配置中修改

#### 使用指南

1. **选择模式**
   - 点击顶部的"本地模式"或"远程模式"按钮
   - 本地模式：直接操作本地文件
   - 远程模式：需要先配置 SSH 连接

2. **SSH 连接设置**（远程模式）
   - 填写服务器地址、用户名、端口
   - 选择认证方式：密码或 SSH 密钥
   - 点击"连接"建立远程连接

3. **功能使用**
   - 通过左侧功能菜单选择需要的工具
   - 每个功能都有详细的操作说明
   - 操作结果会在操作日志中显示

### 🔧 技术特性

#### 架构设计
- **前后端分离**：Flask 后端 + 现代化前端
- **模块化结构**：功能模块独立，易于维护
- **响应式设计**：适配各种屏幕尺寸

#### 安全特性
- **SSH 连接加密**：所有远程操作通过 SSH 加密传输
- **密钥认证支持**：更安全的无密码认证方式
- **操作确认**：危险操作需要用户确认

#### 性能优化
- **异步处理**：大文件操作不阻塞界面
- **智能缓存**：目录浏览结果缓存提升响应速度
- **批量操作**：减少网络请求次数

### 📖 详细功能说明

#### 目录比较功能详解

**使用场景**：
- 清理重复文件，释放存储空间
- 备份验证，确保文件一致性
- 文件同步检查
- 数据整理和去重

**操作步骤**：
1. 在"目录比较"面板中输入两个目录路径
2. 设置相似度阈值（推荐 80%）
3. 点击"比较"按钮开始分析
4. 查看结果列表，包含：
   - 完全重复的文件（MD5 相同）
   - 相似的文件（文件名相似）
5. 选择要删除的文件，支持批量操作

**相似度算法**：
- 使用编辑距离算法计算文件名相似度
- 考虑文件大小和修改时间
- 提供可调节的阈值控制

#### 目录树生成详解

**使用场景**：
- 项目结构文档生成
- 文件系统结构分析
- 代码仓库结构展示
- 技术文档编写

**生成选项**：
- **应用 .gitignore**：自动排除 Git 忽略的文件
- **仅显示目录**：只显示文件夹结构
- **最大层级**：限制显示深度，避免过深的嵌套

**输出格式**：
```
project/
├── src/
│   ├── components/
│   │   ├── Header.js
│   │   └── Footer.js
│   └── utils/
│       └── helpers.js
├── docs/
│   └── README.md
└── package.json
```

#### 批量重命名详解

**预设规则说明**：

1. **移除数字前缀**：删除文件名开头的数字（如 "001-文件.txt" → "文件.txt"）
2. **添加序号前缀**：按顺序添加编号（如 "文件.txt" → "001-文件.txt"）
3. **自定义前缀/后缀**：添加指定的文本到文件名前后
4. **特殊字符处理**：移除或替换特殊字符，规范文件名
5. **大小写转换**：统一文件名的大小写格式
6. **空格处理**：空格与下划线的相互转换
7. **日期前缀**：添加当前日期到文件名前（格式：YYYY-MM-DD）

**正则表达式模式**：
- 支持标准正则表达式语法
- 常用模式示例：
  - `^\d+\s*` - 匹配开头的数字和空格
  - `\[.*?\]` - 匹配方括号及内容
  - `\s+` - 匹配多个空格

#### 文件编辑器详解

**支持的文件类型**：
- **配置文件**：YAML、JSON、XML、INI
- **脚本文件**：Shell、Python、JavaScript
- **网页文件**：HTML、CSS
- **文档文件**：Markdown、纯文本
- **数据库文件**：SQL

**编辑功能**：
- **自动检测**：根据文件扩展名自动选择类型
- **语法高亮**：提供基础的语法着色
- **格式化**：JSON 和 YAML 文件的自动格式化
- **状态显示**：实时显示光标位置
- **安全保存**：自动创建备份文件

### 🛠️ 开发与部署

#### 开发环境设置

1. **Python 环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **开发模式启动**
   ```bash
   export FLASK_ENV=development  # Windows: set FLASK_ENV=development
   python ssh_file_manager.py
   ```

#### 生产部署

1. **使用 Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 ssh_file_manager:app
   ```

2. **Nginx 配置示例**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### 🔒 安全注意事项

1. **SSH 密钥管理**
   - 使用强密码保护私钥
   - 定期更换 SSH 密钥
   - 限制密钥使用权限

2. **网络安全**
   - 建议在内网环境使用
   - 如需公网访问，请配置 HTTPS
   - 考虑添加访问认证

3. **文件权限**
   - 确保程序有足够的文件系统权限
   - 避免以 root 权限运行
   - 定期检查日志文件

### 🐛 故障排除

#### 常见问题

1. **SSH 连接失败**
   - 检查网络连接和防火墙设置
   - 验证 SSH 服务是否运行
   - 确认用户名和密码正确
   - 检查 SSH 密钥文件路径和权限

2. **文件操作权限错误**
   - 确认当前用户有足够权限
   - 检查目标目录的访问权限
   - 验证磁盘空间是否充足

3. **界面响应缓慢**
   - 检查网络连接质量
   - 减少同时处理的文件数量
   - 关闭不必要的浏览器标签页

#### 日志查看

程序运行时会输出详细的日志信息，包括：
- SSH 连接状态
- 文件操作结果
- 错误信息和堆栈跟踪

### 🤝 贡献指南

欢迎参与项目改进！

1. **Fork 项目**
2. **创建功能分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送分支** (`git push origin feature/AmazingFeature`)
5. **创建 Pull Request**

### 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

### 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 在线讨论

---

<a name="english"></a>
## 🇺🇸 English Version

### 📋 Project Introduction

Unified File Manager is a web-based file management tool that supports unified management of local file systems and remote SSH servers. Through a modern web interface, you can easily perform various file operations between local and remote file systems.

### ✨ Core Features

#### 🔗 Connection Management
- **Local Mode**: Direct operation of local file system
- **Remote Mode**: Manage remote server files via SSH connection
- **Dual Authentication**: Support for password and SSH key authentication
- **Connection History**: Save common connection configurations for quick reconnection

#### 📊 Directory Comparison
- Compare file differences between two directories
- Intelligently detect duplicate and similar files
- Adjustable similarity threshold (60%-100%)
- Batch delete duplicate files
- Detailed comparison result display

#### 🌳 Directory Tree Generation
- Generate tree structure diagrams of directories
- Support .gitignore rule filtering
- Option to show files or directories only
- Limit display depth levels
- Clear directory structure visualization

#### 🧹 Empty Directory Cleanup
- Automatically scan and clean empty directories
- Recursively clean deeply nested empty directories
- Support undo operations
- Detailed cleanup logs

#### 📝 Batch Renaming
- **Preset Renaming Rules**:
  - Remove number prefix
  - Add sequence prefix/suffix
  - Add custom prefix/suffix
  - Remove special characters
  - Case conversion
  - Space and underscore interchange
  - Add date prefix
  - Capitalize words
- **Regular Expressions**: Support complex pattern matching and replacement
- **Batch Processing**: Rename multiple files at once

#### 📁 Directory Organization
- **Create folders for files**: Automatically create individual folders for each file
- **Remove empty directories**: Clean up empty directories generated during organization
- Batch operation result statistics

#### ✏️ File Editor
- **Multi-format Support**:
  - Plain text, YAML, JSON, XML
  - INI/Config, Shell Script
  - Python, JavaScript, CSS, HTML
  - SQL, Markdown
- **Auto Detection**: Automatically identify type based on file extension
- **Syntax Highlighting**: Provide syntax coloring based on file type
- **Format Function**: Auto-formatting for JSON, YAML and other formats
- **Real-time Status**: Display cursor position and file loading status

#### 📋 Operation Log
- **Detailed Records**: Complete logs of all operations
- **Visual Status**: Success, warning, error status icons
- **Undo Function**: Support undo for some operations
- **Floating Display**: Convenient log viewing panel

### 🚀 Quick Start

#### Requirements
- Python 3.7+
- Flask and related dependencies
- Modern browser (Chrome, Firefox, Safari, Edge)

#### Installation Steps

1. **Clone Project**
   ```bash
   git clone https://github.com/your-repo/unified-file-manager.git
   cd unified-file-manager
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Service**
   ```bash
   python ssh_file_manager.py
   ```
   Or use the startup script:
   ```bash
   python start_file_manager.py
   ```

4. **Access Application**
   - Open browser and visit: http://localhost:5000
   - Default port is 5000, can be modified in configuration

#### Usage Guide

1. **Select Mode**
   - Click "Local Mode" or "Remote Mode" button at the top
   - Local mode: Direct operation of local files
   - Remote mode: Need to configure SSH connection first

2. **SSH Connection Setup** (Remote Mode)
   - Fill in server address, username, port
   - Choose authentication method: password or SSH key
   - Click "Connect" to establish remote connection

3. **Feature Usage**
   - Select needed tools through the left function menu
   - Each function has detailed operation instructions
   - Operation results will be displayed in the operation log

### 🔧 Technical Features

#### Architecture Design
- **Frontend-Backend Separation**: Flask backend + modern frontend
- **Modular Structure**: Independent functional modules, easy to maintain
- **Responsive Design**: Adapt to various screen sizes

#### Security Features
- **SSH Connection Encryption**: All remote operations transmitted via SSH encryption
- **Key Authentication Support**: More secure passwordless authentication
- **Operation Confirmation**: Dangerous operations require user confirmation

#### Performance Optimization
- **Asynchronous Processing**: Large file operations don't block interface
- **Smart Caching**: Directory browsing result caching improves response speed
- **Batch Operations**: Reduce network request frequency

### 📖 Detailed Feature Description

#### Directory Comparison Feature

**Use Cases**:
- Clean duplicate files to free storage space
- Backup verification to ensure file consistency
- File synchronization checking
- Data organization and deduplication

**Operation Steps**:
1. Enter two directory paths in the "Directory Comparison" panel
2. Set similarity threshold (recommended 80%)
3. Click "Compare" button to start analysis
4. View result list, including:
   - Completely duplicate files (same MD5)
   - Similar files (similar filenames)
5. Select files to delete, support batch operations

**Similarity Algorithm**:
- Use edit distance algorithm to calculate filename similarity
- Consider file size and modification time
- Provide adjustable threshold control

#### Directory Tree Generation

**Use Cases**:
- Project structure documentation generation
- File system structure analysis
- Code repository structure display
- Technical documentation writing

**Generation Options**:
- **Apply .gitignore**: Automatically exclude Git-ignored files
- **Show directories only**: Display only folder structure
- **Maximum levels**: Limit display depth to avoid deep nesting

**Output Format**:
```
project/
├── src/
│   ├── components/
│   │   ├── Header.js
│   │   └── Footer.js
│   └── utils/
│       └── helpers.js
├── docs/
│   └── README.md
└── package.json
```

#### Batch Renaming Details

**Preset Rules Explanation**:

1. **Remove number prefix**: Delete numbers at the beginning of filename (e.g., "001-file.txt" → "file.txt")
2. **Add sequence prefix**: Add numbering in order (e.g., "file.txt" → "001-file.txt")
3. **Custom prefix/suffix**: Add specified text before/after filename
4. **Special character handling**: Remove or replace special characters, standardize filenames
5. **Case conversion**: Unify filename case format
6. **Space handling**: Interchange between spaces and underscores
7. **Date prefix**: Add current date to filename prefix (format: YYYY-MM-DD)

**Regular Expression Patterns**:
- Support standard regex syntax
- Common pattern examples:
  - `^\d+\s*` - Match leading digits and spaces
  - `\[.*?\]` - Match square brackets and content
  - `\s+` - Match multiple spaces

#### File Editor Details

**Supported File Types**:
- **Configuration files**: YAML, JSON, XML, INI
- **Script files**: Shell, Python, JavaScript
- **Web files**: HTML, CSS
- **Document files**: Markdown, plain text
- **Database files**: SQL

**Editing Features**:
- **Auto Detection**: Automatically select type based on file extension
- **Syntax Highlighting**: Provide basic syntax coloring
- **Formatting**: Auto-formatting for JSON and YAML files
- **Status Display**: Real-time cursor position display
- **Safe Save**: Automatically create backup files

### 🛠️ Development & Deployment

#### Development Environment Setup

1. **Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Development Mode Startup**
   ```bash
   export FLASK_ENV=development  # Windows: set FLASK_ENV=development
   python ssh_file_manager.py
   ```

#### Production Deployment

1. **Using Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 ssh_file_manager:app
   ```

2. **Nginx Configuration Example**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### 🔒 Security Considerations

1. **SSH Key Management**
   - Use strong passwords to protect private keys
   - Regularly rotate SSH keys
   - Limit key usage permissions

2. **Network Security**
   - Recommended for use in internal network environments
   - Configure HTTPS if public network access is needed
   - Consider adding access authentication

3. **File Permissions**
   - Ensure program has sufficient file system permissions
   - Avoid running with root privileges
   - Regularly check log files

### 🐛 Troubleshooting

#### Common Issues

1. **SSH Connection Failure**
   - Check network connection and firewall settings
   - Verify SSH service is running
   - Confirm username and password are correct
   - Check SSH key file path and permissions

2. **File Operation Permission Errors**
   - Confirm current user has sufficient permissions
   - Check target directory access permissions
   - Verify sufficient disk space

3. **Slow Interface Response**
   - Check network connection quality
   - Reduce number of files processed simultaneously
   - Close unnecessary browser tabs

#### Log Viewing

The program outputs detailed log information during runtime, including:
- SSH connection status
- File operation results
- Error messages and stack traces

### 🤝 Contributing

Contributions are welcome to improve the project!

1. **Fork the Project**
2. **Create Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push Branch** (`git push origin feature/AmazingFeature`)
5. **Create Pull Request**

### 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

### 📞 Contact

For questions or suggestions, please contact through:
- Submit Issues
- Send emails
- Online discussions

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-repo/unified-file-manager&type=Date)](https://star-history.com/#your-repo/unified-file-manager&Date)

---

**Made with ❤️ by the development team**
