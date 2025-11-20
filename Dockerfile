# 支持从环境变量接收基础镜像，默认使用官方Ubuntu 22.04
ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 安装系统依赖
RUN apt-get update -y && \
    apt-get install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# 安装Kivy和Android相关依赖
RUN apt-get update -y && \
    apt-get install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# 安装Buildozer
RUN pip3 install --upgrade pip && \
    pip3 install --upgrade buildozer

# 创建工作目录
WORKDIR /app

# 初始化buildozer配置（如果需要）
RUN mkdir -p /root/.buildozer && \
    chmod -R 777 /root/.buildozer

# 设置默认命令为buildozer构建命令
CMD ["buildozer", "android", "debug"]