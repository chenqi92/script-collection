/* 文件浏览器模块 */

// 浏览路径
async function browsePath(inputId) {
    // 先检查连接状态
    try {
        const statusResponse = await fetch('/connection_status');
        const statusResult = await statusResponse.json();

        if (statusResult.mode === 'remote' && !statusResult.connected) {
            showMessage('请先连接SSH服务器', 'warning');
            updateConnectionStatus(false, statusResult.mode);
            return;
        }
    } catch (error) {
        showMessage('检查连接状态失败', 'danger');
        return;
    }

    currentBrowsingInput = inputId;
    // 设置默认路径，Windows本地模式显示驱动器列表
    let defaultPath;
    if (currentMode === 'local') {
        // 检查是否是Windows系统
        if (navigator.platform.toLowerCase().includes('win')) {
            defaultPath = 'drives'; // Windows显示驱动器列表
        } else {
            defaultPath = '/'; // Linux/Mac显示根目录
        }
    } else {
        defaultPath = '/'; // 远程模式显示根目录
    }
    currentPath = document.getElementById(inputId).value || defaultPath;
    
    // 初始化路径输入框
    const pathInput = document.getElementById('directPathInput');
    pathInput.value = currentPath;
    
    // 绑定回车事件（每次重新绑定以确保正确工作）
    pathInput.onkeypress = function(e) {
        if (e.key === 'Enter') {
            navigateToPath();
        }
    };
    
    loadDirectory(currentPath);
    browseModal.show();
}

// 加载目录
async function loadDirectory(path) {
    try {
        const response = await fetch(`/browse?path=${encodeURIComponent(path)}`);
        const result = await response.json();

        if (result.success) {
            displayFileList(result.items, result.current_path);
            updateBreadcrumb(result.current_path);
        } else {
            showMessage(result.message, 'danger');
            // 如果是连接问题，更新连接状态
            if (result.message.includes('请先连接SSH服务器') || result.message.includes('请先确保本地模式正常')) {
                updateConnectionStatus(false, currentMode);
                browseModal.hide();
            }
        }
    } catch (error) {
        showMessage('浏览目录失败: ' + error.message, 'danger');
    }
}

// 显示文件列表
function displayFileList(items, path) {
    const fileList = document.getElementById('fileList');
    currentPath = path;

    let html = '';

    // 添加上级目录选项或驱动器列表
    if (currentMode === 'local' && (path === '/' || path === '' || path === '.' || path === 'drives')) {
        // Windows根目录，不显示上级目录
    } else if (path !== '/') {
        // 普通目录显示上级目录
        html += `
            <div class="list-group-item file-item" onclick="navigateToParent()">
                <i class="bi bi-arrow-up"></i> 上级目录
            </div>
        `;
    }

    // 在Windows本地模式下，添加驱动器列表入口
    if (currentMode === 'local' && path !== '/' && path !== '' && path !== '.' && path !== 'drives') {
        // 检测是否在Windows驱动器根目录
        const isDriveRoot = /^[A-Z]:\/$/i.test(path);
        if (isDriveRoot) {
            html += `
                <div class="list-group-item file-item" onclick="loadDirectory('drives')">
                    <i class="bi bi-hdd"></i> 其他驱动器
                </div>
            `;
        }
    }

    // 先显示目录
    items.filter(item => item.is_dir).forEach(item => {
        html += `
            <div class="list-group-item file-item" onclick="loadDirectory('${item.path}')">
                <i class="bi bi-folder text-warning"></i> ${item.name}
                <small class="text-muted float-end">${item.modified}</small>
            </div>
        `;
    });

    // 再显示文件
    items.filter(item => !item.is_dir).forEach(item => {
        const isFileSelection = currentBrowsingInput === 'editorFilePath';
        const fileClickHandler = isFileSelection ? `selectFile('${item.path}')` : '';
        const fileClass = isFileSelection ? 'file-item' : '';

        html += `
            <div class="list-group-item ${fileClass}" ${isFileSelection ? `onclick="${fileClickHandler}"` : ''}>
                <i class="bi bi-file-earmark text-primary"></i> ${item.name}
                <small class="text-muted float-end">${formatFileSize(item.size)} | ${item.modified}</small>
            </div>
        `;
    });

    if (html === '') {
        html = '<div class="list-group-item text-muted">目录为空</div>';
    }

    fileList.innerHTML = html;
}

