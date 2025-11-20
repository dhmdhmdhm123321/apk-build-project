# 🚀 SSH连接使用示例

## 基本连接

### 1. 使用配置名称连接
```bash
ssh ubuntu-server-trae
```

### 2. 直接连接
```bash
ssh root@43.226.47.156
```

### 3. 指定端口连接
```bash
ssh -p 22 root@43.226.47.156
```

## 远程命令执行

### 1. 单个命令
```bash
# 检查系统信息
ssh ubuntu-server-trae "uname -a && lsb_release -a"

# 检查Python环境
ssh ubuntu-server-trae "python3 --version && which python3"

# 查看目录内容
ssh ubuntu-server-trae "ls -la /root"
```

### 2. 多个命令
```bash
ssh ubuntu-server-trae "
    echo '=== 系统信息 ==='
    uname -a
    echo '=== Python环境 ==='
    python3 --version
    echo '=== 磁盘使用 ==='
    df -h
    echo '=== 内存使用 ==='
    free -h
"
```

### 3. 运行Python程序
```bash
# 直接运行Python代码
ssh ubuntu-server-trae "python3 -c 'import datetime; print(datetime.datetime.now())'"

# 运行Python脚本
ssh ubuntu-server-trae "python3 /path/to/your_script.py"

# 后台运行程序
ssh ubuntu-server-trae "nohup python3 /path/to/your_script.py &"
```

## 文件传输

### 1. 上传文件到服务器
```bash
# 简单上传
scp -P 22 local_file.py root@43.226.47.156:/root/

# 使用配置名称
scp -F ~/.ssh/config local_file.py ubuntu-server-trae:/root/

# 上传整个目录
scp -r -P 22 local_directory/ root@43.226.47.156:/root/
```

### 2. 从服务器下载文件
```bash
# 简单下载
scp -P 22 root@43.226.47.156:/root/remote_file.py ./

# 使用配置名称
scp -F ~/.ssh/config ubuntu-server-trae:/root/remote_file.py ./

# 下载整个目录
scp -r -P 22 root@43.226.47.156:/root/remote_directory/ ./
```

## 使用创建的脚本

### 1. 快速连接
```bash
./quick_connect.sh
```

### 2. 远程执行命令
```bash
./remote_cmd.sh "python3 --version"
./remote_cmd.sh "ls -la /root"
./remote_cmd.sh "uptime"
```

### 3. 文件传输
```bash
# 上传文件
./transfer_file.sh to local_file.py /root/

# 下载文件
./transfer_file.sh from /root/remote_file.py ./
```

## 实用技巧

### 1. 保持连接活跃
```bash
# 避免连接超时
ssh -o ServerAliveInterval=60 ubuntu-server-trae
```

### 2. 端口转发
```bash
# 将远程端口转发到本地
ssh -L 8080:localhost:80 ubuntu-server-trae
```

### 3. X11转发（如果需要GUI）
```bash
# 启用X11转发
ssh -X ubuntu-server-trae
```

## 故障排除

### 1. 连接问题
```bash
# 检查网络连通性
ping 43.226.47.156

# 检查端口开放性
telnet 43.226.47.156 22

# 详细连接调试
ssh -vvv ubuntu-server-trae
```

### 2. 认证问题
```bash
# 使用密码认证
ssh -o PreferredAuthentications=password ubuntu-server-trae

# 禁用公钥认证
ssh -o PubkeyAuthentication=no ubuntu-server-trae
```

## 在Trae CN中使用

### 1. 直接在终端中使用
```powershell
# 在PowerShell中使用
ssh ubuntu-server-trae
```

### 2. 在Python脚本中使用
```python
import subprocess

def run_remote_command(command):
    cmd = ['ssh', 'ubuntu-server-trae', command]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr

# 使用示例
stdout, stderr = run_remote_command("python3 --version")
print(stdout)
```

---
✅ **配置完成后，您就可以在Trae CN中轻松连接到Ubuntu服务器了！**
