import os
import re
import sys
import importlib
import buildozer

# 获取buildozer模块路径
buildozer_module_path = buildozer.__file__
buildozer_dir = os.path.dirname(buildozer_module_path)

# 备份并修改__init__.py文件
init_file = os.path.join(buildozer_dir, '__init__.py')
with open(init_file, 'r') as f:
    content = f.read()

# 检查是否已经修改过
if 'def check_root(self):\n        return # 禁用root检查' not in content:
    # 备份文件
    import shutil
    shutil.copy2(init_file, init_file + '.backup')
    
    # 修改文件
    new_content = content.replace('def check_root(self):', 'def check_root(self):\n        return # 禁用root检查')
    with open(init_file, 'w') as f:
        f.write(new_content)
    print('已禁用buildozer的root用户检查')
else:
    print('buildozer的root用户检查已经被禁用')
