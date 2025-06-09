#!/bin/bash

# 记录当前路径
current_dir="$(pwd)"

while true; do
    echo "当前位置: $current_dir"
    echo "-------------------------"
    # 列出所有子目录
    dirs=()
    idx=1
    for d in "$current_dir"/*/; do
        if [ -d "$d" ]; then
            dirs+=("$d")
            echo "$idx) $(basename "$d")"
            idx=$((idx+1))
        fi
    done

    # 增加其他操作选项
    echo "a) 检测并删除当前目录下所有空文件夹"
    echo "b) 返回上一层"
    echo "q) 退出脚本"
    echo "-------------------------"
    read -p "请输入要进入的目录编号，或选择操作: " choice

    # 判断用户输入
    if [[ "$choice" == "q" ]]; then
        echo "已退出。"
        exit 0
    elif [[ "$choice" == "b" ]]; then
        # 返回上一层
        parent_dir="$(dirname "$current_dir")"
        # 防止回到根目录上面
        if [[ "$parent_dir" == "$current_dir" ]]; then
            echo "已经到达根目录。"
        else
            current_dir="$parent_dir"
        fi
    elif [[ "$choice" == "a" ]]; then
        echo "正在检测并删除空文件夹..."
        for dir in "$current_dir"/*/; do
            [ -d "$dir" ] && [ "$(ls -A "$dir")" == "" ] && \
            { echo "删除空文件夹: $dir"; rmdir "$dir"; }
        done
        echo "完成。"
    elif [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#dirs[@]} )); then
        # 进入选定子目录
        current_dir="${dirs[$((choice-1))]}"
        # 去除末尾的斜杠，避免意外
        current_dir="${current_dir%/}"
    else
        echo "无效输入，请重新选择。"
    fi
    echo
done

