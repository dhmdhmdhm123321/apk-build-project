#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Android主入口文件

这个文件作为工资计算系统在Android设备上的入口点，使用Kivy作为容器
来运行基于Tkinter的主应用。
"""

import kivy
kivy.require('2.3.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window

import os
import sys
import threading
from functools import partial

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入pyjnius用于Android原生交互
HAS_PYJNIUS = False
try:
    from jnius import autoclass, cast
    HAS_PYJNIUS = True
except ImportError:
    HAS_PYJNIUS = False
    print("警告: pyjnius模块未找到，将使用替代的退出机制")

class AndroidMainApp(App):
    def build(self):
        # 设置窗口大小
        Window.size = (800, 600)
        
        # 创建主布局
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 标题
        title_label = Label(text="工资计算系统", font_size=24, size_hint_y=0.2)
        main_layout.add_widget(title_label)
        
        # 状态标签
        self.status_label = Label(text="准备启动应用...", size_hint_y=0.1)
        main_layout.add_widget(self.status_label)
        
        # 启动按钮
        start_button = Button(text="启动工资计算系统", size_hint_y=0.1)
        start_button.bind(on_press=self.start_salary_calculator)
        main_layout.add_widget(start_button)
        
        # 退出按钮
        exit_button = Button(text="退出", size_hint_y=0.1)
        exit_button.bind(on_press=self.exit_app)
        main_layout.add_widget(exit_button)
        
        # 启动时自动启动应用
        Clock.schedule_once(self.start_salary_calculator, 1)
        
        return main_layout
    
    def start_salary_calculator(self, *args):
        """在单独的线程中启动工资计算系统"""
        self.status_label.text = "正在启动系统..."
        
        # 创建并启动新线程来运行工资计算系统
        threading.Thread(target=self._run_salary_calculator, daemon=True).start()
    
    def _run_salary_calculator(self):
        """运行工资计算系统的函数"""
        try:
            # 更新状态
            self.update_status("正在加载Android修复模块...")
            
            # 导入android_tkinter_fix模块以修复Android上的Tkinter问题
            from src import android_tkinter_fix
            android_tkinter_fix.init_android_tkinter()
            
            # 导入工资计算系统
            self.update_status("正在加载工资计算系统...")
            from src import salary_calculator
            
            # 更新状态
            self.update_status("应用已启动，请查看系统窗口...")
            
            # 运行工资计算系统
            salary_calculator.main()
            
        except Exception as e:
            # 如果发生错误，显示错误信息
            self.update_status(f"启动失败: {str(e)}")
            print(f"启动工资计算系统时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_status(self, message):
        """更新状态标签"""
        Clock.schedule_once(partial(self._update_status_label, message), 0)
    
    def _update_status_label(self, message, dt):
        """在主线程中更新状态标签"""
        self.status_label.text = message
    
    def exit_app(self, *args):
        """退出应用"""
        try:
            if HAS_PYJNIUS:
                # 获取Android活动管理器
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                
                # 调用finish方法退出应用
                activity.finish()
            else:
                # 如果pyjnius不可用，尝试多种退出方式
                print("使用替代的退出机制")
                
                # 方式1: 尝试使用kivy的stop方法
                try:
                    self.stop()
                except Exception as e:
                    print(f"尝试停止Kivy应用失败: {str(e)}")
                    
                # 方式2: 尝试强制退出进程
                try:
                    import os
                    if hasattr(os, '_exit'):
                        os._exit(0)  # 强制退出，不执行清理
                    else:
                        sys.exit(0)  # 常规退出
                except Exception as e:
                    print(f"尝试退出进程失败: {str(e)}")
        except Exception as e:
            print(f"退出应用时发生错误: {str(e)}")
            # 作为最后的手段，尝试强制退出
            try:
                import os
                if hasattr(os, '_exit'):
                    os._exit(0)
                else:
                    sys.exit(0)
            except:
                # 无法退出，但至少我们已经尽力了
                pass

if __name__ == '__main__':
    # 确保中文显示正常
    try:
        import matplotlib.pyplot as plt
        plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial"]
        plt.rcParams['axes.unicode_minus'] = False
    except ImportError:
        print("警告: matplotlib模块未找到，图表显示可能会有问题")
    
    # 运行应用
    AndroidMainApp().run()