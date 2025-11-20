with open("/usr/local/lib/python3.8/dist-packages/buildozer/__init__.py", 'r') as f:
    lines = f.readlines()

# 找到check_root函数并修复
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'def check_root(self):' in line:
        # 保存函数定义行
        new_lines.append(line)
        # 添加新的函数体
        indent = ' ' * (len(line) - len(line.lstrip()) + 4)
        new_lines.append(f'{indent}# 自动以root身份运行，不提示\n')
        new_lines.append(f'{indent}return True\n')
        new_lines.append('\n')
        # 跳过原来的函数体直到找到下一个方法
        i += 1
        while i < len(lines):
            if lines[i].strip().startswith('def ') and len(lines[i]) - len(lines[i].lstrip()) <= len(line) - len(line.lstrip()):
                break
            i += 1
    else:
        new_lines.append(line)
        i += 1

# 写回文件
with open("/usr/local/lib/python3.8/dist-packages/buildozer/__init__.py", 'w') as f:
    f.writelines(new_lines)

print("已修复buildozer的check_root函数")