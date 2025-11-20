# 🔗 Xshell连接Ubuntu服务器指南

## 📡 服务器信息
- **主机**: 43.226.47.156
- **端口**: 22
- **用户名**: root
- **密码**: DHMdhm99698

## 🚀 Xshell连接步骤

### 1. 新建会话
1. 打开Xshell
2. 点击"文件" → "新建"
3. 在"基本设置"中填入：
   - **名称**: Ubuntu服务器-Trae CN
   - **协议**: SSH
   - **主机**: 43.226.47.156
   - **端口号**: 22

### 2. 用户身份验证
1. 点击"用户身份验证"
2. 选择"方法": 密码
3. 填入：
   - **用户名**: root
   - **密码**: DHMdhm99698

### 3. 连接设置
1. 点击"连接" → "数据"
2. 在"连接中保持活动状态"中设置：
   - ✅ 勾选"保持连接"
   - **间隔**: 60秒
   - **重试次数**: 3次

### 4. 开始连接
1. 点击"确定"保存设置
2. 双击会话名称开始连接
3. 首次连接时选择"接受并保存"

## 🎯 连接后的操作

### 立即测试
连接成功后，运行以下命令验证：
```bash
# 系统信息
uname -a && lsb_release -a

# Python环境
python3 --version && which python3

# 运行测试程序
python3 -c "
import datetime, platform
print('✅ Ubuntu服务器连接成功！')
print(f'时间: {datetime.datetime.now()}')
print(f'系统: {platform.system()} {platform.release()}')
print(f'用户: root')
"
```

### 运行您的程序
```bash
# 方法1: 交互式运行
# 在Xshell中直接输入命令
python3 your_script.py

# 方法2: 运行完整程序
cat > test_program.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import threading

PORT = 8000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Hello from Ubuntu Server!</h1>')

with socketserver.TCPServer(('', PORT), MyHandler) as httpd:
    print(f'🌐 Web服务器运行在端口 {PORT}')
    httpd.serve_forever()
EOF

python3 test_program.py
```

### 文件操作
```bash
# 查看文件
cat /root/your_file.txt

# 编辑文件
nano /root/script.py
# 或使用vim
vim /root/script.py

# 文件传输（在Windows中打开命令提示符）
scp -P 22 test_program.py root@43.226.47.156:/root/
scp -P 22 root@43.226.47.156:/root/output.txt ./
```

## 💡 Trae CN中的使用

### 方法1: 使用SSH命令
在Trae CN的PowerShell中：
```powershell
ssh root@43.226.47.156
# 然后输入密码
```

### 方法2: 远程执行命令
在Trae CN的PowerShell中：
```powershell
ssh root@43.226.47.156 "python3 --version"
ssh root@43.226.47.156 "ls -la /root"
```

### 方法3: 使用Python脚本
```python
import subprocess

def run_on_ubuntu_server():
    cmd = ['ssh', '-p', '22', f'root@43.226.47.156', 'echo "Hello from Trae CN!"']
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)

run_on_ubuntu_server()
```

---
✅ **使用Xshell连接后，您就可以在Windows的Trae CN中完全控制Ubuntu服务器了！**
