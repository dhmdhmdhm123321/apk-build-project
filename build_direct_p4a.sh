#!/bin/bash

# 直接使用python-for-android构建APK，手动配置所有路径
echo "===== 直接使用python-for-android构建APK ====="

# 设置工作目录和环境变量
WORKDIR="$(pwd)"
ANDROID_HOME="$WORKDIR/.android_sdk"
ANDROID_NDK_HOME="$ANDROID_HOME/ndk/25.1.8937393"
JAVA_HOME="$(which java | xargs readlink -f | xargs dirname | xargs dirname)"

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

# 创建项目结构
mkdir -p android_project/src/main/python\cp main.py android_project/src/main/python/

# 安装依赖
echo "安装必要的Python依赖..."
pip3 install --upgrade pip setuptools wheel
pip3 install --force-reinstall importlib-metadata==4.8.3
pip3 install Cython==0.29.33 wheel kivy
pip3 install python-for-android

# 检查Android SDK是否存在，如果不存在则简化构建过程
echo "检查Android SDK..."
if [ ! -d "$ANDROID_HOME" ]; then
    echo "Android SDK未找到。使用简化的p4a配置..."
    
    # 使用p4a的简化命令，让p4a自动处理依赖
    echo "使用python-for-android构建..."
    p4a apk \
        --private "$WORKDIR" \
        --package=org.test.myapp \
        --name="MyKivyApp" \
        --version=0.1 \
        --bootstrap=sdl2 \
        --requirements=kivy \
        --window
else
    echo "使用自定义Android SDK路径构建..."
    p4a apk \
        --private "$WORKDIR" \
        --package=org.test.myapp \
        --name="MyKivyApp" \
        --version=0.1 \
        --bootstrap=sdl2 \
        --requirements=kivy \
        --window \
        --sdk-dir="$ANDROID_HOME"
fi

# 检查结果
echo "===== 构建完成！检查结果 ====="
find . -name "*.apk" -ls
ls -la