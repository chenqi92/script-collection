/* 统一文件管理器 - 主应用程序脚本 */

// 全局变量
let currentBrowsingInput = '';
let currentPath = '/';
let browseModal;
let customConfirmModal;
let currentMode = 'local';
let operationHistory = [];
let isLogVisible = false;
let duplicatesData = [];
let currentFileContent = '';
let currentFilePath = '';

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function () {
    browseModal = new bootstrap.Modal(document.getElementById('browseModal'));
    customConfirmModal = new bootstrap.Modal(document.getElementById('customConfirmModal'));

    // 初始化页面状态
    clearPreviousFunctionState();

    // 初始化模式
    initializeMode();

    // 初始化功能菜单
    initializeFunctionMenu();

    // 初始化浮动按钮
    updateFloatingLogButton();

    // 定期检查连接状态
    checkConnectionStatus();
    setInterval(checkConnectionStatus, 5000);

    // 绑定事件
    bindEventListeners();

    // 绑定认证方式切换事件
    document.getElementById('authPassword').addEventListener('change', toggleAuthMethod);
    document.getElementById('authKey').addEventListener('change', toggleAuthMethod);

    // 初始化连接历史
    refreshConnectionHistory();

    // 初始化编辑器事件
    initializeEditorEvents();
});

// 绑定事件监听器
function bindEventListeners() {
    document.getElementById('localModeBtn').addEventListener('click', () => setMode('local'));
    document.getElementById('remoteModeBtn').addEventListener('click', () => setMode('remote'));
    document.getElementById('connectBtn').addEventListener('click', connectSSH);
    document.getElementById('disconnectBtn').addEventListener('click', disconnectSSH);
    document.getElementById('compareBtn').addEventListener('click', comparePaths);
    document.getElementById('selectPathBtn').addEventListener('click', selectCurrentPath);
    document.getElementById('generateTreeBtn').addEventListener('click', generateTree);
    document.getElementById('cleanEmptyDirsBtn').addEventListener('click', cleanEmptyDirectories);
}

// 初始化模式
async function initializeMode() {
    try {
        const response = await fetch('/get_mode');
        const result = await response.json();
        currentMode = result.mode;
        updateModeDisplay();
    } catch (error) {
        console.error('获取模式失败:', error);
        setMode('local'); // 默认使用本地模式
    }
}

// 设置模式
async function setMode(mode) {
    try {
        const response = await fetch('/set_mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({mode: mode})
        });

        const result = await response.json();
        if (result.success) {
            currentMode = mode;
            updateModeDisplay();
            showMessage(result.message, 'success');
            checkConnectionStatus(); // 更新连接状态

            // 延迟执行以确保连接状态已更新
            setTimeout(() => {
                if (currentMode === 'remote') {
                    updateRemoteFunctionAvailability();
                }
            }, 500);
        } else {
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        showMessage('切换模式失败: ' + error.message, 'danger');
    }
}

// 初始化功能菜单
function initializeFunctionMenu() {
    // 绑定功能菜单点击事件
    const functionTabs = document.querySelectorAll('.function-tab');
    functionTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const functionName = tab.dataset.function;
            switchFunction(functionName);
        });
    });
}

