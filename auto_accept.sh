#!/bin/bash
# 自动接受Android SDK许可证

echo "正在配置SDK许可证自动接受..."

# 创建必要的目录
mkdir -p ~/.android
mkdir -p "$HOME/.buildozer/android/platform/android-sdk/licenses"

# 生成模拟的许可文件
cat > ~/.android/repositories.cfg << 'EOL'
### Android Repository Configuration.
#Wed Nov 13 07:50:29 CST 2025
EOL

# 自动接受所有许可证
for license in "android-sdk-license" "android-sdk-preview-license" "android-sdk-arm-dbt-license" "google-gdk-license"; do
    mkdir -p "$HOME/.android/licenses"
    mkdir -p "$HOME/.buildozer/android/platform/android-sdk/licenses"
    echo "24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$HOME/.android/licenses/$license"
    echo "24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$HOME/.buildozer/android/platform/android-sdk/licenses/$license"
done

# 添加其他可能需要的许可证
mkdir -p "$HOME/.buildozer/android/platform/android-sdk/licenses"
echo "8933bad161af4178b1185d1a37fbf41ea5269c55" > "$HOME/.buildozer/android/platform/android-sdk/licenses/android-sdk-preview-license"
echo "d975f751698a77b662f1254ddbeed3901e976f5a" > "$HOME/.buildozer/android/platform/android-sdk/licenses/google-gdk-license"
echo "33b6a2b64607f11d30a1a61c13c7d429a1bab77a" > "$HOME/.buildozer/android/platform/android-sdk/licenses/intel-android-extra-license"

echo "已自动接受所有SDK许可证"
