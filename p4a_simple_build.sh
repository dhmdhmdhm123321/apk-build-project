#!/bin/bash

# 简洁版p4a构建脚本
echo "===== 开始构建APK ======"

# 设置环境变量
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export PATH=$PATH:/root/.local/bin

# 创建一个简单的main.py作为入口文件
if [ ! -f "main.py" ]; then
    echo "创建默认的main.py入口文件..."
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

# 设置Android SDK和NDK路径
export ANDROID_SDK_HOME=/root/apk/.buildozer/android/platform/android-sdk

# 确保SDK目录存在
if [ ! -d "$ANDROID_SDK_HOME" ]; then
    echo "SDK目录不存在，尝试创建..."
    mkdir -p $ANDROID_SDK_HOME
fi

# 直接使用p4a命令构建APK
echo "使用p4a构建APK..."
p4a apk \
    --package=org.test.myapp \
    --name="MyApp" \
    --version=0.1 \
    --bootstrap=sdl2 \
    --requirements=kivy \
    --private=. \
    --android-api=28 \
    --sdk-dir=$ANDROID_SDK_HOME \
    --orientation=portrait \
    --arch=armeabi-v7a \
    --log-level=2 \
    --debug

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "===== 构建成功！====="
    find . -name "*.apk" -ls
else
    echo "===== 构建失败 ======"
    echo "检查是否存在构建输出目录..."
    ls -la
fi