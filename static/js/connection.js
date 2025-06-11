/* 连接管理模块 */

// SSH连接
async function connectSSH() {
    const hostname = document.getElementById('hostname').value;
    const username = document.getElementById('username').value;
    const port = document.getElementById('port').value;
    const isKeyAuth = document.getElementById('authKey').checked;

    if (!hostname || !username) {
        showMessage('请填写服务器地址和用户名', 'warning');
        return;
    }

    let response;
    showLoading();

    try {
        if (isKeyAuth) {
            // SSH密钥认证
            const privateKeyPath = document.getElementById('privateKeyPath').value;
            const keyPassphrase = document.getElementById('keyPassphrase').value;

            if (!privateKeyPath) {
                hideLoading();
                showMessage('请选择SSH私钥文件', 'warning');
                return;
            }

            response = await fetch('/connect_with_key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    hostname: hostname,
                    username: username,
                    private_key_path: privateKeyPath,
                    port: parseInt(port),
                    passphrase: keyPassphrase || null
                })
            });
        } else {
            // 密码认证
            const password = document.getElementById('password').value;

            if (!password) {
                hideLoading();
                showMessage('请输入密码', 'warning');
                return;
            }

            response = await fetch('/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    hostname: hostname,
                    username: username,
                    password: password,
                    port: parseInt(port)
                })
            });
        }

        const result = await response.json();
        hideLoading();

        if (result.success) {
            updateConnectionStatus(true);
            updateRemoteFunctionAvailability(); // 更新远程功能可用性
            showMessage(result.message, 'success');

            // 刷新连接历史
            refreshConnectionHistory();
        } else {
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        hideLoading();
        showMessage('连接请求失败: ' + error.message, 'danger');
    }
}

// 断开SSH连接
async function disconnectSSH() {
    try {
        const response = await fetch('/disconnect', {
            method: 'POST'
        });
        const result = await response.json();
        updateConnectionStatus(false);
        updateRemoteFunctionAvailability(); // 更新远程功能可用性
        showMessage(result.message, 'info');
    } catch (error) {
        showMessage('断开连接失败: ' + error.message, 'danger');
    }
}

// 切换认证方式
function toggleAuthMethod() {
    const isKeyAuth = document.getElementById('authKey').checked;
    const passwordAuth = document.getElementById('passwordAuth');
    const keyAuth = document.getElementById('keyAuth');

    if (isKeyAuth) {
        passwordAuth.style.display = 'none';
        keyAuth.style.display = 'block';
    } else {
        passwordAuth.style.display = 'block';
        keyAuth.style.display = 'none';
    }
}

// 刷新连接历史
async function refreshConnectionHistory() {
    try {
        const response = await fetch('/connection_history');
        const result = await response.json();

        if (result.success) {
            displayConnectionHistory(result.connections);
        } else {
            console.error('获取连接历史失败:', result.message);
            displayConnectionHistory([]);
        }
    } catch (error) {
        console.error('获取连接历史失败:', error);
        displayConnectionHistory([]);
    }
}

