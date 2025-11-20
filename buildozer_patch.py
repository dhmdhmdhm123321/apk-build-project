# Monkey patch for buildozer to disable root check and interactive prompts
import sys
print("加载buildozer补丁...")

# 修补builtins.input以自动回答'y'
import builtins
original_input = builtins.input

def patched_input(prompt=""):
    print(f"自动回答提示: {prompt} -> y")
    return "y"

builtins.input = patched_input
print("已修补input函数")

# 导入buildozer后再应用补丁
try:
    from buildozer import Buildozer as OriginalBuildozer
    # 保存原始的check_root方法
    original_check_root = OriginalBuildozer.check_root
    # 重写check_root方法使其始终返回True
    OriginalBuildozer.check_root = lambda self: True
    print("已修补Buildozer.check_root方法")
except Exception as e:
    print(f"补丁应用时出错: {e}")
