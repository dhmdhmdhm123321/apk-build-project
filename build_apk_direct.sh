#!/bin/bash

# 设置非交互式环境变量
export BUILDOZER_ALLOW_ROOT=1
export BUILDOZER_NON_INTERACTIVE=1
export BUILDOZER_AUTO_UPDATE=0

# 禁用buildozer交互式提示的函数
disable_buildozer_interactive() {
    # 查找buildozer的check_root函数并修改
    BUILDOZER_PATH=$(python3 -c "import buildozer; print(buildozer.__file__)")
    echo "修改 buildozer 文件: $BUILDOZER_PATH"
    
    # 备份原始文件
    cp $BUILDOZER_PATH ${BUILDOZER_PATH}.bak
    
    # 使用简单的sed命令直接替换整个check_root函数
    # 首先删除原来的check_root函数
    sed -i.bak '/def check_root(self):/,/^        return False/ d' $BUILDOZER_PATH
    
    # 然后在适当位置添加新的check_root函数
    sed -i.bak '/^    def check_requirements(self):/ i\
    def check_root(self):\n        # 自动以root身份运行，不提示\n        return True\n' $BUILDOZER_PATH
    
    # 验证修改是否成功
    if grep -q "def check_root(self):" $BUILDOZER_PATH && grep -q "return True" $BUILDOZER_PATH; then
        echo "成功修改buildozer以禁用交互式提示"
    else
        echo "警告：修改buildozer文件失败，尝试另一种方法..."
        # 备用方法：直接在文件开头添加monkey patch
        echo "from buildozer import Buildozer as OriginalBuildozer\nOriginalBuildozer.check_root = lambda self: True" > /tmp/buildozer_patch.py
        # 将patch导入添加到buildozer的__init__.py
        sed -i.bak '1i import sys; sys.path.append("/tmp"); import buildozer_patch' $BUILDOZER_PATH
    fi
}

# 配置buildozer.spec文件
configure_buildozer_spec() {
    if [ -f "buildozer.spec" ]; then
        echo "配置buildozer.spec文件..."
        sed -i.bak 's/buildozer_args = .*/buildozer_args = --non-interactive/' buildozer.spec
        
        # 确保添加了--non-interactive参数
        if ! grep -q "buildozer_args = --non-interactive" buildozer.spec; then
            echo "buildozer_args = --non-interactive" >> buildozer.spec
        fi
    else
        echo "buildozer.spec文件不存在，使用buildozer init创建..."
        python3 -m buildozer init --non-interactive
        configure_buildozer_spec
    fi
}

# 主执行函数
main() {
    echo "开始非交互式APK构建流程..."
    
    # 禁用buildozer交互式提示
    disable_buildozer_interactive
    
    # 配置buildozer.spec
    configure_buildozer_spec
    
    # 使用yes命令自动回答所有提示
    echo "执行buildozer android debug构建..."
    python3 -m buildozer android debug
    
    # 检查构建结果
    if [ $? -eq 0 ]; then
        echo "APK构建成功！"
        find bin -name "*.apk" | xargs ls -la
    else
        echo "构建失败，请检查错误日志"
        exit 1
    fi
}

# 执行主函数
main