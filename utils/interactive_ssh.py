#!/usr/bin/env python3
import subprocess

print("🔗 连接到Ubuntu服务器...")
print("主机: 43.226.47.156")
print("用户: root")
print("按 Ctrl+C 退出连接")

try:
    # 启动交互式SSH会话
    subprocess.run([
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"root@43.226.47.156"
    ], input="DHMdhm99698")
except KeyboardInterrupt:
    print("\n👋 SSH会话已结束")
except Exception:
    print("❌ 连接异常")
    print("💡 建议使用Xshell等专用SSH客户端")
