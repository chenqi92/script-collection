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
    const defaultPath = currentMode === 'local' ? '.' : '/';
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

    // 添加上级目录选项
    if (path !== '/') {
        html += `
            <div class="list-group-item file-item" onclick="navigateToParent()">
                <i class="bi bi-arrow-up"></i> 上级目录
            </div>
        `;
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
    const parts = path.split('/').filter(part => part !== '');

    let html = '<li class="breadcrumb-item"><a href="#" onclick="loadDirectory(\'/\')">根目录</a></li>';
    let currentPath = '';

    parts.forEach((part, index) => {
        currentPath += '/' + part;
        if (index === parts.length - 1) {
            html += `<li class="breadcrumb-item active">${part}</li>`;
        } else {
            html += `<li class="breadcrumb-item"><a href="#" onclick="loadDirectory('${currentPath}')">${part}</a></li>`;
        }
    });

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
    const defaultPath = currentMode === 'remote' ? '/' : (currentPath || '/');
    
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