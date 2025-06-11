/* 操作日志模块 */

// 添加操作日志
function addOperationLog(operation, description, status = 'success', undoData = null) {
    const timestamp = new Date().toLocaleString();
    const logEntry = {
        id: Date.now(),
        operation,
        description,
        status,
        timestamp,
        undoData
    };

    operationHistory.unshift(logEntry);

    // 限制历史记录数量
    if (operationHistory.length > 50) {
        operationHistory = operationHistory.slice(0, 50);
    }

    updateLogDisplay();
    updateUndoButton();

    // 自动显示日志面板（如果有新的操作）
    if (!isLogVisible && status !== 'error') {
        showOperationLog();
    }
}

// 更新日志显示
function updateLogDisplay() {
    const logContent = document.getElementById('logContent');
    if (!logContent) return;

    logContent.innerHTML = '';

    operationHistory.forEach((entry, index) => {
        const logItem = document.createElement('div');
        logItem.className = `log-item ${entry.status}`;

        const statusIcon = entry.status === 'success' ? 'bi-check-circle' :
            entry.status === 'error' ? 'bi-x-circle' : 'bi-exclamation-triangle';

        logItem.innerHTML = `
            <div>
                <i class="bi ${statusIcon}"></i>
                <strong>${entry.operation}:</strong> ${entry.description}
                <small class="text-muted d-block">${entry.timestamp}</small>
            </div>
            ${entry.undoData && index === 0 ?
            `<button class="btn btn-sm undo-btn" onclick="undoOperation(${entry.id})" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">
                        <i class="bi bi-arrow-counterclockwise"></i>
                    </button>` : ''
        }
        `;

        logContent.appendChild(logItem);
    });

    // 更新浮动按钮的计数
    updateFloatingLogButton();
}

// 更新撤销按钮状态
function updateUndoButton() {
    const undoBtn = document.getElementById('undoBtn');
    if (undoBtn) {
        const hasUndoableOperation = operationHistory.length > 0 && operationHistory[0].undoData;
        undoBtn.disabled = !hasUndoableOperation;
    }
}

// 显示操作日志
function showOperationLog() {
    const logPanel = document.getElementById('operationLog');
    logPanel.style.display = 'block';
    isLogVisible = true;
    updateFloatingLogButton();
}

// 隐藏操作日志
function hideOperationLog() {
    const logPanel = document.getElementById('operationLog');
    logPanel.style.display = 'none';
    isLogVisible = false;
    updateFloatingLogButton();
}

// 更新浮动日志按钮
function updateFloatingLogButton() {
    const floatingBtn = document.getElementById('floatingLogBtn');
    const logCount = document.getElementById('logCount');

    if (isLogVisible) {
        floatingBtn.style.display = 'none';
    } else {
        floatingBtn.style.display = 'flex';

        if (operationHistory.length > 0) {
            logCount.textContent = operationHistory.length;
            logCount.style.display = 'block';
        } else {
            logCount.style.display = 'none';
        }
    }
}

// 切换操作日志显示
function toggleOperationLog() {
    if (isLogVisible) {
        hideOperationLog();
    } else {
        showOperationLog();
    }
}

// 清空操作日志
function clearOperationLog() {
    operationHistory = [];
    updateLogDisplay();
    updateUndoButton();
    updateFloatingLogButton();
}

// 撤销最后一个操作
function undoLastOperation() {
    if (operationHistory.length > 0 && operationHistory[0].undoData) {
        undoOperation(operationHistory[0].id);
    }
}

// 撤销指定操作
function undoOperation(operationId) {
    const operation = operationHistory.find(op => op.id === operationId);
    if (!operation || !operation.undoData) {
        showMessage('无法撤销此操作', 'error');
        return;
    }

    // 执行撤销操作
    performUndo(operation.undoData)
        .then(() => {
            addOperationLog('撤销操作', `已撤销: ${operation.description}`, 'success');
            // 从历史记录中移除已撤销的操作
            operationHistory = operationHistory.filter(op => op.id !== operationId);
            updateLogDisplay();
            updateUndoButton();
            showMessage('操作已成功撤销', 'success');
        })
        .catch(error => {
            addOperationLog('撤销失败', `撤销操作失败: ${error.message}`, 'error');
            showMessage(`撤销操作失败: ${error.message}`, 'error');
        });
}

// 执行撤销操作
function performUndo(undoData) {
    return new Promise((resolve, reject) => {
        const {type, data} = undoData;

        switch (type) {
            case 'delete_files':
                // 恢复已删除的文件（理论上需要备份机制）
                reject(new Error('文件删除操作无法撤销'));
                break;

            case 'clean_empty_dirs':
                // 重新创建已删除的空目录
                restoreEmptyDirectories(data)
                    .then(resolve)
                    .catch(reject);
                break;

            default:
                reject(new Error('不支持的撤销操作类型'));
        }
    });
}

// 恢复空目录
function restoreEmptyDirectories(directories) {
    return fetch('/restore_directories', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            directories: directories,
            mode: currentMode
        })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                throw new Error(data.message || '恢复目录失败');
            }
        });
} 