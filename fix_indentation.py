#!/usr/bin/env python3

# 修复buildozer __init__.py文件的缩进错误
import os

def fix_indentation():
    init_file = '/usr/local/lib/python3.8/dist-packages/buildozer/__init__.py'
    print(f"修复文件: {init_file}")
    
    # 读取文件内容
    with open(init_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 简单地重新格式化所有行的缩进
    fixed_lines = []
    indent_level = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 处理空行或注释
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue
        
        # 减少缩进的情况
        if stripped.startswith('return ') or stripped.startswith('raise ') or stripped.startswith('pass'):
            indent_level = max(0, indent_level - 1)
        if stripped.startswith('except:') or stripped.startswith('except ') or stripped.startswith('else:') or stripped.startswith('elif '):
            indent_level = max(0, indent_level - 1)
        
        # 添加正确缩进的行
        fixed_line = ' ' * (4 * indent_level) + stripped + '\n'
        fixed_lines.append(fixed_line)
        
        # 增加缩进的情况
        if stripped.endswith(':'):
            indent_level += 1
    
    # 写回文件
    with open(init_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"成功修复缩进: {init_file}")
    
    # 测试修复是否成功
    try:
        # 创建一个简单的测试脚本
        test_script = '''
import sys
print("尝试导入buildozer...")
sys.path.append('/usr/local/lib/python3.8/dist-packages')
import buildozer
print("buildozer导入成功！")
'''
        with open('/root/apk/test_import.py', 'w') as f:
            f.write(test_script)
        
        # 运行测试脚本
        import subprocess
        result = subprocess.run(['python3', '/root/apk/test_import.py'], capture_output=True, text=True)
        print("导入测试结果:")
        print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == '__main__':
    fix_indentation()