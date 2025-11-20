#!/bin/bash
echo "正在自动接受所有Android SDK许可证..."
for license_file in $(find $ANDROID_HOME -name "*-license"); do
    echo "查看许可证文件: $license_file"
done

# 为不同版本的sdkmanager准备命令
SDKMANAGER_CMD=""
if [ -f "$ANDROID_HOME/tools/bin/sdkmanager" ]; then
    SDKMANAGER_CMD="$ANDROID_HOME/tools/bin/sdkmanager"
elif [ -f "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
    SDKMANAGER_CMD="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
elif [ -f "$ANDROID_HOME/cmdline-tools/tools/bin/sdkmanager" ]; then
    SDKMANAGER_CMD="$ANDROID_HOME/cmdline-tools/tools/bin/sdkmanager"
fi

# 创建许可文件目录和文件
mkdir -p $ANDROID_HOME/licenses
echo "8933bad161af4178b1185d1a37fbf41ea5269c55" > $ANDROID_HOME/licenses/android-sdk-license
echo "d56f5187479451eabf01fb78af6dfcb131a6481e" > $ANDROID_HOME/licenses/android-sdk-preview-license
echo "24333f8a63b6825ea9c5514f83c2829b004d1fee" > $ANDROID_HOME/licenses/android-sdk-license
echo "d975f751698a77b662f1254ddbeed3901e976f5a" > $ANDROID_HOME/licenses/android-sdk-preview-license
echo "84831b9409646a918e30573bab4c9c91346d8abd" > $ANDROID_HOME/licenses/intel-android-extra-license

# 自动接受所有许可证
if [ -n "$SDKMANAGER_CMD" ]; then
    echo "使用SDK管理器: $SDKMANAGER_CMD"
    # 使用yes命令自动接受
    yes | $SDKMANAGER_CMD --sdk_root=$ANDROID_HOME --licenses > /dev/null 2>&1 || echo "警告: 许可证接受过程可能未完成"
    
    # 安装必要的SDK组件
    echo "安装SDK组件..."
    $SDKMANAGER_CMD "platforms;android-$ANDROIDAPI" "build-tools;33.0.2" "build-tools;36.1.0" "platform-tools" "tools" --sdk_root=$ANDROID_HOME > /dev/null 2>&1 || echo "警告: SDK组件安装可能未完成"
    
    # 验证安装
    echo "验证SDK组件安装..."
    ls -la $ANDROID_HOME/platforms/ 2>/dev/null || echo "平台目录不存在"
    ls -la $ANDROID_HOME/build-tools/ 2>/dev/null || echo "构建工具目录不存在"
else
    echo "错误: 找不到SDK管理器在 $ANDROID_HOME"
fi