// 切换功能面板
function switchFunction(functionName) {
    const targetTab = document.querySelector(`[data-function="${functionName}"]`);

    // 检查是否为禁用状态
    if (targetTab && targetTab.classList.contains('disabled')) {
        showMessage('请先连接SSH服务器才能使用此功能', 'warning');
        return;
    }

    // 清除上一个功能的状态
    clearPreviousFunctionState();

    // 清理文件编辑器状态（如果不是切换到编辑器）
    if (functionName !== 'editor') {
        clearEditorState();
    }

    // 更新选项卡状态
    document.querySelectorAll('.function-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // 切换面板显示
    document.querySelectorAll('.function-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    const targetPanel = document.getElementById(functionName + 'Panel');
    if (targetPanel) {
        targetPanel.classList.add('active');
    }
}

// 清除之前功能的状态
function clearPreviousFunctionState() {
    // 隐藏所有结果面板
    const resultPanels = [
        'resultsPanel',      // 目录比较结果
        'treeOutputPanel'    // 目录树输出
    ];

    resultPanels.forEach(panelId => {
        const panel = document.getElementById(panelId);
        if (panel) {
            panel.style.display = 'none';
        }
    });

    // 清除结果内容
    const resultContainers = [
        'duplicatesList',    // 重复文件列表
        'treeOutput'         // 目录树内容
    ];

    resultContainers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
        }
    });

    // 清除计数显示
    const countElements = [
        'duplicateCount',    // 重复文件计数
        'selectedCount'      // 选中项计数
    ];

    countElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = '';
        }
    });

    // 清除所有输入框内容
    const inputFields = [
        'path1',             // 比较路径1
        'path2',             // 比较路径2
        'treeDirectory',     // 目录树路径
        'cleanDirectory',    // 清理目录路径
        'renamePath',        // 重命名路径
        'organizePath',      // 整理路径
        'editorFilePath',    // 编辑器文件路径
        'customText',        // 自定义文本
        'regexPattern',      // 正则表达式模式
        'regexReplacement'   // 正则表达式替换
    ];

    inputFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = '';
        }
    });

    // 重置复选框和下拉框
    const checkboxes = [
        'applyGitignore',    // 应用gitignore
        'excludeFiles',      // 排除文件
        'selectAll'          // 全选
    ];

    checkboxes.forEach(checkboxId => {
        const checkbox = document.getElementById(checkboxId);
        if (checkbox) {
            if (checkboxId === 'applyGitignore') {
                checkbox.checked = true;  // 默认选中
            } else {
                checkbox.checked = false;
            }
        }
    });

    // 重置下拉框
    const selectFields = [
        'similarityThreshold' // 相似度阈值
    ];

    selectFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.selectedIndex = 2; // 默认选择80%
        }
    });

    // 重置数字输入框
    const numberFields = [
        'maxLevel'           // 最大层级
    ];

    numberFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = '';
        }
    });

    // 隐藏批量控制区
    const batchControls = document.getElementById('batchControls');
    if (batchControls) {
        batchControls.style.display = 'none';
    }

    // 清除全局数据
    duplicatesData = [];
}

// 清理文件编辑器状态
function clearEditorState() {
    // 清空编辑器内容
    const fileEditor = document.getElementById('fileEditor');
    if (fileEditor) {
        fileEditor.value = '';
    }

    // 重置文件信息显示
    const fileInfo = document.getElementById('fileInfo');
    if (fileInfo) {
        fileInfo.textContent = '未加载文件';
    }

    // 重置光标信息
    const cursorInfo = document.getElementById('cursorInfo');
    if (cursorInfo) {
        cursorInfo.textContent = '行: 1, 列: 1';
    }

    // 重置文件类型选择
    const fileType = document.getElementById('fileType');
    if (fileType) {
        fileType.value = 'text';
    }

    // 清空文件路径
    const editorFilePath = document.getElementById('editorFilePath');
    if (editorFilePath) {
        editorFilePath.value = '';
    }

    // 清除全局变量
    if (typeof currentFileContent !== 'undefined') {
        currentFileContent = '';
    }
    if (typeof currentFilePath !== 'undefined') {
        currentFilePath = '';
    }
}

// 更新模式显示
function updateModeDisplay() {
    // 更新按钮状态
    document.getElementById('localModeBtn').classList.toggle('active', currentMode === 'local');
    document.getElementById('remoteModeBtn').classList.toggle('active', currentMode === 'remote');

    // 清除上一个模式的状态
    clearPreviousFunctionState();

    // 根据模式显示/隐藏功能选项卡
    updateFunctionMenuForMode();
}

