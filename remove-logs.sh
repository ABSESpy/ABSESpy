#!/bin/bash
# 文件名：remove-logs.sh

echo "Listing directories containing log files:"
# 找到包含 .log 文件的目录
directories=$(find . -type f -name "*.log" | awk -F'/' '{OFS="/"; NF--; print $0}' | sort -u)

for dir in $directories; do
    echo "Found log files in directory: $dir"
    # 列出该目录下的所有 .log 文件
    find "$dir" -maxdepth 1 -type f -name "*.log"

    # 请求确认是否删除该目录下的所有 log 文件
    read -p "Do you want to delete all log files in this directory? (y/n) " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        # 删除该目录下的所有 log 文件
        find "$dir" -maxdepth 1 -type f -name "*.log" -exec rm {} +
        echo "Log files in $dir deleted."
    else
        echo "Deletion cancelled for $dir."
    fi
done
