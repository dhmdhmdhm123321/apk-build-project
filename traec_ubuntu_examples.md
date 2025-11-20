# 🎯 Trae CN操作Ubuntu服务器实用示例

## 🔗 基本连接
```bash
# 方式1: 直接SSH连接
ssh root@43.226.47.156

# 方式2: 带指定端口
ssh -p 22 root@43.226.47.156
```

## 🐍 Python程序管理

### 运行Python脚本
```bash
# 方式1: SSH内执行
ssh root@43.226.47.156 "python3 /root/script.py"

# 方式2: 连接后执行
ssh root@43.226.47.156
# 然后在服务器上直接运行
python3 /root/script.py
```

### 后台运行程序
```bash
# SSH连接后执行
ssh root@43.226.47.156
nohup python3 /root/server.py &
```

### 查看程序状态
```bash
# SSH连接后执行
ssh root@43.226.47.156
ps aux | grep python
jobs
```

## 📁 文件传输

### 上传文件到服务器
```bash
# 单个文件
scp local_file.py root@43.226.47.156:/root/

# 多个文件
scp file1.py file2.py root@43.226.47.156:/root/

# 整个目录
scp -r local_dir/ root@43.226.47.156:/root/
```

### 从服务器下载文件
```bash
# 单个文件
scp root@43.226.47.156:/root/remote_file.py ./

# 多个文件
scp root@43.226.47.156:/root/file{1,2,3}.py ./

# 整个目录
scp -r root@43.226.47.156:/root/remote_dir/ ./
```

## 🔧 系统管理

### 查看系统状态
```bash
# SSH连接后执行
ssh root@43.226.47.156 "uptime && free -h && df -h"
```

### 安装软件包
```bash
# SSH连接后执行
ssh root@43.226.47.156 "apt update && apt install python3-pip"
```

### 重启服务
```bash
# SSH连接后执行
ssh root@43.226.47.156 "systemctl restart ssh"
```

## 💡 Trae CN中的工作流

### 1. 开发-测试循环
```bash
# 1. 在Trae CN中编辑代码
echo "print('Hello from Trae CN!')" > test.py

# 2. 上传到服务器
scp test.py root@43.226.47.156:/root/

# 3. 在服务器上运行
ssh root@43.226.47.156 "python3 /root/test.py"

# 4. 下载结果
scp root@43.226.47.156:/root/output.txt ./
```

### 2. 远程程序监控
```bash
# 查看服务器状态
ssh root@43.226.47.156 "ps aux | grep python && free -h"

# 查看日志
ssh root@43.226.47.156 "tail -f /var/log/syslog"
```

### 3. 批量操作
```bash
# 在多个服务器上运行相同命令
ssh root@43.226.47.156 "hostname && uptime"
```
