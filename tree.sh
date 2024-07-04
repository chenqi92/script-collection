#!/bin/bash

# 获取当前脚本的名称
script_name=$(basename "$0")
output_file="tree_output.txt"

# 定义读取 .gitignore 文件的函数
read_gitignore() {
    local directory="$1"
    gitignore_file="$directory/.gitignore"
    if [[ -f "$gitignore_file" ]]; then
        # 读取 .gitignore 文件并排除注释和空行
        GITIGNORE_RULES=($(grep -Ev '^\s*#|^\s*$' "$gitignore_file"))
    else
        GITIGNORE_RULES=()
    fi
    # 将脚本名称和输出文件添加到排除列表
    GITIGNORE_RULES+=("$script_name" "$output_file")
}

# 检查文件或文件夹是否应该被忽略
is_excluded() {
    local path="$1"
    local relative_path="${path#$directory/}"
    local match_exclude=0  # 是否匹配到排除规则
    local match_include=0  # 是否匹配到包含规则（例外）

    # 转换为相对路径，并确保路径不以斜杠开头
    relative_path=$(echo "$relative_path" | sed 's/^\///')

    # 遍历 .gitignore 规则
    for rule in "${GITIGNORE_RULES[@]}"; do
        local original_rule="$rule"
        local is_inclusion=0  # 默认为排除规则
        if [[ "${rule:0:1}" == "!" ]]; then
            is_inclusion=1  # 如果是例外规则
            rule="${rule:1}"  # 移除开头的感叹号
        fi

        # 替换通配符 * 和 ?
        local pattern="${rule//\*/.*}"
        pattern="${pattern//\?/.}"

        # 根据规则中的斜杠位置构建不同的正则表达式
        if [[ "$rule" == /* ]]; then
            pattern="${pattern#/}"
            pattern="^$pattern($|/.*)$"
        elif [[ "$rule" == */ ]]; then
            pattern="${pattern%/}"
            pattern="^$pattern(/.*|$)"
        elif [[ "$rule" == */* ]]; then
            pattern="($|^.*/)$pattern($|/.*)$"
        else
            pattern="($|^.*/)$pattern($|/.*)$"
        fi

        # 检查路径匹配
        if [[ "$relative_path" =~ $pattern ]]; then
            if [[ "$is_inclusion" -eq 1 ]]; then
                match_include=1  # 匹配到例外规则，标记为包含
            else
                match_exclude=1  # 匹配到排除规则，标记为排除
            fi
        fi
    done

    # 如果匹配到包含规则，返回0（不忽略）
    # 如果匹配到排除规则且没有匹配到包含规则，返回1（忽略）
    if [[ "$match_include" -eq 1 ]]; then
        return 0
    elif [[ "$match_exclude" -eq 1 ]]; then
        return 1
    else
        return 0  # 默认不忽略
    fi
}

# 定义全局数组来记录每层级的计数
declare -a count_stack
declare -a index_stack

# 定义递归函数来打印目录结构
print_tree() {
    local directory="$1"
    local prefix="$2"
    local exclude_files="$3"
    local level="$4"
    local max_level="$5"

    # 递归到达最大层级时返回
    if [[ -n "$max_level" && "$level" -gt "$max_level" ]]; then
        return
    fi

    # 获取当前目录下的所有文件和文件夹
    shopt -s nullglob
    local items=("$directory"/*)
    shopt -u nullglob
    local count=${#items[@]}

    count_stack[$level]=$count
    index_stack[$level]=0

    while [[ ${index_stack[$level]} -lt ${count_stack[$level]} ]]; do
        local item="${items[${index_stack[$level]}]}"
        local base_name=$(basename "$item")
        local is_last=$((index_stack[$level] == count - 1))

        index_stack[$level]=$((index_stack[$level] + 1))

        # 跳过应该被 .gitignore 排除的文件夹和文件
		if [[ "$apply_gitignore" == "y" ]]; then
			is_excluded "$item"
			if [[ $? -eq 1 ]]; then  # 检查 is_excluded 的返回值，如果为 1 则忽略
				continue
			fi
		fi


        # 确定当前项的前缀符号
        if [ "$is_last" == "1" ]; then
            current_prefix="${prefix}└── $base_name"
            new_prefix="${prefix}    "
        else
            current_prefix="${prefix}├── $base_name"
            new_prefix="${prefix}│   "
        fi

        if [ -d "$item" ]; then
            # 打印目录名
            echo "$current_prefix"
            # 保存目录名到输出变量
            output_tree+="$current_prefix"$'\n'
            # 递归调用自己
            print_tree "$item" "$new_prefix" "$exclude_files" $((level + 1)) "$max_level"
        elif [ "$exclude_files" != "y" ]; then
            # 打印文件名
            echo "$current_prefix"
            # 保存文件名到输出变量
            output_tree+="$current_prefix"$'\n'
        fi
    done
}

# 获取当前目录的树型结构
directory="$(pwd)"

# 询问用户是否应用 .gitignore 中的内容
read -p "是否应用 .gitignore 中的内容? (y/n): " apply_gitignore

# 如果选择不应用，则清空排除列表
if [ "$apply_gitignore" == "n" ]; then
    GITIGNORE_RULES=()
else
    # 读取 .gitignore 文件
    read_gitignore "$directory"
fi

# 询问用户是否不包含文件
read -p "输出的树是否不包含文件? (y/n): " exclude_files

# 询问用户输出的层级
read -p "请输入输出的层级 (默认输出所有层级): " max_level

# 初始化输出变量
output_tree=""

# 打印并保存树型结构
echo "$(basename "$directory")"
output_tree+="$(basename "$directory")"$'\n'
print_tree "$directory" "" "$exclude_files" 1 "$max_level"

# 询问用户是否导出树型结构
read -p "是否导出这个输出的树? (y/n): " export_tree

if [ "$export_tree" == "y" ]; then
    echo -e "$output_tree" > "$output_file"
    echo "树型结构已导出到 $output_file"
fi
