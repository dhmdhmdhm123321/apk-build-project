@echo off

:: 工资计算系统 APK 构建启动脚本
:: 本脚本用于指导用户如何在Linux环境下构建APK

echo. ====================================================
echo.             工资计算系统 APK 构建指南               
echo. ====================================================
echo.
echo 重要提示: Kivy+Buildozer 构建需要在 Linux 环境中进行！
echo.
echo 您可以通过以下方式构建APK:
echo.
echo 方法1: 使用Linux系统或虚拟机
echo ---------------------------------------------
echo 1. 将 cwapk 目录复制到 Linux 系统
echo 2. 确保已安装 Docker 和 Docker Compose
echo 3. 在Linux终端中执行:
echo    cd /path/to/cwapk
    chmod +x build_apk_linux.sh
    ./build_apk_linux.sh

echo.
echo 方法2: 使用WSL2 (适用于Windows 10/11)
echo ---------------------------------------------
echo 1. 确保已启用并安装 WSL2 Ubuntu
    wsl --install -d Ubuntu
    wsl
    sudo apt update && sudo apt install docker.io docker-compose -y

echo 2. 在WSL终端中执行:
echo    cd /mnt/d/dhm/cwapk
    chmod +x build_apk_linux.sh
    ./build_apk_linux.sh

echo.
echo 首次构建将下载大量依赖(约2GB+)，可能需要1-2小时
echo 构建完成后，APK文件将位于 bin 目录中
echo.
echo 按任意键查看详细构建步骤...
pause >nul

echo.
echo 详细构建步骤:
echo ---------------------------------------------
echo 1. 准备Linux环境
    sudo apt update
    sudo apt install git zip openjdk-17-jdk python3-pip -y
    pip3 install --upgrade pip

echo 2. 安装Docker和Docker Compose
    sudo apt install docker.io docker-compose -y
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    newgrp docker

echo 3. 进入项目目录并构建
    cd /path/to/cwapk
    docker-compose up --build

echo 4. 查看构建结果
    ls -la bin/

echo.
echo 构建问题排查:
echo ---------------------------------------------
echo - 内存不足: 确保至少分配4GB内存给Linux环境
echo - 网络问题: 可能需要设置Docker镜像加速
echo - 权限问题: 使用sudo或以root用户运行Docker命令
echo.

:: 显示项目中的重要文件
echo 当前项目文件列表:
echo ---------------------------------------------
dir /B "%~dp0" | findstr /i "py db spec"
echo.

echo 按任意键退出...
pause >nul