#!/bin/bash
echo "🚀 开始WSL环境APK构建"
# 更新系统
echo "📦 更新系统包..."
sudo apt update && sudo apt upgrade -y
# 安装依赖
echo "🔧 安装构建依赖..."
sudo apt install -y python3-pip python3-dev build-essential libssl-dev libffi-dev
# 安装p4a
echo "📱 安装p4a..."
pip3 install --upgrade pip
pip3 install python-for-android
# 创建构建目录
echo "📂 准备构建环境..."
mkdir -p ~/apk_build
cd ~/apk_build
# 复制文件（这里假设文件已在WSL中）
echo "📋 准备项目文件..."
if [ ! -f "p4a_simple_build.sh" ]; then
    echo "❌ 错误：找不到构建脚本"
    exit 1
fi
# 执行构建
echo "🏗️ 开始构建APK..."
bash p4a_simple_build.sh
echo "✅ 构建完成！"
