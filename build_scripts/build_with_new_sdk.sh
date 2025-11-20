#!/bin/bash

# 使用新安装的Android SDK构建APK
echo "===== 使用新安装的Android SDK构建APK ====="

# 设置环境变量
ANDROID_SDK_ROOT="/root/apk/android-sdk"
ANDROID_HOME="$ANDROID_SDK_ROOT"
export ANDROID_SDK_ROOT ANDROID_HOME
export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"

# 设置正确的Java环境（使用OpenJDK 11，Android SDK工具需要这个版本）
export JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"


# 确保main.py存在
if [ ! -f "main.py" ]; then
    cat > main.py << 'EOL'
import kivy
from kivy.app import App
from kivy.uix.label import Label

class MyApp(App):
    def build(self):
        return Label(text='Hello from Kivy!')

if __name__ == '__main__':
    MyApp().run()
EOL
fi

# 安装Python依赖（如果需要）
pip3 install --force-reinstall importlib-metadata==4.8.3
pip3 install Cython==0.29.33 wheel kivy
pip3 install python-for-android

# 创建输出目录
mkdir -p output

# 使用p4a构建APK
echo "使用新SDK构建APK..."
echo "SDK路径: $ANDROID_SDK_ROOT"
echo "Java路径: $JAVA_HOME"

# 使用新安装的SDK工具构建
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
    --sdk-dir="$ANDROID_SDK_ROOT" \
    --ndk-dir="$ANDROID_SDK_ROOT/ndk/25.1.8937393"

# 检查结果
echo "===== 构建完成！检查结果 ====="
find . -name "*.apk" -type f 2>/dev/null || echo "没有找到APK文件"
ls -la output/ 2>/dev/null || echo "output目录为空"
