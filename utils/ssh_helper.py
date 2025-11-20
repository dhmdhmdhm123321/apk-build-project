#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH连接助手脚本
自动连接到Ubuntu服务器并执行命令
"""

import subprocess
import sys
import getpass
import os
import time

# 服务器配置
SERVER_CONFIG = {
    'host': '43.226.47.156',
    'port': '22',
    'username': 'root',
    'password': 'DHMdhm99698',
    'server_name': 'ubuntu-server-trae'
}

def connect_and_execute(command="", use_password=True):
    """连接到服务器并执行命令"""
    if use_password and SERVER_CONFIG['password']:
        # 使用密码的连接
        ssh_cmd = [
            'sshpass', '-p', SERVER_CONFIG['password'],
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            '-p', SERVER_CONFIG['port'],
            f"{SERVER_CONFIG['username']}@{SERVER_CONFIG['host']}",
            command if command else 'echo "连接成功！&& uname -a && python3 --version"'
        ]
    else:
        # 使用配置名称的连接
        ssh_cmd = [
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            SERVER_CONFIG['server_name'],
            command if command else 'echo "连接成功！&& uname -a && python3 --version"'
        ]
    
    try:
        print(f"🚀 连接到 {SERVER_CONFIG['host']}...")
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ SSH连接成功！")
            if result.stdout:
                print("📤 远程输出:")
                print(result.stdout)
            return True, result.stdout
        else:
            print("❌ SSH连接失败")
            if result.stderr:
                print(f"错误: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print("⏰ 连接超时")
        return False, "连接超时"
    except FileNotFoundError:
        print("❌ sshpass未找到，尝试使用配置名称连接...")
        # 尝试使用配置名称
        ssh_cmd = [
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            SERVER_CONFIG['server_name'],
            command if command else 'echo "连接成功！&& uname -a && python3 --version"'
        ]
        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ SSH连接成功（使用配置名称）！")
                if result.stdout:
                    print("📤 远程输出:")
                    print(result.stdout)
                return True, result.stdout
            else:
                print("❌ SSH连接失败（使用配置名称）")
                if result.stderr:
                    print(f"错误: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            print(f"❌ 连接异常: {e}")
            return False, str(e)
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False, str(e)

def interactive_session():
    """启动交互式SSH会话"""
    print("🖥️ 启动交互式SSH会话...")
    print("输入 'quit' 或 'exit' 退出")
    
    while True:
        try:
            command = input("\n{SERVER_CONFIG['server_name']}$ ")
            
            if command.lower() in ['quit', 'exit', 'bye']:
                print("👋 退出SSH会话")
                break
            
            if not command.strip():
                continue
                
            print(f"📤 执行: {command}")
            success, output = connect_and_execute(command)
            
            if success and output:
                print("📥 远程响应:")
                print(output)
                
        except KeyboardInterrupt:
            print("\n👋 退出SSH会话")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

def main():
    """主程序"""
    print("=" * 60)
    print("🚀 SSH连接助手")
    print("=" * 60)
    print(f"📡 服务器: {SERVER_CONFIG['host']}")
    print(f"👤 用户: {SERVER_CONFIG['username']}")
    print(f"🏷️  配置名: {SERVER_CONFIG['server_name']}")
    
    if len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
        print(f"🔍 执行命令: {command}")
        success, output = connect_and_execute(command)
        
        if success:
            print("✅ 命令执行成功")
        else:
            print("❌ 命令执行失败")
            sys.exit(1)
    else:
        print("\n📋 可用选项:")
        print("1. 交互式会话")
        print("2. 快速测试连接")
        print("3. 自定义命令")
        
        choice = input("\n选择操作 (1-3): ").strip()
        
        if choice == "1":
            interactive_session()
        elif choice == "2":
            success, output = connect_and_execute("uname -a && python3 --version")
            if success:
                print("✅ 连接测试成功！")
            else:
                print("❌ 连接测试失败")
        elif choice == "3":
            command = input("输入要执行的命令: ").strip()
            if command:
                success, output = connect_and_execute(command)
                if success:
                    print("✅ 命令执行成功")
                else:
                    print("❌ 命令执行失败")
            else:
                print("❌ 命令不能为空")
        else:
            print("❌ 无效选择")

if __name__ == "__main__":
    main()
