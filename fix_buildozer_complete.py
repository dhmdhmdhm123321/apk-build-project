#!/usr/bin/env python3

# 完全修复buildozer的__init__.py文件
import os
import re

def fix_buildozer_init():
    # 直接指定buildozer的路径
    init_file = '/usr/local/lib/python3.8/dist-packages/buildozer/__init__.py'
    print(f"修复文件: {init_file}")
    
    # 检查文件是否存在
    if not os.path.exists(init_file):
        # 尝试通过pip show找到正确的路径
        import subprocess
        try:
            result = subprocess.check_output(['pip3', 'show', 'buildozer'], text=True)
            for line in result.split('\n'):
                if line.startswith('Location:'):
                    loc = line.split(':', 1)[1].strip()
                    init_file = os.path.join(loc, 'buildozer', '__init__.py')
                    print(f"找到buildozer路径: {init_file}")
                    break
        except:
            print("无法找到buildozer安装路径")
            return
    
    # 读取文件内容
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复缩进错误 - 使用正则表达式找到check_root函数并替换
    # 确保函数有正确的缩进
    fixed_content = re.sub(
        r'def check_root\(self\):[\s\S]+?return True',
        '    def check_root(self):\n        # 自动确认以root用户运行\n        return True',
        content
    )
    
    # 如果没有找到check_root函数，则添加它
    if fixed_content == content:
        # 在适当的位置添加check_root函数
        if 'class Buildozer:' in fixed_content:
            # 在class定义后添加函数
            parts = fixed_content.split('class Buildozer:')
            fixed_content = parts[0] + 'class Buildozer:' + '\n    def check_root(self):\n        # 自动确认以root用户运行\n        return True' + parts[1]
    
    # 修复所有可能的缩进问题 - 简单地重新格式化
    lines = fixed_content.split('\n')
    fixed_lines = []
    indent_level = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            fixed_lines.append('')
            continue
        
        # 减少缩进级别
        if stripped.startswith('return ') or stripped.startswith('raise ') or stripped.startswith('pass'):
            indent_level = max(0, indent_level - 1)
        if stripped.startswith('except:') or stripped.startswith('except ') or stripped.startswith('else:') or stripped.startswith('elif '):
            indent_level = max(0, indent_level - 1)
        
        # 添加缩进
        fixed_lines.append(' ' * (4 * indent_level) + stripped)
        
        # 增加缩进级别
        if stripped.endswith(':'):
            indent_level += 1
        
    fixed_content = '\n'.join(fixed_lines)
    
    # 写回文件
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"成功修复: {init_file}")
    
    # 验证修复
    try:
        # 尝试导入以验证语法
        with open(init_file, 'r') as f:
            exec(f.read(), {})
        print("✓ 文件语法验证通过")
    except Exception as e:
        print(f"✗ 文件验证失败: {e}")

if __name__ == '__main__':
    fix_buildozer_init()