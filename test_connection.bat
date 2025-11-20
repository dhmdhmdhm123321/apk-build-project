@echo off
echo 🔍 测试SSH连接...
ssh -o ConnectTimeout=10 ubuntu-server-trae "echo '连接成功！' && uname -a && python3 --version"
pause
