/* 工具模块 */

// 生成目录树
async function generateTree() {
    const directory = document.getElementById('treeDirectory').value || null;
    const applyGitignore = document.getElementById('applyGitignore').checked;
    const excludeFiles = document.getElementById('excludeFiles').checked;
    const maxLevel = document.getElementById('maxLevel').value || null;

    const directoryText = directory || '当前目录';
    const options = [];
    if (applyGitignore) options.push('应用.gitignore');
    if (excludeFiles) options.push('仅显示目录');
    if (maxLevel) options.push(`最大层级: ${maxLevel}`);
    const optionsText = options.length > 0 ? ` (${options.join(', ')})` : '';

    showLoading();
    addOperationLog('目录树生成', `开始生成目录树: ${directoryText}${optionsText}`, 'warning');

    try {
        const response = await fetch('/tree', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                directory: directory,
                apply_gitignore: applyGitignore,
                exclude_files: excludeFiles,
                max_level: maxLevel ? parseInt(maxLevel) : null
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            // 隐藏其他功能的结果面板
            document.getElementById('resultsPanel').style.display = 'none';

            document.getElementById('treeOutput').textContent = result.result;
            document.getElementById('treeOutputPanel').style.display = 'block';

            // 计算树的行数作为复杂度指标
            const lineCount = result.result.split('\n').length;
            addOperationLog('目录树生成', `成功生成目录树: ${lineCount} 行`, 'success');
            showMessage('目录树生成成功！', 'success');
        } else {
            addOperationLog('目录树生成', `生成失败: ${result.result}`, 'error');
            showMessage(result.result, 'danger');
        }
    } catch (error) {
        hideLoading();
        addOperationLog('目录树生成', `生成异常: ${error.message}`, 'error');
        showMessage('生成目录树失败: ' + error.message, 'danger');
    }
}

// 清理空目录
async function cleanEmptyDirectories() {
    const directory = document.getElementById('cleanDirectory').value || null;
    const directoryText = directory || '当前工作目录';

    const confirmed = await showCustomConfirm(
        `确定要清理以下目录中的空目录吗？<br><br><code>${directoryText}</code><br><br><strong>此操作会删除所有空目录，操作不可撤销！</strong>`,
        '清理空目录确认',
        'warning'
    );

    if (!confirmed) {
        return;
    }

    showLoading();
    addOperationLog('空目录清理', `开始清理空目录: ${directoryText}`, 'warning');

    try {
        const response = await fetch('/clean_empty_dirs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                directory: directory
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            // 隐藏其他功能的结果面板
            document.getElementById('resultsPanel').style.display = 'none';
            document.getElementById('treeOutputPanel').style.display = 'none';

            // 提取清理的目录数量
            const cleanedDirs = result.cleaned_directories || [];
            const cleanedCount = cleanedDirs.length;

            if (cleanedCount > 0) {
                // 记录撤销数据
                const undoData = {
                    type: 'clean_empty_dirs',
                    data: cleanedDirs
                };

                addOperationLog(
                    '空目录清理',
                    `成功清理 ${cleanedCount} 个空目录`,
                    'success',
                    undoData
                );

                // 详细记录清理的目录
                cleanedDirs.slice(0, 10).forEach(dir => {
                    addOperationLog('清理详情', `已删除空目录: ${dir}`, 'success');
                });

                if (cleanedDirs.length > 10) {
                    addOperationLog('清理详情', `还有 ${cleanedDirs.length - 10} 个目录...`, 'success');
                }
            } else {
                addOperationLog('空目录清理', '没有发现需要清理的空目录', 'success');
            }

            showMessage(result.result, 'success');
        } else {
            addOperationLog('空目录清理', `清理失败: ${result.result}`, 'error');
            showMessage(result.result, 'danger');
        }
    } catch (error) {
        hideLoading();
        addOperationLog('空目录清理', `清理异常: ${error.message}`, 'error');
        showMessage('清理空目录失败: ' + error.message, 'danger');
    }
}