// 根据模式更新功能菜单
function updateFunctionMenuForMode() {
    const connectionTab = document.querySelector('[data-function="connection"]');
    const toolsTab = document.querySelector('[data-function="tools"]');
    const compareTab = document.querySelector('[data-function="compare"]');
    const treeTab = document.querySelector('[data-function="tree"]');
    const cleanTab = document.querySelector('[data-function="clean"]');
    const renameTab = document.querySelector('[data-function="rename"]');
    const organizeTab = document.querySelector('[data-function="organize"]');
    const editorTab = document.querySelector('[data-function="editor"]');

    if (currentMode === 'local') {
        // 本地模式：隐藏连接管理，显示所有其他功能
        connectionTab.style.display = 'none';
        toolsTab.style.display = 'block';
        compareTab.style.display = 'block';
        treeTab.style.display = 'block';
        cleanTab.style.display = 'block';
        renameTab.style.display = 'block';
        organizeTab.style.display = 'block';
        editorTab.style.display = 'block';

        // 移除所有禁用状态
        [toolsTab, compareTab, treeTab, cleanTab, renameTab, organizeTab, editorTab].forEach(tab => {
            tab.classList.remove('disabled');
            tab.style.pointerEvents = 'auto';
        });

        // 如果当前在连接管理面板，切换到目录比较
        if (connectionTab.classList.contains('active')) {
            switchFunction('compare');
        }
    } else {
        // 远程模式：显示连接管理，其他功能根据连接状态控制
        connectionTab.style.display = 'block';
        toolsTab.style.display = 'none'; // 本地工具在远程模式下隐藏
        compareTab.style.display = 'block';
        treeTab.style.display = 'block';
        cleanTab.style.display = 'block';
        renameTab.style.display = 'block';
        organizeTab.style.display = 'block';
        editorTab.style.display = 'block';

        // 如果当前在本地工具面板，切换到连接管理
        if (toolsTab.classList.contains('active')) {
            switchFunction('connection');
        }

        // 根据连接状态更新功能可用性
        updateRemoteFunctionAvailability();
    }
}

// 更新远程功能可用性
function updateRemoteFunctionAvailability() {
    if (currentMode !== 'remote') return;

    // 检查当前连接状态
    fetch('/connection_status')
        .then(response => response.json())
        .then(result => {
            const isConnected = result.connected;
            const compareTab = document.querySelector('[data-function="compare"]');
            const treeTab = document.querySelector('[data-function="tree"]');
            const cleanTab = document.querySelector('[data-function="clean"]');
            const renameTab = document.querySelector('[data-function="rename"]');
            const organizeTab = document.querySelector('[data-function="organize"]');
            const editorTab = document.querySelector('[data-function="editor"]');

            [compareTab, treeTab, cleanTab, renameTab, organizeTab, editorTab].forEach(tab => {
                if (tab) {
                    if (isConnected) {
                        tab.classList.remove('disabled');
                        tab.style.pointerEvents = 'auto';
                    } else {
                        tab.classList.add('disabled');
                        tab.style.pointerEvents = 'none';
                    }
                }
            });

            // 如果当前在被禁用的功能面板，且未连接，切换到连接管理
            if (!isConnected &&
                (compareTab?.classList.contains('active') ||
                    treeTab?.classList.contains('active') ||
                    cleanTab?.classList.contains('active') ||
                    renameTab?.classList.contains('active') ||
                    organizeTab?.classList.contains('active') ||
                    editorTab?.classList.contains('active'))) {
                switchFunction('connection');
                showMessage('请先连接SSH服务器才能使用此功能', 'warning');
            }
        })
        .catch(error => {
            console.error('检查连接状态失败:', error);
        });
}

// 检查连接状态
async function checkConnectionStatus() {
    try {
        const response = await fetch('/connection_status');
        const result = await response.json();
        updateConnectionStatus(result.connected, result.mode);
    } catch (error) {
        console.error('检查连接状态失败:', error);
    }
}

