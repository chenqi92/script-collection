/* 文件编辑器模块 */

// 加载文件内容
async function loadFileContent() {
    const filePath = document.getElementById('editorFilePath').value;

    if (!filePath) {
        showMessage('请输入文件路径', 'warning');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/read_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: filePath
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            currentFileContent = result.content;
            currentFilePath = filePath;

            document.getElementById('fileEditor').value = result.content;
            document.getElementById('fileInfo').textContent = `已加载: ${filePath}`;

            // 自动检测文件类型
            autoDetectFileType(filePath);
            updateEditorLanguage();

            showMessage('文件加载成功', 'success');
            addOperationLog('文件编辑', `成功加载文件: ${filePath}`, 'success');
        } else {
            showMessage(result.message, 'danger');
            addOperationLog('文件编辑', `加载失败: ${result.message}`, 'error');
        }
    } catch (error) {
        hideLoading();
        showMessage('加载文件失败: ' + error.message, 'danger');
        addOperationLog('文件编辑', `加载异常: ${error.message}`, 'error');
    }
}

// 保存文件内容
async function saveFileContent() {
    const filePath = document.getElementById('editorFilePath').value;
    const content = document.getElementById('fileEditor').value;

    if (!filePath) {
        showMessage('请输入文件路径', 'warning');
        return;
    }

    const confirmed = await showCustomConfirm(
        `确定要保存文件吗？<br><br><code>${filePath}</code><br><br><small class="text-muted">系统会自动创建备份文件 (.backup)</small>`,
        '保存文件确认',
        'info'
    );

    if (!confirmed) {
        return;
    }

    showLoading();

    try {
        const response = await fetch('/write_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: filePath,
                content: content
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            currentFileContent = content;
            showMessage('文件保存成功', 'success');
            addOperationLog('文件编辑', `成功保存文件: ${filePath}`, 'success');
        } else {
            showMessage(result.message, 'danger');
            addOperationLog('文件编辑', `保存失败: ${result.message}`, 'error');
        }
    } catch (error) {
        hideLoading();
        showMessage('保存文件失败: ' + error.message, 'danger');
        addOperationLog('文件编辑', `保存异常: ${error.message}`, 'error');
    }
}

// 自动检测文件类型
function autoDetectFileType(filePath) {
    const extension = filePath.split('.').pop().toLowerCase();
    const fileTypeSelect = document.getElementById('fileType');

    const typeMap = {
        'yaml': 'yaml',
        'yml': 'yaml',
        'json': 'json',
        'xml': 'xml',
        'ini': 'ini',
        'conf': 'ini',
        'config': 'ini',
        'sh': 'shell',
        'bash': 'shell',
        'py': 'python',
        'js': 'javascript',
        'css': 'css',
        'html': 'html',
        'htm': 'html',
        'sql': 'sql',
        'md': 'markdown',
        'txt': 'text'
    };

    const detectedType = typeMap[extension] || 'text';
    fileTypeSelect.value = detectedType;
}

// 更新编辑器语言样式
function updateEditorLanguage() {
    const fileType = document.getElementById('fileType').value;
    const editor = document.getElementById('fileEditor');

    // 移除所有语法高亮类
    editor.className = 'file-editor';

    // 添加对应的语法高亮类
    if (fileType !== 'text') {
        editor.classList.add(`syntax-${fileType}`);
    }
}

// 格式化内容
function formatContent() {
    const fileType = document.getElementById('fileType').value;
    const editor = document.getElementById('fileEditor');
    let content = editor.value;

    try {
        switch (fileType) {
            case 'json':
                const jsonObj = JSON.parse(content);
                content = JSON.stringify(jsonObj, null, 2);
                break;
            case 'yaml':
                // 简单的YAML格式化（基础版本）
                content = content.split('\n').map(line => line.trim()).join('\n');
                break;
            default:
                showMessage('当前文件类型不支持自动格式化', 'info');
                return;
        }

        editor.value = content;
        showMessage('内容格式化成功', 'success');
    } catch (error) {
        showMessage('格式化失败: 内容格式错误', 'danger');
    }
}

// 初始化编辑器事件
function initializeEditorEvents() {
    const editor = document.getElementById('fileEditor');
    const cursorInfo = document.getElementById('cursorInfo');

    if (editor && cursorInfo) {
        editor.addEventListener('keyup', updateCursorInfo);
        editor.addEventListener('click', updateCursorInfo);

        function updateCursorInfo() {
            const lines = editor.value.substring(0, editor.selectionStart).split('\n');
            const line = lines.length;
            const col = lines[lines.length - 1].length + 1;
            cursorInfo.textContent = `行: ${line}, 列: ${col}`;
        }
    }
}