// 比较路径
async function comparePaths() {
    const path1 = document.getElementById('path1').value;
    const path2 = document.getElementById('path2').value;
    const similarityThreshold = parseFloat(document.getElementById('similarityThreshold').value);

    if (!path1 || !path2) {
        showMessage('请输入两个有效的路径', 'warning');
        return;
    }

    showLoading();
    addOperationLog('目录比较', `开始比较: ${path1} 与 ${path2} (相似度阈值: ${similarityThreshold}%)`, 'warning');

    try {
        const response = await fetch('/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path1: path1,
                path2: path2,
                threshold: similarityThreshold
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            // 隐藏其他功能的结果面板
            document.getElementById('treeOutputPanel').style.display = 'none';

            const duplicateCount = result.duplicates ? result.duplicates.length : 0;
            addOperationLog(
                '目录比较',
                `比较完成: 发现 ${duplicateCount} 个重复/相似项`,
                duplicateCount > 0 ? 'warning' : 'success'
            );

            displayDuplicates(result.duplicates);
            showMessage(result.message, 'success');
        } else {
            addOperationLog('目录比较', `比较失败: ${result.message}`, 'error');
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        hideLoading();
        addOperationLog('目录比较', `比较异常: ${error.message}`, 'error');
        showMessage('比较请求失败: ' + error.message, 'danger');
    }
}

// 显示重复文件
function displayDuplicates(duplicates) {
    duplicatesData = duplicates; // 保存数据供批量操作使用
    const resultsPanel = document.getElementById('resultsPanel');
    const duplicatesList = document.getElementById('duplicatesList');
    const duplicateCount = document.getElementById('duplicateCount');
    const batchControls = document.getElementById('batchControls');

    // 重置全选状态
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
    }

    const exactCount = duplicates.filter(d => d.match_type === 'exact').length;
    const similarCount = duplicates.filter(d => d.match_type === 'similar').length;
    duplicateCount.textContent = `找到 ${exactCount} 个完全重复项和 ${similarCount} 个相似项`;

    if (duplicates.length === 0) {
        duplicatesList.innerHTML = '<div class="alert alert-info">没有找到重复的文件或文件夹</div>';
        batchControls.style.display = 'none';
    } else {
        let html = '';
        duplicates.forEach((item, index) => {
            const itemClass = item.match_type === 'exact' ? 'duplicate-item' : 'similar-item';
            const similarityBadge = item.match_type === 'similar' ?
                `<span class="badge bg-warning text-dark ms-2">相似度: ${Math.round(item.similarity * 100)}%</span>` : '';

            html += `
                <div class="card mb-3 ${itemClass}">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-1">
                                <input type="checkbox" class="form-check-input item-checkbox" 
                                       data-index="${index}" onchange="updateSelectedCount()">
                            </div>
                            <div class="col-md-5">
                                <h6 class="card-title">
                                    <i class="bi bi-${item.type === 'file' ? 'file-earmark' : 'folder'}"></i>
                                    ${item.name}
                                    ${similarityBadge}
                                </h6>
                                <small class="text-muted">类型: ${item.type === 'file' ? '文件' : '目录'}</small>
                                ${item.type === 'file' && typeof item.size === 'number' ? '<br><small class="text-muted">大小: ' + formatFileSize(item.size) + '</small>' : ''}
                                ${item.type === 'file' && typeof item.size === 'string' ? '<br><small class="text-muted">大小: ' + item.size + '</small>' : ''}
                            </div>
                            <div class="col-md-6">
                                <div class="row">
                                    <div class="col-6">
                                        <div class="card bg-light">
                                            <div class="card-body p-2">
                                                <small class="text-muted d-block">路径 1:</small>
                                                <code class="small">${item.path1}</code>
                                                <br><small class="text-muted">修改时间: ${item.modified1}</small>
                                                <br>
                                                <button class="btn btn-danger btn-sm mt-2" onclick="deleteFile('${item.path1}', ${index})">
                                                    <i class="bi bi-trash"></i> 删除
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="card bg-light">
                                            <div class="card-body p-2">
                                                <small class="text-muted d-block">路径 2:</small>
                                                <code class="small">${item.path2}</code>
                                                <br><small class="text-muted">修改时间: ${item.modified2}</small>
                                                <br>
                                                <button class="btn btn-danger btn-sm mt-2" onclick="deleteFile('${item.path2}', ${index})">
                                                    <i class="bi bi-trash"></i> 删除
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        duplicatesList.innerHTML = html;
        batchControls.style.display = 'block';

        // 设置全选/全不选事件
        document.getElementById('selectAll').onchange = function () {
            const checkboxes = document.querySelectorAll('.item-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            updateSelectedCount();
        };
    }

    resultsPanel.style.display = 'block';
}

// 删除文件
async function deleteFile(path, index) {
    const confirmed = await showCustomConfirm(
        `确定要删除以下文件吗？<br><br><code>${path}</code><br><br><strong>此操作不可撤销！</strong>`,
        '删除文件确认',
        'danger'
    );

    if (!confirmed) {
        return;
    }

    showLoading();
    addOperationLog('文件删除', `开始删除: ${path}`, 'warning');

    try {
        const response = await fetch('/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: path
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            addOperationLog('文件删除', `成功删除: ${path}`, 'success');
            showMessage(result.message, 'success');
            // 重新比较以更新列表
            comparePaths();
        } else {
            addOperationLog('文件删除', `删除失败: ${path} - ${result.message}`, 'error');
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        hideLoading();
        addOperationLog('文件删除', `删除异常: ${path} - ${error.message}`, 'error');
        showMessage('删除请求失败: ' + error.message, 'danger');
    }
}

// 更新选中计数
function updateSelectedCount() {
    const checked = document.querySelectorAll('.item-checkbox:checked').length;
    const selectedCountElement = document.getElementById('selectedCount');
    if (selectedCountElement) {
        selectedCountElement.textContent = checked;
    }
}

// 获取选中的路径
function getSelectedPaths(pathType) {
    const checkedBoxes = document.querySelectorAll('.item-checkbox:checked');
    const paths = [];
    checkedBoxes.forEach(checkbox => {
        const index = parseInt(checkbox.dataset.index);
        const item = duplicatesData[index];
        if (pathType === 'path1') {
            paths.push(item.path1);
        } else {
            paths.push(item.path2);
        }
    });
    return paths;
}

// 批量删除路径1
async function batchDeletePath1() {
    const paths = getSelectedPaths('path1');
    if (paths.length === 0) {
        showMessage('请先选择要删除的项目', 'warning');
        return;
    }

    const pathsPreview = paths.slice(0, 5).map(p => `<code>${p}</code>`).join('<br>');
    const moreText = paths.length > 5 ? `<br><small class="text-muted">还有 ${paths.length - 5} 个项目...</small>` : '';

    const confirmed = await showCustomConfirm(
        `确定要删除路径1中的 <strong>${paths.length}</strong> 个项目吗？<br><br>${pathsPreview}${moreText}<br><br><strong>此操作不可撤销！</strong>`,
        '批量删除确认',
        'danger'
    );

    if (!confirmed) {
        return;
    }

    await performBatchDelete(paths, 'path1');
}

// 批量删除路径2
async function batchDeletePath2() {
    const paths = getSelectedPaths('path2');
    if (paths.length === 0) {
        showMessage('请先选择要删除的项目', 'warning');
        return;
    }

    const pathsPreview = paths.slice(0, 5).map(p => `<code>${p}</code>`).join('<br>');
    const moreText = paths.length > 5 ? `<br><small class="text-muted">还有 ${paths.length - 5} 个项目...</small>` : '';

    const confirmed = await showCustomConfirm(
        `确定要删除路径2中的 <strong>${paths.length}</strong> 个项目吗？<br><br>${pathsPreview}${moreText}<br><br><strong>此操作不可撤销！</strong>`,
        '批量删除确认',
        'danger'
    );

    if (!confirmed) {
        return;
    }

    await performBatchDelete(paths, 'path2');
}

// 执行批量删除
async function performBatchDelete(paths, pathType = 'unknown') {
    showLoading();
    addOperationLog('批量删除', `开始批量删除 ${pathType} 中的 ${paths.length} 个项目`, 'warning');

    try {
        const response = await fetch('/batch_delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                paths: paths
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            const successCount = result.summary.success;
            const failedCount = result.summary.failed;

            addOperationLog(
                '批量删除',
                `删除完成: 成功 ${successCount} 个，失败 ${failedCount} 个`,
                failedCount > 0 ? 'warning' : 'success'
            );

            showMessage(result.message, failedCount > 0 ? 'warning' : 'success');

            // 记录详细结果到操作日志
            result.results.forEach(r => {
                if (!r.success) {
                    addOperationLog('删除失败', `${r.path}: ${r.message}`, 'error');
                }
            });

            // 重新比较以更新列表
            comparePaths();
        } else {
            addOperationLog('批量删除', `批量删除失败: ${result.message}`, 'error');
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        hideLoading();
        addOperationLog('批量删除', `批量删除异常: ${error.message}`, 'error');
        showMessage('批量删除请求失败: ' + error.message, 'danger');
    }
} 