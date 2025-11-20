#!/bin/bash

# 使用Docker构建APK，完全绕过本地环境问题
echo "===== 使用Docker构建APK ======"

# 创建Dockerfile（如果不存在）
if [ ! -f "Dockerfile.buildozer" ]; then
    cat > Dockerfile.buildozer << 'EOF'
FROM ubuntu:20.04

# 设置非交互式前端
ARG DEBIAN_FRONTEND=noninteractive

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 python3-pip python3-dev \
    git \
    openjdk-8-jdk \
    unzip \
    ant \
    ccache \
    autoconf automake libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 \
    curl wget \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip3 install --upgrade pip setuptools wheel cython && \
    pip3 install buildozer python-for-android

# 创建工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 设置环境变量
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# 预先下载依赖（加速构建）
RUN buildozer android clean

# 构建命令
CMD buildozer android debug
EOF
fi

# 创建简化的buildozer.spec
cat > buildozer.spec << 'EOF'
[app]
title = MyApp
package.name = org.test.myapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

requirements = kivy
orientation = portrait
screen = fullscreen

[buildozer]
log_level = 2
warn_on_root = 0
EOF

# 创建简单的main.py
if [ ! -f "main.py" ]; then
    cat > main.py << 'EOF'
import kivy
from kivy.app import App
from kivy.uix.label import Label

class MyApp(App):
    def build(self):
        return Label(text='Hello from Kivy!')

if __name__ == '__main__':
    MyApp().run()
EOF
fi

# 构建Docker镜像
echo "构建Docker镜像..."
docker build -t buildozer-builder -f Dockerfile.buildozer .

# 运行Docker容器进行构建
echo "运行Docker容器构建APK..."
docker run --rm -v $(pwd):/app buildozer-builder

# 检查结果
echo "===== 构建完成！检查结果 ======"
find . -name "*.apk" -ls
ls -la bin 2>/dev/null || echo "bin目录不存在"