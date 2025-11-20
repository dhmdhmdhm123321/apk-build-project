#!/bin/bash

# 直接使用python-for-android构建APK
echo "===== 使用python-for-android直接构建APK ======"

# 确保所有依赖都已安装
echo "安装/更新必要的依赖..."
pip3 install --upgrade pip setuptools wheel cython packaging tomli --index-url=https://mirrors.aliyun.com/pypi/simple/
pip3 install --upgrade python-for-android --index-url=https://mirrors.aliyun.com/pypi/simple/

# 设置环境变量
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
# 设置Android SDK和NDK路径
export ANDROID_SDK_ROOT=/root/apk/android-sdk
export ANDROID_NDK_HOME=/root/apk/android-sdk/ndk/25.1.8937393
# 设置代理和镜像源
export PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
export PIP_TRUSTED_HOST=mirrors.aliyun.com
# 增加网络超时和重试参数
export PIP_TIMEOUT=120
export PIP_RETRY=5

# 创建一个基本的p4a配置文件
echo "创建p4a配置..."
cat > p4a_config.py << 'EOF'
# p4a构建配置
from pythonforandroid.toolchain import BootstrapNDKRecipe

# 应用信息
package_name = 'org.test.myapp'
package_domain = 'org.test'
name = 'MyApp'
version = '0.1'

# 源代码设置
source_dir = '.'
requirements = ['kivy', 'certifi']  # 添加你的依赖

# 构建设置
orientation = 'portrait'
screen = 'fullscreen'

# Android设置
android_api = 28
ndk_version = '21.4.7075529'
sdk_version = '28'
archs = ['armeabi-v7a']  # 也可以是['armeabi-v7a', 'arm64-v8a']

# 其他设置
log_level = 2
strip_debug = True
EOF

echo "开始使用p4a构建APK..."

# 直接使用p4a命令构建APK
p4a apk \
    --package=org.test.myapp \
    --name="MyApp" \
    --version=0.1 \
    --bootstrap=sdl2 \
    --requirements=kivy \
    --private=. \
    --android-api=33 \
    --sdk-dir=/root/apk/android-sdk \
    --ndk-dir=/root/apk/android-sdk/ndk/25.1.8937393 \
    --orientation=portrait \
    --arch=armeabi-v7a \
    --log-level=2 \
    --debug

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "===== 构建成功！检查输出文件 ======"
    find . -name "*.apk" -ls
else
    echo "===== 构建失败 ======"
    echo "尝试安装更多可能需要的系统依赖..."
    # 尝试安装一些常见的系统依赖（如果权限允许）
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        openjdk-8-jdk \
        unzip \
        ant \
        ccache \
        autoconf automake libtool pkg-config \
        zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 \
        python3-dev libffi-dev libssl-dev
fi