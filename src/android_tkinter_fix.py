#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Android Tkinter 环境初始化修复模块
专为解决Android设备上运行Python Tkinter应用时出现的 'self.tk.getvar' 错误而设计

这个模块应该在任何Tkinter代码执行前导入和初始化
"""

import sys
import os
import types
import importlib
from functools import wraps

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试多种导入方式
try:
    from utils.common_utils import logger
except ImportError:
    # 如果无法导入，创建一个简单的logger
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# 检查是否在Android环境中运行
def is_android_environment():
    """检测当前是否在Android环境中运行"""
    # 检查特征目录
    if os.path.exists('/data/user/'):
        return True
    # 检查Python路径特征
    if 'aarch64-linux-android' in sys.executable:
        return True
    if 'com.cscjapp.python' in sys.executable:
        return True
    # 检查平台信息
    if hasattr(sys, 'getandroidapilevel'):
        return True
    # 检查系统环境变量
    if os.environ.get('ANDROID_ROOT') or os.environ.get('ANDROID_DATA'):
        return True
    return False

# 全局标志，表示是否已应用修复
_fix_applied = False

class FixedTkWrapper:
    """Tkinter Tk 类的包装器，提供针对Android环境的修复"""
    def __init__(self, original_tk_class):
        self.original_tk_class = original_tk_class
        
    def __call__(self, *args, **kwargs):
        # 尝试创建原始的Tk实例
        try:
            instance = self.original_tk_class(*args, **kwargs)
            # 验证tk属性是否存在且有效
            if hasattr(instance, 'tk') and instance.tk is not None:
                # 尝试修复_loadtk方法
                self._patch_loadtk(instance)
                return instance
        except Exception as e:
            print(f"创建原始Tk实例失败: {e}")
            print("尝试使用备用Tk实现...")
        
        # 如果原始Tk实例创建失败，返回一个模拟的Tk对象
        return self._create_fallback_tk_instance()
    
    def _patch_loadtk(self, instance):
        """修补_loadtk方法以防止getvar错误"""
        original_loadtk = instance.tk._loadtk
        
        @wraps(original_loadtk)
        def patched_loadtk():
            try:
                original_loadtk()
            except AttributeError as e:
                if 'getvar' in str(e) and 'tk_version' in str(e):
                    print(f"捕获并修复_loadtk错误: {e}")
                    # 手动设置tk_version属性以避免后续错误
                    if hasattr(instance.tk, '__dict__'):
                        instance.tk.__dict__['tk_version'] = '8.6'
                else:
                    raise
        
        # 应用补丁
        instance.tk._loadtk = patched_loadtk
    
    def _create_fallback_tk_instance(self):
        """创建一个模拟的Tk对象作为最后的后备方案"""
        class DummyTk:
            """模拟Tkinter Tk对象的最小实现"""
            def __init__(self):
                self._dummy_tk = self
                self.tk = self
                self.children = {}
                self.winfo_exists = lambda: True
                self.winfo_width = lambda: 800
                self.winfo_height = lambda: 600
                self.winfo_screenwidth = lambda: 800
                self.winfo_screenheight = lambda: 600
                self.update = lambda: None
                self.update_idletasks = lambda: None
                self.destroy = lambda: None
                self.withdraw = lambda: None
                self.deiconify = lambda: None
                self.title = lambda title: None
                self.geometry = lambda geometry: None
                self.configure = lambda **kwargs: None
                self.bind = lambda event, callback: None
                self.unbind = lambda event: None
                self.after = lambda ms, func=None, *args: None
            
            # Dummy tk属性实现
            def getvar(self, name, value=None):
                print(f"DummyTk.getvar called with name={name}, returning={value}")
                return value
            
            def setvar(self, name, value):
                print(f"DummyTk.setvar called with name={name}, value={value}")
                pass
            
            def _loadtk(self):
                print("DummyTk._loadtk called")
                pass
            
            # 其他必要的Tkinter方法实现
            def createcommand(self, name, func):
                pass
            
            def deletecommand(self, name):
                pass
            
            def eval(self, cmd):
                print(f"DummyTk.eval called with cmd={cmd}")
                return ""
            
            def call(self, *args):
                print(f"DummyTk.call called with args={args}")
                return ""
        
        # 创建并返回模拟的Tk实例
        dummy_tk = DummyTk()
        print("已创建模拟的Tk实例作为后备方案")
        return dummy_tk

def apply_tkinter_fix():
    """应用Tkinter修复，解决Android环境下的self.tk.getvar错误"""
    global _fix_applied
    
    # 避免重复应用修复
    if _fix_applied:
        return True
    
    # 只有在Android环境中才应用修复
    if not is_android_environment():
        print("不在Android环境中，跳过Tkinter修复")
        return False
    
    print("检测到Android环境，应用Tkinter修复...")
    
    try:
        # 尝试导入tkinter模块
        import tkinter as tk
        
        # 保存原始的Tk类
        original_tk = tk.Tk
        
        # 包装Tk类
        tk.Tk = FixedTkWrapper(original_tk)
        
        # 如果tkinter已经被其他模块导入，尝试重新加载它们
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('tkinter'):
                importlib.reload(sys.modules[module_name])
        
        _fix_applied = True
        print("Tkinter修复应用成功")
        return True
        
    except Exception as e:
        print(f"应用Tkinter修复失败: {e}")
        return False

# 在模块导入时自动应用修复（如果在Android环境中）
# 注意：这只会在第一次导入此模块时执行一次
if not _fix_applied:
    apply_tkinter_fix()

# 提供一个初始化函数，供应用程序显式调用
def init_android_tkinter():
    """应用程序可以显式调用此函数来确保Tkinter修复已应用"""
    return apply_tkinter_fix()