// 显示连接历史
function displayConnectionHistory(connections) {
    const container = document.getElementById('connectionHistoryList');

    if (!connections || connections.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-clock-history text-muted" style="font-size: 2rem;"></i>
                <p class="text-muted mt-2">暂无连接历史</p>
            </div>
        `;
        return;
    }

    let html = '';
    connections.forEach((conn, index) => {
        const isRecent = index === 0; // 最新的连接标记为recent
        const authIcon = conn.auth_type === 'key' ? 'bi-key' : 'bi-shield-lock';
        const authText = conn.auth_type === 'key' ? 'SSH密钥' : '密码';
        const authClass = conn.auth_type === 'key' ? 'bg-info' : 'bg-primary';

        const lastConnected = new Date(conn.last_connected);
        const timeAgo = getTimeAgo(lastConnected);

        html += `
            <div class="connection-item ${isRecent ? 'recent' : ''}">
                <div class="connection-info">
                    <div class="connection-details">
                        <div class="connection-title">
                            ${conn.description || conn.id}
                        </div>
                        <div class="connection-meta">
                            <i class="bi bi-laptop"></i> ${conn.hostname}:${conn.port}
                            <span class="mx-2">|</span>
                            <i class="bi bi-person"></i> ${conn.username}
                            <span class="mx-2">|</span>
                            <span class="badge auth-type-badge ${authClass}">
                                <i class="bi ${authIcon}"></i> ${authText}
                            </span>
                        </div>
                        <div class="connection-meta">
                            <i class="bi bi-clock"></i> ${timeAgo}
                            <span class="mx-2">|</span>
                            <i class="bi bi-graph-up"></i> 连接 ${conn.connect_count || 1} 次
                        </div>
                    </div>
                    <div class="connection-actions">
                        <button class="btn btn-sm btn-success" onclick="connectFromHistory('${conn.id}')" title="快速连接">
                            <i class="bi bi-play"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="editConnectionDescription('${conn.id}', '${conn.description || ''}')" title="编辑描述">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="removeConnectionHistory('${conn.id}')" title="删除历史">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// 计算时间差
function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
        return diffMins <= 0 ? '刚刚' : `${diffMins} 分钟前`;
    } else if (diffHours < 24) {
        return `${diffHours} 小时前`;
    } else if (diffDays < 30) {
        return `${diffDays} 天前`;
    } else {
        return date.toLocaleDateString('zh-CN');
    }
}

// 从历史记录连接
async function connectFromHistory(connectionId) {
    try {
        // 先获取连接历史
        const response = await fetch('/connection_history');
        const result = await response.json();

        if (!result.success) {
            showMessage('获取连接信息失败', 'danger');
            return;
        }

        const connection = result.connections.find(conn => conn.id === connectionId);
        if (!connection) {
            showMessage('连接信息不存在', 'danger');
            return;
        }

        // 填充连接表单
        document.getElementById('hostname').value = connection.hostname;
        document.getElementById('username').value = connection.username;
        document.getElementById('port').value = connection.port;
        document.getElementById('connectionDescription').value = connection.description || '';

        // 根据认证类型切换认证方式
        if (connection.auth_type === 'key') {
            document.getElementById('authKey').checked = true;
            document.getElementById('authPassword').checked = false;
            toggleAuthMethod();

            // 提示用户需要选择私钥文件
            showMessage('已填充连接信息，请选择SSH私钥文件后点击连接', 'info');
        } else {
            document.getElementById('authPassword').checked = true;
            document.getElementById('authKey').checked = false;
            toggleAuthMethod();

            // 提示用户需要输入密码
            showMessage('已填充连接信息，请输入密码后点击连接', 'info');
        }

    } catch (error) {
        showMessage('连接失败: ' + error.message, 'danger');
    }
}

// 删除连接历史
async function removeConnectionHistory(connectionId) {
    const confirmed = await showCustomConfirm(
        '确定要删除这个连接历史记录吗？',
        '删除连接历史',
        'warning'
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch('/remove_connection_history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                connection_id: connectionId
            })
        });

        const result = await response.json();
        if (result.success) {
            showMessage('连接历史已删除', 'success');
            refreshConnectionHistory();
        } else {
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        showMessage('删除连接历史失败: ' + error.message, 'danger');
    }
}

// 编辑连接描述
async function editConnectionDescription(connectionId, currentDescription) {
    const newDescription = prompt('请输入新的描述：', currentDescription);

    if (newDescription === null) {
        return; // 用户取消
    }

    try {
        const response = await fetch('/update_connection_description', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                connection_id: connectionId,
                description: newDescription
            })
        });

        const result = await response.json();
        if (result.success) {
            showMessage('连接描述已更新', 'success');
            refreshConnectionHistory();
        } else {
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        showMessage('更新连接描述失败: ' + error.message, 'danger');
    }
}

// 浏览私钥文件
function browsePrivateKey() {
    // 简单的文件路径提示
    const path = prompt('请输入SSH私钥文件的完整路径：\n\n常见路径示例：\n- Windows: C:\\Users\\用户名\\.ssh\\id_rsa\n- Linux/Mac: ~/.ssh/id_rsa');
    if (path) {
        document.getElementById('privateKeyPath').value = path;
    }
} 