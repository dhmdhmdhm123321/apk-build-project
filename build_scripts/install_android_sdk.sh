#!/bin/bash

# 安装完整的Android SDK和必要工具
echo "===== 安装完整的Android SDK工具 ====="

# 设置目录
ANDROID_SDK_ROOT="/root/apk/android-sdk"
ANDROID_HOME="$ANDROID_SDK_ROOT"
export ANDROID_SDK_ROOT ANDROID_HOME

# 清理旧的SDK目录
rm -rf "$ANDROID_SDK_ROOT"
mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools/latest"

# 下载Android SDK Command-line Tools
echo "下载Android SDK Command-line Tools..."
wget -q "https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip" -O /tmp/sdk-tools.zip

# 解压SDK Tools
echo "解压SDK Tools..."
unzip -q /tmp/sdk-tools.zip -d /tmp/
mv /tmp/cmdline-tools/* "$ANDROID_SDK_ROOT/cmdline-tools/latest/"
rm -rf /tmp/cmdline-tools /tmp/sdk-tools.zip

# 添加SDK工具到PATH
export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"

# 接受SDK许可
echo "接受SDK许可..."
echo "y" | sdkmanager --licenses > /dev/null 2>&1

# 安装必要的SDK组件
echo "安装必要的SDK组件..."
sdkmanager "platforms;android-33" "platform-tools" "build-tools;33.0.2" "ndk;25.1.8937393"

# 检查安装是否成功
echo "检查SDK工具..."
ls -la "$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/"
ls -la "$ANDROID_SDK_ROOT/platform-tools/"

# 创建使用新SDK的构建脚本
echo "创建新的构建脚本..."
cat > /root/apk/build_with_new_sdk.sh << 'EOF'
#!/bin/bash

# 使用新安装的Android SDK构建APK
echo "===== 使用新安装的Android SDK构建APK ====="

# 设置环境变量
ANDROID_SDK_ROOT="/root/apk/android-sdk"
ANDROID_HOME="$ANDROID_SDK_ROOT"
export ANDROID_SDK_ROOT ANDROID_HOME
export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"

# 设置Java环境
export JAVA_HOME="$(readlink -f /usr/bin/java | sed "s:jre/bin/java::")"

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
EOF

chmod +x /root/apk/build_with_new_sdk.sh
echo "安装完成！可以运行 ./build_with_new_sdk.sh 来构建APK"