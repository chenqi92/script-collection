/* 批量操作模块 */

// 切换重命名输入框
function toggleRenameInputs() {
    const renameType = document.getElementById('renameType').value;
    const regexInputs = document.getElementById('regexInputs');
    const customTextInputs = document.getElementById('customTextInputs');

    // 隐藏所有输入框
    regexInputs.style.display = 'none';
    customTextInputs.style.display = 'none';

    if (renameType === 'regex') {
        regexInputs.style.display = 'block';
    } else if (renameType === 'add_custom_prefix' || renameType === 'add_custom_suffix') {
        customTextInputs.style.display = 'block';
    }
}

// 执行批量重命名
async function executeRename() {
    const path = document.getElementById('renamePath').value;
    const renameType = document.getElementById('renameType').value;
    const pattern = document.getElementById('regexPattern').value;
    const replacement = document.getElementById('regexReplacement').value;
    const customText = document.getElementById('customText').value;

    if (!path) {
        showMessage('请输入目标目录路径', 'warning');
        return;
    }

    if (renameType === 'regex' && !pattern) {
        showMessage('使用正则表达式时，请输入正则表达式模式', 'warning');
        return;
    }

    if ((renameType === 'add_custom_prefix' || renameType === 'add_custom_suffix') && !customText) {
        showMessage('使用自定义前缀/后缀时，请输入自定义文本', 'warning');
        return;
    }

    const confirmed = await showCustomConfirm(
        `确定要对目录 <code>${path}</code> 中的文件进行批量重命名吗？<br><br><strong>重命名类型:</strong> ${getRenameTypeText(renameType)}<br><br><strong>此操作不可撤销！</strong>`,
        '批量重命名确认',
        'warning'
    );

    if (!confirmed) {
        return;
    }

    showLoading();
    addOperationLog('批量重命名', `开始重命名: ${path} (${getRenameTypeText(renameType)})`, 'warning');

    try {
        const response = await fetch('/batch_rename', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: path,
                rename_type: renameType,
                pattern: pattern,
                replacement: replacement,
                custom_text: customText
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            const successCount = result.results ? result.results.filter(r => r.success).length : 0;
            const failedCount = result.results ? result.results.filter(r => !r.success).length : 0;

            addOperationLog(
                '批量重命名',
                `重命名完成: 成功 ${successCount} 个，失败 ${failedCount} 个`,
                failedCount > 0 ? 'warning' : 'success'
            );

            displayOperationResults('重命名结果', result.results, result.message);
            showMessage(result.message, 'success');
        } else {
            addOperationLog('批量重命名', `重命名失败: ${result.message}`, 'error');
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        hideLoading();
        addOperationLog('批量重命名', `重命名异常: ${error.message}`, 'error');
        showMessage('批量重命名请求失败: ' + error.message, 'danger');
    }
}

// 执行目录整理
async function executeOrganize() {
    const path = document.getElementById('organizePath').value;
    const organizeType = document.getElementById('organizeType').value;

    if (!path) {
        showMessage('请输入目标目录路径', 'warning');
        return;
    }

    const confirmed = await showCustomConfirm(
        `确定要对目录 <code>${path}</code> 执行整理操作吗？<br><br><strong>整理类型:</strong> ${getOrganizeTypeText(organizeType)}<br><br><strong>此操作不可撤销！</strong>`,
        '目录整理确认',
        'warning'
    );

    if (!confirmed) {
        return;
    }

    showLoading();
    addOperationLog('目录整理', `开始整理: ${path} (${getOrganizeTypeText(organizeType)})`, 'warning');

    try {
        const response = await fetch('/organize_directory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: path,
                organize_type: organizeType
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            const successCount = result.results ? result.results.filter(r => r.success).length : 0;
            const failedCount = result.results ? result.results.filter(r => !r.success).length : 0;

            addOperationLog(
                '目录整理',
                `整理完成: 成功 ${successCount} 个，失败 ${failedCount} 个`,
                failedCount > 0 ? 'warning' : 'success'
            );

            displayOperationResults('整理结果', result.results, result.message);
            showMessage(result.message, 'success');
        } else {
            addOperationLog('目录整理', `整理失败: ${result.message}`, 'error');
            showMessage(result.message, 'danger');
        }
    } catch (error) {
        hideLoading();
        addOperationLog('目录整理', `整理异常: ${error.message}`, 'error');
        showMessage('目录整理请求失败: ' + error.message, 'danger');
    }
}

// 显示操作结果
function displayOperationResults(title, results, message) {
    const resultsPanel = document.getElementById('resultsPanel');
    const resultsTitle = document.getElementById('resultsTitle');
    const duplicateCount = document.getElementById('duplicateCount');
    const duplicatesList = document.getElementById('duplicatesList');
    const batchControls = document.getElementById('batchControls');

    // 更新标题和计数
    resultsTitle.innerHTML = `<i class="bi bi-check-circle"></i> ${title}`;
    duplicateCount.textContent = message;

    // 隐藏批量控制区域（不适用于重命名和整理操作）
    batchControls.style.display = 'none';

    // 生成结果列表
    let html = '';
    results.forEach((item, index) => {
        const statusIcon = item.success ? 'bi-check-circle text-success' : 'bi-x-circle text-danger';
        const cardClass = item.success ? 'border-success' : 'border-danger';

        html += `
            <div class="card mb-2 ${cardClass}">
                <div class="card-body p-3">
                    <div class="row align-items-center">
                        <div class="col-md-1">
                            <i class="bi ${statusIcon}"></i>
                        </div>
                        <div class="col-md-11">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
        `;

        if (item.old_name !== undefined) {
            // 重命名结果
            html += `
                                    <strong>原名称:</strong> ${item.old_name}<br>
                                    <strong>新名称:</strong> ${item.new_name}<br>
            `;
        } else if (item.filename !== undefined) {
            // 文件夹创建结果
            html += `
                                    <strong>文件:</strong> ${item.filename}<br>
                                    <strong>文件夹:</strong> ${item.folder_name}<br>
            `;
        } else if (item.dir_name !== undefined) {
            // 目录清理结果
            html += `
                                    <strong>目录:</strong> ${item.dir_name}<br>
            `;
        }

        html += `
                                    <small class="text-muted">${item.message}</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    if (html === '') {
        html = '<div class="alert alert-info">没有需要处理的项目</div>';
    }

    duplicatesList.innerHTML = html;
    resultsPanel.style.display = 'block';
}

// 获取重命名类型文本
function getRenameTypeText(type) {
    const typeMap = {
        'remove_number_prefix': '移除数字前缀',
        'add_sequence_prefix': '添加序号前缀',
        'add_sequence_suffix': '添加序号后缀',
        'add_custom_prefix': '添加自定义前缀',
        'add_custom_suffix': '添加自定义后缀',
        'remove_special_chars': '移除特殊字符',
        'to_lowercase': '转为小写',
        'to_uppercase': '转为大写',
        'space_to_underscore': '空格替换下划线',
        'underscore_to_space': '下划线替换空格',
        'date_prefix': '添加日期前缀',
        'capitalize_words': '首字母大写',
        'regex': '正则表达式'
    };
    return typeMap[type] || type;
}

// 获取整理类型文本
function getOrganizeTypeText(type) {
    const typeMap = {
        'create_folders_for_files': '为文件创建同名文件夹',
        'remove_empty_dirs': '移除空目录'
    };
    return typeMap[type] || type;
} 