// 更新面包屑导航
function updateBreadcrumb(path) {
    const breadcrumb = document.getElementById('pathBreadcrumb');
    let html = '';
    
    if (currentMode === 'local') {
        // 本地模式的面包屑处理
        if (path === '/' || path === '' || path === '.' || path === 'drives') {
            // 显示驱动器列表
            html = '<li class="breadcrumb-item active">驱动器列表</li>';
        } else {
            // Windows路径处理
            const isWindowsPath = /^[A-Z]:/i.test(path);
            if (isWindowsPath) {
                const parts = path.split('/').filter(part => part !== '');
                const driveLetter = parts[0]; // 如 "C:"
                
                // 驱动器根目录链接
                html += `<li class="breadcrumb-item"><a href="#" onclick="loadDirectory('drives')">驱动器</a></li>`;
                html += `<li class="breadcrumb-item"><a href="#" onclick="loadDirectory('${driveLetter}/')">${driveLetter}</a></li>`;
                
                // 其他路径部分
                let currentPath = driveLetter;
                for (let i = 1; i < parts.length; i++) {
                    currentPath += '/' + parts[i];
                    if (i === parts.length - 1) {
                        html += `<li class="breadcrumb-item active">${parts[i]}</li>`;
                    } else {
                        html += `<li class="breadcrumb-item"><a href="#" onclick="loadDirectory('${currentPath}')">${parts[i]}</a></li>`;
                    }
                }
            } else {
                // Unix样式路径
                const parts = path.split('/').filter(part => part !== '');
                html = '<li class="breadcrumb-item"><a href="#" onclick="loadDirectory(\'/\')">根目录</a></li>';
                let currentPath = '';
                parts.forEach((part, index) => {
                    currentPath += '/' + part;
                    if (index === parts.length - 1) {
                        html += `<li class="breadcrumb-item active">${part}</li>`;
                    } else {
                        html += `<li class="breadcrumb-item"><a href="#" onclick="loadDirectory('${currentPath}')">${part}</a></li>`;
                    }
                });
            }
        }
    } else {
        // 远程模式保持原逻辑
        const parts = path.split('/').filter(part => part !== '');
        html = '<li class="breadcrumb-item"><a href="#" onclick="loadDirectory(\'/\')">根目录</a></li>';
        let currentPath = '';
        parts.forEach((part, index) => {
            currentPath += '/' + part;
            if (index === parts.length - 1) {
                html += `<li class="breadcrumb-item active">${part}</li>`;
            } else {
                html += `<li class="breadcrumb-item"><a href="#" onclick="loadDirectory('${currentPath}')">${part}</a></li>`;
            }
        });
    }

    breadcrumb.innerHTML = html;
    
    // 同步更新路径输入框
    document.getElementById('directPathInput').value = path;
}

// 导航到指定路径
function navigateToPath() {
    const inputPath = document.getElementById('directPathInput').value.trim();
    if (inputPath) {
        loadDirectory(inputPath);
    } else {
        showMessage('请输入有效的路径', 'warning');
    }
}

// 导航到上级目录
function navigateToParent() {
    if (currentMode === 'local') {
        // Windows路径特殊处理
        const isWindowsPath = /^[A-Z]:/i.test(currentPath);
        if (isWindowsPath) {
            const parts = currentPath.split('/').filter(part => part !== '');
            if (parts.length === 1) {
                // 从驱动器根目录返回到驱动器列表
                loadDirectory('drives');
                return;
            } else {
                // 返回上一级目录
                parts.pop();
                const parentPath = parts.join('/') + (parts.length === 1 ? '/' : '');
                loadDirectory(parentPath);
                return;
            }
        }
    }
    
    // 默认处理（Linux/远程模式）
    const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/')) || '/';
    loadDirectory(parentPath);
}

// 选择当前路径
function selectCurrentPath() {
    document.getElementById(currentBrowsingInput).value = currentPath;
    browseModal.hide();
}

// 选择文件
function selectFile(filePath) {
    document.getElementById(currentBrowsingInput).value = filePath;
    browseModal.hide();
}

// 为文件选择浏览
function browseForFile() {
    // 使用目录浏览器，但允许选择文件
    currentBrowsingInput = 'editorFilePath';
    
    // 初始化路径
    let defaultPath;
    if (currentMode === 'local') {
        // 检查是否是Windows系统
        if (navigator.platform.toLowerCase().includes('win')) {
            defaultPath = currentPath || 'drives'; // Windows显示驱动器列表
        } else {
            defaultPath = currentPath || '/'; // Linux/Mac显示根目录
        }
    } else {
        defaultPath = '/'; // 远程模式显示根目录
    }
    
    // 初始化路径输入框
    const pathInput = document.getElementById('directPathInput');
    pathInput.value = defaultPath;
    
    // 绑定回车事件
    pathInput.onkeypress = function(e) {
        if (e.key === 'Enter') {
            navigateToPath();
        }
    };
    
    browseModal.show();
    loadDirectory(defaultPath);
} 