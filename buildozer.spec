[app]
title = Salary Calculator
package.name = com.salary.calculator
package.domain = com.salary
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
version = 1.0

requirements = python3,kivy
orientation = portrait
screen = fullscreen

# 应用权限
android.permissions = INTERNET

# 构建选项
android.arch = armeabi-v7a
android.api = 31
targetapi = 31

[buildozer]
log_level = 2
warn_on_root = 0
# 缓存目录设置
data_dir = .buildozer
