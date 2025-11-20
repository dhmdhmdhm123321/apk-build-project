#!/bin/bash

# 最终构建尝试：安装必要系统依赖并使用python-for-android
echo "===== 最终构建尝试 ====="

# 安装必要的系统依赖
echo "安装必要的系统依赖..."
apt-get update && apt-get install -y \
    android-tools-adb android-tools-fastboot \
    libc6:i386 libncurses5:i386 libstdc++6:i386 lib32z1 \
    build-essential git unzip wget curl \
    python3-dev python3-pip python3-setuptools python3-wheel

# 设置环境变量
export PATH=$PATH:/root/.local/bin

# 清理之前的构建缓存
echo "清理之前的构建缓存..."
rm -rf .buildozer/.gradle .buildozer/dist .buildozer/build \
       .buildozer/cache .p4a .cache/p4a
# 清理SDL2_image构建缓存目录，解决git克隆冲突
sdl2_image_dir="/root/.local/share/python-for-android/build/bootstrap_builds/sdl2/jni/SDL2_image"
if [ -d "$sdl2_image_dir/external" ]; then
  echo "删除SDL2_image外部依赖目录..."
  rm -rf "$sdl2_image_dir/external"
  # 创建空目录以避免FileNotFoundError
  mkdir -p "$sdl2_image_dir/external"
fi

# 确保main.py存在
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

# 安装Python依赖
echo "安装Python依赖..."
pip3 install --upgrade pip
pip3 install --force-reinstall importlib-metadata==4.8.3
pip3 install Cython==0.29.33 wheel kivy
pip3 install python-for-android

# 设置Android SDK路径（使用已有的SDK）
ANDROID_SDK_PATH="$(pwd)/android-sdk"
# 设置Android NDK路径
ANDROID_NDK_PATH="$(pwd)/android-sdk/ndk/25.1.8937393"
# 设置JAVA_HOME为JDK目录而非二进制文件
JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
export JAVA_HOME
# 将SDK和NDK路径添加到p4a命令中
P4A_SDK_DIR="$ANDROID_SDK_PATH"
P4A_NDK_DIR="$ANDROID_NDK_PATH"
export P4A_SDK_DIR
export P4A_NDK_DIR

# 使用p4a构建APK
echo "使用python-for-android构建APK..."
echo "Python路径: $(which python3)"
echo "pip路径: $(which pip3)"
echo "p4a路径: $(which p4a)"
echo "Android SDK路径: $ANDROID_SDK_PATH"
echo "Java路径: $JAVA_HOME"

# 设置Java环境变量（如果未自动设置）
if [ -z "$JAVA_HOME" ]; then
    export JAVA_HOME=$(readlink -f /usr/bin/java | sed "s:jre/bin/java::")
    echo "设置JAVA_HOME为: $JAVA_HOME"
fi

# 创建输出目录
mkdir -p output

# 使用p4a命令，明确指定架构、SDK和NDK目录
echo "使用指定架构、SDK和NDK目录重新构建..."
p4a apk \
    --private "$(pwd)" \
    --package=org.test.myapp \
    --name="MyKivyApp" \
    --version=0.1 \
    --bootstrap=sdl2 \
    --requirements=kivy \
    --window \
    --force-build \
    --log-level=debug \
    --output-dir="$(pwd)/output" \
    --arch=armeabi-v7a \
    --sdk-dir="$ANDROID_SDK_PATH" \
    --ndk-dir="$ANDROID_NDK_PATH"

# 检查结果
echo "===== 构建完成！检查结果 ====="
find . -name "*.apk" -type f 2>/dev/null || echo "没有找到APK文件"
ls -la output/ 2>/dev/null || echo "output目录为空"
ls -la .buildozer/android/platform/python-for-android/dists/ 2>/dev/null || echo "dists目录不存在"