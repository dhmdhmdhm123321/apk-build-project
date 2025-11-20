# p4a构建配置
from pythonforandroid.toolchain import BootstrapNDKRecipe

# 应用信息
package_name = 'org.test.myapp'
package_domain = 'org.test'
name = 'MyApp'
version = '0.1'

# 源代码设置
source_dir = '.'
requirements = ['kivy', 'certifi']  # 添加你的依赖

# 构建设置
orientation = 'portrait'
screen = 'fullscreen'

# Android设置
android_api = 28
ndk_version = '21.4.7075529'
sdk_version = '28'
archs = ['armeabi-v7a']  # 也可以是['armeabi-v7a', 'arm64-v8a']

# 其他设置
log_level = 2
strip_debug = True