// 更新连接状态显示
function updateConnectionStatus(connected, mode = currentMode) {
    const badge = document.getElementById('connectionBadge');
    const connectBtn = document.getElementById('connectBtn');
    const disconnectBtn = document.getElementById('disconnectBtn');

    if (mode === 'local') {
        badge.className = 'badge bg-info';
        badge.innerHTML = '<i class="bi bi-laptop"></i> 本地模式';
        connectBtn.style.display = 'none';
        disconnectBtn.style.display = 'none';
    } else if (connected) {
        badge.className = 'badge bg-success';
        badge.innerHTML = '<i class="bi bi-wifi"></i> 远程已连接';
        connectBtn.style.display = 'none';
        disconnectBtn.style.display = 'block';
    } else {
        badge.className = 'badge bg-danger';
        badge.innerHTML = '<i class="bi bi-wifi-off"></i> 远程未连接';
        connectBtn.style.display = 'block';
        disconnectBtn.style.display = 'none';
        // 隐藏结果面板，因为未连接时无法进行比较
        document.getElementById('resultsPanel').style.display = 'none';
    }
}

// 显示/隐藏加载动画
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

// 显示消息提示
function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('messageContainer');
    
    // 清除所有现有消息，确保只显示一个
    messageContainer.innerHTML = '';
    
    const toastId = 'toast-' + Date.now();

    const toastDiv = document.createElement('div');
    toastDiv.id = toastId;
    toastDiv.className = `message-toast ${type}`;

    // 根据类型设置图标
    let icon = 'bi-info-circle';
    let title = '提示';
    switch (type) {
        case 'success':
            icon = 'bi-check-circle';
            title = '成功';
            break;
        case 'danger':
            icon = 'bi-exclamation-triangle';
            title = '错误';
            break;
        case 'warning':
            icon = 'bi-exclamation-triangle';
            title = '警告';
            break;
        case 'info':
            icon = 'bi-info-circle';
            title = '信息';
            break;
    }

    toastDiv.innerHTML = `
        <div class="toast-header">
            <i class="bi ${icon} me-2"></i>
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close" onclick="hideMessage('${toastId}')"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    messageContainer.appendChild(toastDiv);

    // 触发显示动画
    setTimeout(() => {
        toastDiv.classList.add('show');
    }, 100);

    // 自动隐藏
    setTimeout(() => {
        hideMessage(toastId);
    }, 5000);
}

// 隐藏消息提示
function hideMessage(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// 自定义确认对话框
function showCustomConfirm(message, title = '确认操作', type = 'warning') {
    return new Promise((resolve) => {
        const modalTitle = document.getElementById('confirmModalTitle');
        const modalIcon = document.getElementById('confirmModalIcon');
        const modalMessage = document.getElementById('confirmModalMessage');
        const okBtn = document.getElementById('confirmModalOkBtn');

        // 设置标题
        modalTitle.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${title}`;

        // 设置图标
        if (type === 'danger') {
            modalIcon.innerHTML = '<i class="danger-icon bi bi-exclamation-triangle-fill"></i>';
        } else {
            modalIcon.innerHTML = '<i class="warning-icon bi bi-exclamation-triangle-fill"></i>';
        }

        // 设置消息内容
        modalMessage.innerHTML = message;

        // 移除之前的事件监听器
        const newOkBtn = okBtn.cloneNode(true);
        okBtn.parentNode.replaceChild(newOkBtn, okBtn);

        // 添加新的事件监听器
        newOkBtn.addEventListener('click', () => {
            customConfirmModal.hide();
            resolve(true);
        });

        // 处理取消操作
        const handleCancel = () => {
            customConfirmModal.hide();
            resolve(false);
        };

        // 绑定取消事件
        document.querySelector('#customConfirmModal .btn-cancel').onclick = handleCancel;
        document.querySelector('#customConfirmModal .btn-close').onclick = handleCancel;

        // 显示对话框
        customConfirmModal.show();
    });
}

// 文件大小格式化
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
} 