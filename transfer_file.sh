#!/bin/bash
# 文件传输脚本
# 使用方法: 
#   ./transfer_file.sh to 本地文件 远程目录
#   ./transfer_file.sh from 远程文件 本地目录

if [ "$1" = "to" ]; then
    # 上传文件
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "❌ 参数错误"
        echo "使用方法: $0 to 本地文件 远程目录"
        exit 1
    fi
    echo "📤 上传文件: $2 -> $3"
    scp -P 22 "$2" root@43.226.47.156:"$3"
    
elif [ "$1" = "from" ]; then
    # 下载文件
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "❌ 参数错误"
        echo "使用方法: $0 from 远程文件 本地目录"
        exit 1
    fi
    echo "📥 下载文件: $2 -> $3"
    scp -P 22 root@43.226.47.156:"$2" "$3"
    
else
    echo "❌ 命令错误"
    echo "使用方法:"
    echo "  $0 to 本地文件 远程目录   # 上传文件到服务器"
    echo "  $0 from 远程文件 本地目录 # 从服务器下载文件"
fi
