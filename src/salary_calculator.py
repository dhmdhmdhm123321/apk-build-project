#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ===== 关键Android兼容性修复 - 必须放在最顶部 =====
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入并初始化Android Tkinter修复模块
try:
    from src.android_tkinter_fix import init_android_tkinter
    # 显式初始化修复
    init_android_tkinter()
    print("Android Tkinter修复模块已加载并初始化")
except Exception as e:
    print(f"加载Android Tkinter修复模块时出错: {e}")
    # 即使修复模块加载失败，程序也应该继续运行

# ===== 原有代码开始 =====

# 抑制libpng警告 - 移到最顶部以确保所有警告都被抑制
import warnings
warnings.filterwarnings("ignore", category=Warning, message="iCCP: known incorrect sRGB profile")

# 导入公共工具模块
try:
    from utils.common_utils import DatabaseManager, Validator, generate_emp_id, get_network_time, logger
except ImportError:
    # 降级处理，使用基本功能
    print("警告: 无法导入common_utils模块")
    
    # 创建简单的logger作为备用
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 创建基本的类和函数作为备用
    class DatabaseManager:
        pass
    class Validator:
        pass
    def generate_emp_id():
        return "EMP0000"
    def get_network_time():
        from datetime import datetime
        return datetime.now()

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
try:
    from utils.ttk_layout_constants import LEFT, RIGHT, TOP, BOTTOM, X, Y, BOTH, END, W, E, N, CENTER, WORD
except ImportError:
    # 定义常量作为备用
    LEFT, RIGHT, TOP, BOTTOM, X, Y, BOTH, END = 0, 1, 2, 3, 4, 5, 6, 7
    W, E, N, CENTER, WORD = 8, 9, 10, 11, 12
import datetime
import os
import calendar
import shutil
from tkinter import scrolledtext
from openpyxl import Workbook
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
import tempfile
import threading
import requests
import json
import sqlite3

# 设置matplotlib中文字体 - 优化字体列表顺序，确保Windows系统能找到
plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "KaiTi", "FangSong", "YouYuan", "Heiti TC", "WenQuanYi Micro Hei", "Arial"]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role  # 'admin' 或 'operator'

class Employee:
    def __init__(self, emp_id, name, department, position, base_salary, hire_date, contact='', status='active', leave_date=None):
        self.emp_id = emp_id
        self.name = name
        self.department = department
        self.position = position
        self.base_salary = base_salary
        self.hire_date = hire_date
        self.contact = contact  # 联系方式
        self.status = status  # 'active' 或 'inactive'
        self.leave_date = leave_date
        
    def to_dict(self):
        return {
            'emp_id': self.emp_id,
            'name': self.name,
            'department': self.department,
            'position': self.position,
            'base_salary': self.base_salary,
            'hire_date': self.hire_date,
            'contact': self.contact,
            'status': self.status,
            'leave_date': self.leave_date
        }

class Attendance:
    def __init__(self, emp_id, date, status='present', note=''):
        self.emp_id = emp_id
        self.date = date
        self.status = status  # 'present', 'absent', 'leave'
        self.note = note

class SalaryCalculator:
    def __init__(self, db_path='salary_system.db'):
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
        self.init_database()
        self.current_user = None  # 当前登录用户

    def login(self, username, password):
        """用户登录"""
        logger.info(f"用户登录尝试: {username}")
        result = self.db_manager.execute_query(
            "SELECT username, password, role FROM users WHERE username=? AND password=?",
            (username, password),
            fetch_one=True
        )
        
        if result:
            username, password, role = result
            self.current_user = User(username, password, role)
            logger.info(f"用户登录成功: {username} ({role})")
            return True, role
        logger.warning(f"用户登录失败: {username}")
        return False, None

    def logout(self):
        """用户登出"""
        if self.current_user:
            logger.info(f"用户登出: {self.current_user.username}")
            self.current_user = None
        else:
            logger.warning("尝试登出，但当前没有用户登录")

    def is_admin(self):
        """检查当前用户是否为管理员"""
        return self.current_user and self.current_user.role == 'admin'

    def backup_database(self):
        """备份数据库"""
        logger.info("开始数据库备份操作")
        if not self.is_admin():
            logger.warning(f"非管理员用户 {self.current_user.username if self.current_user else '未知用户'} 尝试执行备份操作")
            return False, "只有管理员才能执行备份操作"
        
        try:
            # 确保备份目录存在
            backup_dir = 'backups'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                logger.info(f"创建备份目录: {backup_dir}")
            
            # 生成备份文件名
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'salary_system_{timestamp}.db')
            
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"数据库文件复制完成: {backup_file}")
            
            # 获取备份文件大小
            file_size = os.path.getsize(backup_file)
            
            # 记录备份信息到数据库
            self.db_manager.execute_query(
                "INSERT INTO backups (backup_time, file_path, size, created_by) VALUES (?, ?, ?, ?)",
                (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), backup_file, file_size, self.current_user.username)
            )
            
            logger.info(f"数据库备份成功: {backup_file} (大小: {file_size} 字节)")
            return True, f"数据库备份成功：{backup_file}"
        except Exception as e:
            logger.error(f"备份失败: {str(e)}")
            return False, f"备份失败：{str(e)}"

    def restore_database(self, backup_id):
        """从备份恢复数据库"""
        logger.info(f"开始数据库恢复操作，备份ID: {backup_id}")
        if not self.is_admin():
            logger.warning(f"非管理员用户 {self.current_user.username if self.current_user else '未知用户'} 尝试执行恢复操作")
            return False, "只有管理员才能执行恢复操作"
        
        try:
            # 获取备份信息
            result = self.db_manager.execute_query(
                "SELECT file_path FROM backups WHERE id=?",
                (backup_id,),
                fetch_one=True
            )
            
            if not result:
                logger.warning(f"找不到指定的备份记录，ID: {backup_id}")
                return False, "找不到指定的备份记录"
            
            backup_file = result[0]
            logger.info(f"找到备份文件: {backup_file}")
            
            # 检查备份文件是否存在
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在：{backup_file}")
                return False, f"备份文件不存在：{backup_file}"
            
            # 复制备份文件到当前数据库
            shutil.copy2(backup_file, self.db_path)
            logger.info(f"数据库恢复成功：{backup_file}")
            
            return True, f"数据库恢复成功：{backup_file}"
        except Exception as e:
            logger.error(f"恢复失败：{str(e)}")
            return False, f"恢复失败：{str(e)}"

    def get_all_backups(self):
        """获取所有备份记录"""
        backups = self.db_manager.execute_query(
            "SELECT id, backup_time, file_path, size FROM backups ORDER BY backup_time DESC",
            fetch_all=True
        )
        return backups if backups else []

    def delete_backup(self, backup_id):
        """删除备份"""
        logger.info(f"开始删除备份，备份ID: {backup_id}")
        
        # 检查是否为管理员
        if not self.current_user or self.current_user.role != 'admin':
            logger.warning(f"非管理员用户 {self.current_user.username if self.current_user else '未知用户'} 尝试执行删除备份操作")
            return False, "只有管理员才能执行删除备份操作"
        
        try:
            # 获取备份信息
            result = self.db_manager.execute_query(
                "SELECT file_path FROM backups WHERE id=?",
                (backup_id,),
                fetch_one=True
            )
            
            if not result:
                logger.warning(f"找不到指定的备份记录，ID: {backup_id}")
                return False, "找不到指定的备份记录"
            
            backup_file = result[0]
            logger.info(f"找到备份文件: {backup_file}")
            
            # 检查备份文件是否存在并删除
            if os.path.exists(backup_file):
                os.remove(backup_file)
                logger.info(f"删除备份文件成功: {backup_file}")
            else:
                logger.warning(f"备份文件不存在: {backup_file}")
            
            # 从数据库中删除记录
            self.db_manager.execute_query(
                "DELETE FROM backups WHERE id=?",
                (backup_id,)
            )
            
            logger.info(f"删除备份记录成功，备份ID: {backup_id}")
            return True, "备份删除成功"
        except Exception as e:
            logger.error(f"删除备份失败: {str(e)}")
            return False, f"删除备份失败：{str(e)}"

    def add_user(self, username, password, role='operator'):
        """添加用户"""
        logger.info(f"开始添加用户: {username} (角色: {role})")
        if not self.is_admin():
            logger.warning(f"非管理员用户 {self.current_user.username} 尝试添加用户")
            return False, "只有管理员才能添加用户"
        
        try:
            # 输入验证
            if not Validator.is_valid_name(username):
                return False, "用户名格式不正确（只能包含中文、英文和数字）！"
            if not password or len(password) < 6:
                return False, "密码长度不能少于6位！"
            if role not in ['admin', 'operator']:
                return False, "角色必须是'admin'或'operator'！"
            
            # 添加新用户
            result = self.db_manager.execute_query(
                "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
                (username, password, role, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            
            if result:
                logger.info(f"用户添加成功: {username} (角色: {role})")
                return True, "用户添加成功"
            else:
                logger.error(f"添加用户失败，数据库操作未成功")
                return False, "添加用户失败，数据库操作未成功"
        except sqlite3.IntegrityError:
            logger.warning(f"用户名已存在: {username}")
            return False, "用户名已存在"
        except Exception as e:
            logger.error(f"添加用户失败: {str(e)}")
            return False, f"添加用户失败: {str(e)}"

    def add_revenue(self, date, emp_id, amount, description):
        """添加收入记录"""
        logger.info(f"开始添加收入记录: 员工ID {emp_id}, 金额 {amount}, 日期 {date}")
        if not self.current_user:
            logger.warning("未登录用户尝试添加收入记录")
            return False, "请先登录"
        
        try:
            # 输入验证
            if not Validator.is_valid_date(date):
                return False, "日期格式不正确（YYYY-MM-DD）！"
            if not Validator.is_valid_emp_id(emp_id):
                return False, "员工ID格式不正确！"
            if not Validator.is_valid_salary(amount):
                return False, "金额必须是非负数！"
            
            # 获取员工姓名
            result = self.db_manager.execute_query(
                "SELECT name FROM employees WHERE emp_id=?",
                (emp_id,),
                fetch_one=True
            )
            emp_name = result[0] if result else '未知'
            
            # 检查是否已有相同日期的收入记录
            existing_record = self.db_manager.execute_query(
                "SELECT id FROM revenue WHERE emp_id=? AND date=?",
                (emp_id, date),
                fetch_one=True
            )
            
            if existing_record:
                logger.warning(f"员工 {emp_id} ({emp_name}) 在 {date} 已有收入记录，不能重复添加")
                return False, f"员工 {emp_name} 在 {date} 已有收入记录，请修改已有记录"
            
            # 添加收入记录
            result = self.db_manager.execute_query(
                "INSERT INTO revenue (date, emp_id, amount, description, added_by) VALUES (?, ?, ?, ?, ?)",
                (date, emp_id, amount, description, self.current_user.username)
            )
            
            if result:
                logger.info(f"收入记录添加成功: {date}, 员工 {emp_id} ({emp_name}), 金额 {amount}, 添加人 {self.current_user.username}")
                return True, "收入记录添加成功"
            else:
                logger.error(f"添加收入记录失败，数据库操作未成功")
                return False, "添加收入记录失败，数据库操作未成功"
        except Exception as e:
            logger.error(f"添加收入记录失败: {str(e)}")
            return False, f"添加失败: {str(e)}"

    def update_revenue(self, revenue_id, date, emp_id, amount, description):
        """更新收入记录"""
        logger.info(f"开始更新收入记录: ID {revenue_id}")
        if not self.current_user:
            logger.warning("未登录用户尝试更新收入记录")
            return False, "请先登录"
        
        try:
            # 输入验证
            if not Validator.is_valid_date(date):
                return False, "日期格式不正确（YYYY-MM-DD）！"
            if not Validator.is_valid_emp_id(emp_id):
                return False, "员工ID格式不正确！"
            if not Validator.is_valid_salary(amount):
                return False, "金额必须是非负数！"
            
            # 确保revenue_id是整数
            try:
                revenue_id = int(revenue_id)
            except (ValueError, TypeError):
                return False, "收入记录ID必须是数字！"
            
            # 获取员工姓名
            result = self.db_manager.execute_query(
                "SELECT name FROM employees WHERE emp_id=?",
                (emp_id,),
                fetch_one=True
            )
            emp_name = result[0] if result else '未知'
            
            # 检查记录是否存在
            existing_record = self.db_manager.execute_query(
                "SELECT id FROM revenue WHERE id=?",
                (revenue_id,),
                fetch_one=True
            )
            
            if not existing_record:
                logger.warning(f"收入记录 ID {revenue_id} 不存在")
                return False, "收入记录不存在"
            
            # 检查是否有其他记录使用相同的员工和日期
            duplicate_record = self.db_manager.execute_query(
                "SELECT id FROM revenue WHERE emp_id=? AND date=? AND id != ?",
                (emp_id, date, revenue_id),
                fetch_one=True
            )
            
            if duplicate_record:
                logger.warning(f"员工 {emp_id} ({emp_name}) 在 {date} 已有其他收入记录")
                return False, f"员工 {emp_name} 在 {date} 已有其他收入记录，请选择不同日期"
            
            # 更新收入记录
            result = self.db_manager.execute_query(
                "UPDATE revenue SET date=?, emp_id=?, amount=?, description=? WHERE id=?",
                (date, emp_id, amount, description, revenue_id)
            )
            
            if result:
                logger.info(f"收入记录更新成功: ID {revenue_id}, 员工 {emp_id} ({emp_name}), 金额 {amount}")
                return True, "收入记录更新成功"
            else:
                logger.error(f"更新收入记录失败，数据库操作未成功")
                return False, "更新收入记录失败，数据库操作未成功"
        except Exception as e:
            logger.error(f"更新收入记录失败: {str(e)}")
            return False, f"更新失败: {str(e)}"

    def delete_revenue(self, revenue_id):
        """删除收入记录"""
        logger.info(f"开始删除收入记录: ID {revenue_id}")
        if not self.current_user:
            logger.warning("未登录用户尝试删除收入记录")
            return False, "请先登录"
        
        if not self.is_admin():
            logger.warning(f"非管理员用户 {self.current_user.username} 尝试删除收入记录")
            return False, "只有管理员才能删除收入记录"
        
        try:
            # 输入验证
            try:
                # 确保revenue_id是整数
                revenue_id = int(revenue_id)
            except (ValueError, TypeError):
                return False, "收入记录ID必须是数字！"
            
            # 检查记录是否存在
            existing_record = self.db_manager.execute_query(
                "SELECT id, emp_id, date FROM revenue WHERE id=?",
                (revenue_id,),
                fetch_one=True
            )
            
            if not existing_record:
                logger.warning(f"收入记录 ID {revenue_id} 不存在")
                return False, "收入记录不存在"
            
            revenue_id, emp_id, date = existing_record
            
            # 获取员工姓名
            result = self.db_manager.execute_query(
                "SELECT name FROM employees WHERE emp_id=?",
                (emp_id,),
                fetch_one=True
            )
            emp_name = result[0] if result else '未知'
            
            # 删除收入记录
            result = self.db_manager.execute_query(
                "DELETE FROM revenue WHERE id=?",
                (revenue_id,)
            )
            
            if result:
                logger.info(f"收入记录删除成功: ID {revenue_id}, 员工 {emp_id} ({emp_name}), 日期 {date}")
                return True, "收入记录删除成功"
            else:
                logger.error(f"删除收入记录失败，数据库操作未成功")
                return False, "删除收入记录失败，数据库操作未成功"
        except Exception as e:
            logger.error(f"删除收入记录失败: {str(e)}")
            return False, f"删除失败: {str(e)}"

    def calculate_profit(self, start_date, end_date, salary_query_type="month"):
        """计算指定日期范围内的利润
        
        参数:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            salary_query_type: 工资查询方式 ("month" 或 "payment_date")
        """
        logger.info(f"开始计算利润: 日期范围 {start_date} 至 {end_date}, 工资查询方式: {salary_query_type}")
        
        try:
            # 输入验证
            if not Validator.is_valid_date(start_date) or not Validator.is_valid_date(end_date):
                return False, "日期格式不正确（YYYY-MM-DD）！"
            
            # 计算总收入
            result = self.db_manager.execute_query(
                "SELECT SUM(amount) FROM revenue WHERE date BETWEEN ? AND ?",
                (start_date, end_date),
                fetch_one=True
            )
            total_revenue = result[0] or 0
            logger.info(f"总收入计算完成: {total_revenue}")
            
            # 计算工资支出 - 根据查询类型选择不同的计算方式
            if salary_query_type == "month":
                # 从日期中提取月份
                start_month = start_date[:7]  # YYYY-MM
                end_month = end_date[:7]
                
                # 查询指定月份范围内的所有工资记录（不依赖payment_date）
                result = self.db_manager.execute_query(
                    "SELECT SUM(final_salary) FROM salaries WHERE month BETWEEN ? AND ?",
                    (start_month, end_month),
                    fetch_one=True
                )
                total_salary = result[0] or 0
                logger.info(f"工资支出计算完成(按月): {total_salary}")
            else:
                # 按支付日期计算
                result = self.db_manager.execute_query(
                    "SELECT SUM(final_salary) FROM salaries WHERE payment_date BETWEEN ? AND ?",
                    (start_date, end_date),
                    fetch_one=True
                )
                total_salary = result[0] or 0
                logger.info(f"工资支出计算完成(按支付日期): {total_salary}")
            
            # 计算其他支出
            result = self.db_manager.execute_query(
                "SELECT SUM(amount) FROM expenses WHERE date BETWEEN ? AND ?",
                (start_date, end_date),
                fetch_one=True
            )
            total_other_expenses = result[0] or 0
            logger.info(f"其他支出计算完成: {total_other_expenses}")
            
            # 总支出 = 工资支出 + 其他支出
            total_expenses = total_salary + total_other_expenses
            
            # 利润 = 收入 - 总支出
            profit = total_revenue - total_expenses
            logger.info(f"利润计算完成: {profit}")
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'total_revenue': total_revenue,
                'total_salary': total_salary,
                'total_other_expenses': total_other_expenses,
                'total_expenses': total_expenses,
                'profit': profit
            }
        except Exception as e:
            logger.error(f"计算利润失败: {str(e)}")
            return {'error': str(e)}
        
    def init_database(self):
        """初始化数据库"""
        logger.info("初始化数据库...")
        
        # 创建备份记录表
        self.db_manager.execute_query('''
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_time TEXT NOT NULL,
            file_path TEXT NOT NULL,
            size INTEGER NOT NULL,
            created_by TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
        ''')
        
        # 创建用户表
        self.db_manager.execute_query('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'operator', -- 'admin' 或 'operator'
            created_at TEXT NOT NULL
        )
        ''')
        
        # 创建员工表
        self.db_manager.execute_query('''
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            base_salary REAL NOT NULL,
            hire_date TEXT NOT NULL,
            status TEXT NOT NULL,
            leave_date TEXT
        )
        ''')
        
        # 创建考勤表
        self.db_manager.execute_query('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
        ''')
        
        # 创建工资表
        self.db_manager.execute_query('''
        CREATE TABLE IF NOT EXISTS salaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            month TEXT NOT NULL,
            base_salary REAL NOT NULL,
            bonus REAL DEFAULT 0,
            deduction REAL DEFAULT 0,
            final_salary REAL NOT NULL,
            payment_date TEXT,
            status TEXT DEFAULT 'unpaid',
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
        ''')
        
        # 创建收入表
        self.db_manager.execute_query('''
        CREATE TABLE IF NOT EXISTS revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            emp_id TEXT,
            amount REAL NOT NULL,
            description TEXT,
            added_by TEXT NOT NULL,
            FOREIGN KEY (added_by) REFERENCES users(username),
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
        ''')
        
        # 创建支出表
        self.db_manager.execute_query('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            added_by TEXT NOT NULL,
            FOREIGN KEY (added_by) REFERENCES users(username)
        )
        ''')
        
        # 创建税率表
        self.db_manager.execute_query('''
        CREATE TABLE IF NOT EXISTS tax_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            min_salary REAL NOT NULL,
            max_salary REAL NOT NULL,
            rate REAL NOT NULL,
            deduction REAL NOT NULL
        )
        ''')
        
        # 检查是否有税率数据，如果没有则初始化默认税率（中国个人所得税税率表）
        result = self.db_manager.execute_query("SELECT COUNT(*) FROM tax_rates", fetch_one=True)
        if result and result[0] == 0:
            # 添加默认税率数据
            tax_data = [
                (0, 5000, 0, 0),
                (5000, 8000, 0.03, 0),
                (8000, 17000, 0.1, 210),
                (17000, 30000, 0.2, 1410),
                (30000, 40000, 0.25, 2660),
                (40000, 60000, 0.3, 4410),
                (60000, 85000, 0.35, 7160),
                (85000, float('inf'), 0.45, 15160)
            ]
            for data in tax_data:
                self.db_manager.execute_query(
                    "INSERT INTO tax_rates (min_salary, max_salary, rate, deduction) VALUES (?, ?, ?, ?)",
                    data
                )
        
        # 检查是否有管理员用户，如果没有则创建默认管理员
        result = self.db_manager.execute_query("SELECT COUNT(*) FROM users WHERE role='admin'", fetch_one=True)
        if result and result[0] == 0:
            self.db_manager.execute_query(
                "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
                ('admin', 'admin123', 'admin', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
    
    def add_employee(self, employee):
        try:
            # 输入验证
            if not Validator.is_valid_emp_id(employee.emp_id):
                return False, "员工ID格式不正确！"
            if not Validator.is_valid_name(employee.name):
                return False, "姓名格式不正确（只能包含中文、英文和数字）！"
            if not Validator.is_valid_salary(employee.base_salary):
                return False, "基本工资必须是非负数！"
            if not Validator.is_valid_date(employee.hire_date):
                return False, "入职日期格式不正确（YYYY-MM-DD）！"
            if employee.leave_date and not Validator.is_valid_date(employee.leave_date):
                return False, "离职日期格式不正确（YYYY-MM-DD）！"
            if not Validator.is_valid_phone(employee.contact):
                return False, "联系方式必须是11位有效的手机号码！"
            
            # 检查员工姓名是否已存在
            result = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM employees WHERE name=?",
                (employee.name,),
                fetch_one=True
            )
            if result and result[0] > 0:
                return False, "员工姓名已存在！"
            
            # 检查员工表是否有contact字段，如果没有则添加
            result = self.db_manager.execute_query("PRAGMA table_info(employees)", fetch_all=True)
            if result:
                columns = [column[1] for column in result]
                if 'contact' not in columns:
                    self.db_manager.execute_query("ALTER TABLE employees ADD COLUMN contact TEXT")
            
            # 添加调试信息
            logger.info(f"准备添加员工: {employee.emp_id} - {employee.name}")
            logger.info(f"员工数据: {employee}")

            # 插入员工数据 - 修正字段顺序以匹配数据库表结构
            # 数据库表结构顺序: emp_id, name, department, position, base_salary, hire_date, status, leave_date, contact
            result = self.db_manager.execute_query(
                "INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (employee.emp_id, employee.name, employee.department, employee.position,
                 employee.base_salary, employee.hire_date, employee.status, employee.leave_date, employee.contact)
            )

            # 添加调试信息
            logger.info(f"添加员工结果: {result}")

            if result:
                logger.info(f"员工添加成功: {employee.emp_id} - {employee.name}")
                return True, "员工添加成功！"
            else:
                logger.error(f"添加员工失败，数据库操作未成功: {employee.emp_id} - {employee.name}")
                return False, "添加员工失败，数据库操作未成功！"
        except sqlite3.IntegrityError:
            return False, "员工ID已存在！"
        except Exception as e:
            logger.error(f"添加员工异常: {str(e)}")
            return False, f"添加员工异常: {str(e)}"
    
    def update_employee(self, employee):
        try:
            # 输入验证
            if not Validator.is_valid_emp_id(employee.emp_id):
                return False, "员工ID格式不正确！"
            if not Validator.is_valid_name(employee.name):
                return False, "姓名格式不正确（只能包含中文、英文和数字）！"
            if not Validator.is_valid_salary(employee.base_salary):
                return False, "基本工资必须是非负数！"
            if not Validator.is_valid_date(employee.hire_date):
                return False, "入职日期格式不正确（YYYY-MM-DD）！"
            if employee.leave_date and not Validator.is_valid_date(employee.leave_date):
                return False, "离职日期格式不正确（YYYY-MM-DD）！"
            
            # 更新员工数据
            result = self.db_manager.execute_query(
                """UPDATE employees 
                SET name=?, department=?, position=?, base_salary=?, hire_date=?, status=?, leave_date=? 
                WHERE emp_id=?""",
                (employee.name, employee.department, employee.position, employee.base_salary,
                 employee.hire_date, employee.status, employee.leave_date, employee.emp_id)
            )
            
            return result is not None
        except Exception as e:
            logger.error(f"更新员工异常: {str(e)}")
            return False
    
    def get_employee(self, emp_id):
        if not Validator.is_valid_emp_id(emp_id):
            logger.warning(f"无效的员工ID格式: {emp_id}")
            return None
        
        row = self.db_manager.execute_query(
            "SELECT * FROM employees WHERE emp_id=?",
            (emp_id,),
            fetch_one=True
        )
        
        if row:
            return Employee(*row)
        return None
    
    def get_all_employees(self, status=None):
        # 查询员工数据，但不依赖于特定的列顺序
        if status is not None:
            rows = self.db_manager.execute_query(
                "SELECT emp_id, name, department, position, base_salary, hire_date, status, leave_date, contact FROM employees WHERE status=?",
                (status,),
                fetch_all=True
            )
        else:
            rows = self.db_manager.execute_query(
                "SELECT emp_id, name, department, position, base_salary, hire_date, status, leave_date, contact FROM employees",
                fetch_all=True
            )
        
        if rows:
            # 根据实际的数据库表结构和Employee构造函数参数顺序进行映射
            # 数据库返回顺序: emp_id, name, department, position, base_salary, hire_date, status, leave_date, contact
            # Employee构造函数参数顺序: emp_id, name, department, position, base_salary, hire_date, contact, status, leave_date
            employees = []
            for row in rows:
                # 确保行数据长度正确
                if len(row) >= 9:
                    # 重新排序参数以匹配Employee构造函数
                    emp_id, name, department, position, base_salary, hire_date, db_status, leave_date, contact = row[:9]
                    # 按照Employee构造函数的参数顺序创建对象
                    employee = Employee(
                        emp_id=emp_id,
                        name=name,
                        department=department,
                        position=position,
                        base_salary=base_salary,
                        hire_date=hire_date,
                        contact=contact,  # 注意这里的顺序调整
                        status=db_status,  # 注意这里的顺序调整
                        leave_date=leave_date
                    )
                    employees.append(employee)
                else:
                    logger.warning(f"员工数据不完整，跳过此记录: {row}")
            return employees
        return []
    
    def add_attendance(self, attendance):
        try:
            # 输入验证
            if not Validator.is_valid_emp_id(attendance.emp_id):
                logger.warning(f"无效的员工ID格式: {attendance.emp_id}")
                return False
            if not Validator.is_valid_date(attendance.date):
                logger.warning(f"无效的日期格式: {attendance.date}")
                return False
            if attendance.status not in ['present', 'absent', 'leave', 'late']:
                logger.warning(f"无效的考勤状态: {attendance.status}")
                return False
            
            # 检查是否已存在该员工当天的考勤记录
            existing = self.db_manager.execute_query(
                "SELECT id FROM attendance WHERE emp_id=? AND date=?",
                (attendance.emp_id, attendance.date),
                fetch_one=True
            )
            
            if existing:
                # 更新已有记录
                result = self.db_manager.execute_query(
                    """UPDATE attendance 
                    SET status=?, note=? 
                    WHERE id=?""",
                    (attendance.status, attendance.note, existing[0])
                )
            else:
                # 添加新记录
                result = self.db_manager.execute_query(
                    "INSERT INTO attendance (emp_id, date, status, note) VALUES (?, ?, ?, ?)",
                    (attendance.emp_id, attendance.date, attendance.status, attendance.note)
                )
            
            return result is not None
        except Exception as e:
            logger.error(f"添加考勤异常: {str(e)}")
            return False
    
    def delete_attendance(self, emp_id, date):
        """删除指定员工在指定日期的考勤记录"""
        try:
            # 输入验证
            if not Validator.is_valid_emp_id(emp_id):
                logger.warning(f"无效的员工ID格式: {emp_id}")
                return False
            if not Validator.is_valid_date(date):
                logger.warning(f"无效的日期格式: {date}")
                return False

            # 检查记录是否存在
            existing = self.db_manager.execute_query(
                "SELECT id FROM attendance WHERE emp_id=? AND date=?",
                (emp_id, date),
                fetch_one=True
            )

            if not existing:
                logger.warning(f"未找到员工 {emp_id} 在 {date} 的考勤记录")
                return False

            # 删除记录
            result = self.db_manager.execute_query(
                "DELETE FROM attendance WHERE id=?",
                (existing[0],)
            )

            if result:
                logger.info(f"已删除员工 {emp_id} 在 {date} 的考勤记录")
            else:
                logger.error(f"删除员工 {emp_id} 在 {date} 的考勤记录失败")

            return result is not None
        except Exception as e:
            logger.error(f"删除考勤记录异常: {str(e)}")
            return False

    def calculate_tax(self, salary):
        """计算个人所得税"""
        if not Validator.is_valid_salary(salary):
            logger.warning(f"无效的工资数据: {salary}")
            return 0
        
        # 查询适用的税率
        result = self.db_manager.execute_query(
            "SELECT rate, deduction, min_salary FROM tax_rates WHERE min_salary <= ? AND max_salary > ?",
            (salary, salary),
            fetch_one=True
        )
        
        if not result:
            return 0
        
        rate, deduction, min_salary = result
        # 正确的个人所得税计算方式：(应纳税所得额 - 起征点) * 税率 - 速算扣除数
        # 这里min_salary就是该区间的起征点
        tax = (salary - min_salary) * rate - deduction
        return round(max(tax, 0), 2)  # 确保税金不为负数并保留两位小数
    def calculate_salary(self, emp_id, month):
        # 获取员工信息
        emp_row = self.db_manager.execute_query(
            "SELECT * FROM employees WHERE emp_id=?",
            (emp_id,),
            fetch_one=True
        )
        
        if not emp_row:
            return None
        
        # 检查字段数量，适配不同的表结构
        if len(emp_row) == 6:  # 测试表结构: emp_id, name, base_salary, join_date, status, leave_date
            emp_id, name, base_salary, hire_date, status, leave_date = emp_row
            employee = Employee(emp_id, name, "", "", base_salary, hire_date, "", status, leave_date)
        else:  # 原始表结构
            employee = Employee(*emp_row)
        
        # 解析月份
        year, month_num = map(int, month.split('-'))
        days_in_month = calendar.monthrange(year, month_num)[1]
        
        # 计算实际工作天数
        start_date = f"{year}-{month_num:02d}-01"
        end_date = f"{year}-{month_num:02d}-{days_in_month}"
        
        # 检查员工是否在当月在职
        is_employed = True
        if employee.status == 'inactive' and employee.leave_date:
            leave_date = datetime.datetime.strptime(employee.leave_date, '%Y-%m-%d').date()
            start_month = datetime.date(year, month_num, 1)
            if leave_date < start_month:
                is_employed = False
        
        if not is_employed:
            return None
        
        # 获取当月考勤
        attendance_records = self.db_manager.execute_query(
            "SELECT status FROM attendance WHERE emp_id=? AND date BETWEEN ? AND ?",
            (emp_id, start_date, end_date),
            fetch_all=True
        )
        
        # 计算工作日（假设周一到周五是工作日）
        weekdays = 0
        for day in range(1, days_in_month + 1):
            date = datetime.date(year, month_num, day)
            if date.weekday() < 5:  # 0-4表示周一到周五
                weekdays += 1
        
        # 计算出勤天数
        present_days = sum(1 for record in attendance_records if record and record[0] == 'present')
        
        # 计算缺勤天数
        absent_days = sum(1 for record in attendance_records if record and record[0] == 'absent')
        
        # 计算请假天数
        leave_days = sum(1 for record in attendance_records if record and record[0] == 'leave')
        
        # 直接使用员工管理中的基本工资，并确保转换为浮点数
        base_salary = float(employee.base_salary) if employee.base_salary else 0.0
        
        # 首先检查数据库中是否已经存在该员工当月的奖金和扣款记录
        existing_salary = self.db_manager.execute_query(
            "SELECT bonus, deduction FROM salaries WHERE emp_id=? AND month=?",
            (emp_id, month),
            fetch_one=True
        )
        
        if existing_salary and existing_salary[0] is not None:
            # 如果数据库中已有奖金记录，则使用数据库中的值
            bonus = float(existing_salary[0])
        else:
            # 否则默认为0
            bonus = 0
        
        if existing_salary and existing_salary[1] is not None:
            # 如果数据库中已有扣款记录，则使用数据库中的值
            deduction = float(existing_salary[1])
        else:
            # 否则根据缺席和请假的累计次数计算扣款金额：每累计一次扣50元
            total_absences = absent_days + leave_days
            deduction = total_absences * 50
        
        # 计算个人所得税（基于应纳税所得额：基本工资+奖金-扣款）
        taxable_income = base_salary + bonus - deduction
        tax = self.calculate_tax(taxable_income)

        # 计算最终工资（基本工资 + 奖金 - 扣款 - 个人所得税）
        final_salary = base_salary + bonus - deduction - tax
        # 保留两位小数
        final_salary = round(final_salary, 2)
        
        # 返回工资详情
        return {
            'emp_id': employee.emp_id,
            'name': employee.name,
            'base_salary': base_salary,
            'bonus': bonus,
            'deduction': deduction,
            'tax': tax,
            'final_salary': final_salary
        }
    def update_employee_bonus(self, emp_id, month, new_bonus):
        """更新员工的奖金并重新计算相关工资数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取当前工资记录
            cursor.execute(
                "SELECT base_salary, deduction FROM salaries WHERE emp_id=? AND month=?",
                (emp_id, month)
            )
            salary_data = cursor.fetchone()
            
            if not salary_data:
                conn.close()
                logger.warning(f"未找到员工 {emp_id} 在 {month} 月份的工资记录")
                return False
            
            base_salary, deduction = salary_data
            
            # 重新计算个人所得税（基于新的应纳税所得额）
            taxable_income = base_salary + new_bonus - deduction
            tax = self.calculate_tax(taxable_income)
            
            # 重新计算最终工资
            final_salary = base_salary + new_bonus - deduction - tax
            final_salary = round(final_salary, 2)
            
            # 更新数据库
            cursor.execute(
                """UPDATE salaries 
                SET bonus=?, final_salary=? 
                WHERE emp_id=? AND month=?""",
                (new_bonus, final_salary, emp_id, month)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"已更新员工 {emp_id} 在 {month} 月份的奖金为: {new_bonus}")
            return True
        except Exception as e:
            logger.error(f"更新奖金失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    # 修复缩进问题
    def generate_salary_sheet(self, month):
        """生成指定月份的工资表"""
        # 获取所有在职员工
        employees = self.get_all_employees('active')
        
        if not employees:
            logger.warning("没有找到在职员工")
            return []
        
        salary_sheet = []
        
        # 遍历所有员工
        for employee in employees:
            # 首先检查该员工该月份是否已有工资记录
            existing_salary = self.db_manager.execute_query(
                "SELECT base_salary, bonus, deduction, final_salary FROM salaries WHERE emp_id=? AND month=?",
                (employee.emp_id, month),
                fetch_one=True
            )
            
            if existing_salary:
                # 如果已有记录，则直接使用
                base_salary, bonus, deduction, final_salary = existing_salary
                salary_detail = {
                    'emp_id': employee.emp_id,
                    'name': employee.name,
                    'base_salary': float(base_salary),
                    'bonus': float(bonus) if bonus is not None else 0,
                    'deduction': float(deduction) if deduction is not None else 0,
                    'final_salary': float(final_salary)
                }
                # 计算应纳税额（即使数据库中没有存储）
                taxable_income = base_salary + bonus - deduction
                salary_detail['tax'] = self.calculate_tax(taxable_income)
            else:
                # 如果没有记录，则计算工资
                salary_detail = self.calculate_salary(employee.emp_id, month)
                
                if salary_detail:
                    # 保存到数据库
                    # 注意：salaries表没有tax列，最终工资已经扣除了个税
                    self.db_manager.execute_query(
                        "INSERT INTO salaries (emp_id, month, base_salary, bonus, deduction, final_salary, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (salary_detail['emp_id'], month, salary_detail['base_salary'], 
                         salary_detail['bonus'], salary_detail['deduction'], 
                         salary_detail['final_salary'], 'unpaid')
                    )
            
            if salary_detail:
                salary_sheet.append(salary_detail)
        
        return salary_sheet
    def mark_salary_paid(self, emp_id, month):
        # 检查是否为管理员
        if not self.is_admin():
            logger.warning(f"非管理员用户 {self.current_user.username if self.current_user else '未知用户'} 尝试标记工资发放状态")
            return False
        
        payment_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        try:
            result = self.db_manager.execute_query(
                """UPDATE salaries 
                SET status='paid', payment_date=? 
                WHERE emp_id=? AND month=?""",
                (payment_date, emp_id, month)
            )
            return result > 0
        except Exception as e:
            logger.error(f"标记工资发放失败: {str(e)}")
            return False
            
    def mark_salary_unpaid(self, emp_id, month):
        """将工资标记为未发放状态
        
        参数:
            emp_id: 员工ID
            month: 月份 (YYYY-MM)
        """
        # 检查是否为管理员
        if not self.is_admin():
            logger.warning(f"非管理员用户 {self.current_user.username if self.current_user else '未知用户'} 尝试标记工资未发放状态")
            return False
        
        try:
            result = self.db_manager.execute_query(
                """UPDATE salaries 
                SET status='unpaid', payment_date=NULL 
                WHERE emp_id=? AND month=?""",
                (emp_id, month)
            )
            return result > 0
        except Exception as e:
            logger.error(f"标记工资未发放失败: {str(e)}")
            return False

class LoginWindow:
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self.root.title("登录")
        
        # 获取全局屏幕适配实例
        self.screen_adapt = get_screen_adaptation()
        
        # 允许窗口调整大小，方便在不同尺寸的手机上显示
        self.root.resizable(True, True)
        self.root.configure(bg="white")
        
        # 添加响应式布局支持
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self.on_window_resize)
        
        # 初始化字体配置
        self.initialize_fonts()
        
        # 获取合适的内边距
        self.padding = self.screen_adapt.get_padding('large') if self.screen_adapt.is_mobile else self.screen_adapt.get_padding('medium')
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding=self.padding)
        self.main_frame.pack(fill="both", expand=True, padx=self.padding, pady=self.padding)
        
        # 添加响应式布局支持
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # 设置按钮样式使其更适合触摸
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", font=self.fonts['large'])
        
        # 创建UI元素
        self.create_ui_elements()
        
        # 绑定回车键
        self.root.bind("<Return>", lambda event: self.login())
        
        # 初始化计算器
        self.calculator = SalaryCalculator()
    
    def initialize_fonts(self):
        """初始化字体配置"""
        # 使用屏幕适配实例提供的字体配置
        self.fonts = {
            'small': self.screen_adapt.get_font_config('small'),
            'normal': self.screen_adapt.get_font_config('medium'),
            'large': self.screen_adapt.get_font_config('large'),
            'title': (self.screen_adapt.get_font_config('large')[0], 
                     self.screen_adapt.get_font_config('large')[1] + 4, 'bold')
        }
    
    def update_font_sizes(self):
        """更新字体大小 - 使用屏幕适配实例"""
        self.initialize_fonts()
    
    def update_font_size(self):
        """兼容性方法，确保调用update_font_size()时也能正常工作"""
        self.update_font_sizes()
    
    def create_ui_elements(self):
        """创建UI元素"""
        # 清除主框架中的所有元素
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 根据设备类型调整间距
        label_pady = self.screen_adapt.get_padding('large') if self.screen_adapt.is_mobile else 20
        input_pady = self.screen_adapt.get_padding('medium') if self.screen_adapt.is_mobile else 10
        
        # 标题
        ttk.Label(self.main_frame, text="工资表计算系统", font=self.fonts['title']).pack(pady=label_pady)
        
        # 用户名
        username_frame = ttk.Frame(self.main_frame)
        username_frame.pack(fill="x", pady=input_pady)
        
        # 在移动设备上使用更小的标签宽度
        label_width = 8 if self.screen_adapt.is_mobile else 10
        ttk.Label(username_frame, text="用户名: ", width=label_width, font=self.fonts['normal']).pack(side="left")
        
        self.username_var = tk.StringVar()
        entry_width = 25 if self.screen_adapt.is_mobile else 30
        ttk.Entry(username_frame, textvariable=self.username_var, width=entry_width, font=self.fonts['normal']).pack(side="left", fill="x", expand=True)
        
        # 密码
        password_frame = ttk.Frame(self.main_frame)
        password_frame.pack(fill="x", pady=input_pady)
        ttk.Label(password_frame, text="密码: ", width=label_width, font=self.fonts['normal']).pack(side="left")
        self.password_var = tk.StringVar()
        ttk.Entry(password_frame, textvariable=self.password_var, show="*", width=entry_width, font=self.fonts['normal']).pack(side="left", fill="x", expand=True)
        
        # 错误提示
        self.error_var = tk.StringVar()
        ttk.Label(self.main_frame, textvariable=self.error_var, foreground="red", font=self.fonts['small']).pack(pady=input_pady)
        
        # 登录按钮
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill="x", pady=label_pady)
        
        # 在移动设备上增加按钮内边距，更适合触摸
        button_ipady = 8 if self.screen_adapt.is_mobile else 5
        ttk.Button(button_frame, text="登录", command=self.login, style="Accent.TButton").pack(fill="x", ipady=button_ipady)
    
    def on_window_resize(self, event):
        """窗口大小变化时的处理函数"""
        # 避免无限循环调用
        if event.widget == self.root:
            # 获取新的窗口尺寸
            width = event.width
            height = event.height
            
            # 避免在窗口初始化时处理过小的窗口尺寸
            if width < 100 or height < 100:
                return
                
            # 更新字体大小
            self.update_font_sizes()
            
            # 更新按钮样式
            self.style.configure("Accent.TButton", font=self.fonts['large'])
            
            # 重新创建UI元素
            self.create_ui_elements()
            
            # 强制刷新UI
            self.root.update_idletasks()
    
    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            self.error_var.set("用户名和密码不能为空")
            return
        
        success, role = self.calculator.login(username, password)
        if success:
            # 不再销毁窗口，而是通过回调在同一个窗口中创建主应用
            self.callback(role, self.calculator)
        else:
            self.error_var.set("用户名或密码错误")

class ScreenAdaptation:
    """屏幕适配工具类，提供屏幕尺寸检测和自适应功能"""
    def __init__(self, root):
        # 获取屏幕尺寸
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # 判断是否是移动设备或小屏幕
        self.is_mobile = self.screen_width <= 800 or self.screen_height <= 600
        
        # 根据屏幕尺寸设置适配参数
        if self.is_mobile:
            self.window_width = int(self.screen_width * 0.95)  # 占用屏幕95%宽度
            self.window_height = int(self.screen_height * 0.95)  # 占用屏幕95%高度
            self.font_size_small = 10
            self.font_size_medium = 12
            self.font_size_large = 14
            self.padding_small = 2
            self.padding_medium = 4
            self.padding_large = 6
            self.button_width = 10
        else:
            self.window_width = 1024  # 默认桌面宽度
            self.window_height = 768   # 默认桌面高度
            self.font_size_small = 9
            self.font_size_medium = 11
            self.font_size_large = 13
            self.padding_small = 5
            self.padding_medium = 10
            self.padding_large = 15
            self.button_width = 12
    
    def apply_window_geometry(self, window):
        """应用窗口几何设置，使其居中显示"""
        # 计算窗口位置，使其居中
        x = (self.screen_width - self.window_width) // 2
        y = (self.screen_height - self.window_height) // 2
        
        # 设置窗口大小和位置
        window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
        # 在移动设备上，设置窗口为全屏
        if self.is_mobile:
            try:
                # 尝试设置为全屏
                window.attributes('-fullscreen', True)
                # 添加退出全屏的键绑定（ESC键）
                window.bind('<Escape>', lambda e: window.attributes('-fullscreen', False))
            except Exception:
                # 如果设置全屏失败，至少确保窗口最大化
                window.state('zoomed')
    
    def get_font_config(self, size_type='medium'):
        """获取字体配置"""
        font_sizes = {
            'small': self.font_size_small,
            'medium': self.font_size_medium,
            'large': self.font_size_large
        }
        return ('Microsoft YaHei', font_sizes.get(size_type, self.font_size_medium))
    
    def get_padding(self, size_type='medium'):
        """获取内边距配置"""
        paddings = {
            'small': self.padding_small,
            'medium': self.padding_medium,
            'large': self.padding_large
        }
        return paddings.get(size_type, self.padding_medium)
    
    def get_treeview_column_widths(self):
        """根据屏幕大小获取Treeview列宽配置"""
        if self.is_mobile:
            return {
                'emp_id': 60,
                'name': 80,
                'department': 90,
                'position': 90,
                'status': 60,
                'note': 120
            }
        else:
            return {
                'emp_id': 80,
                'name': 100,
                'department': 120,
                'position': 120,
                'status': 80,
                'note': 200
            }

# 全局屏幕适配实例
_screen_adaptation = None
def get_screen_adaptation():
    """获取全局屏幕适配实例"""
    global _screen_adaptation
    return _screen_adaptation

def main():
    # 创建登录窗口
    login_root = tk.Tk()
    login_root.title("工资计算系统 - 登录")
    
    # 初始化屏幕适配
    global _screen_adaptation
    _screen_adaptation = ScreenAdaptation(login_root)
    
    # 应用窗口几何设置
    _screen_adaptation.apply_window_geometry(login_root)
    
    # 记录屏幕适配信息到日志
    logger.info(f"屏幕检测结果 - 宽度: {_screen_adaptation.screen_width}, 高度: {_screen_adaptation.screen_height}")
    logger.info(f"是否移动设备: {_screen_adaptation.is_mobile}")
    
    def on_login_success(role, calculator):
        # 登录成功后创建主应用窗口
        # 不要创建新的Tk实例，而是重新使用登录窗口
        # 清空登录窗口
        for widget in login_root.winfo_children():
            widget.destroy()
        
        # 在同一个窗口中创建主应用
        app = SalaryCalculatorApp(login_root, role, calculator)
        # 不需要再调用mainloop，因为原始的login_root.mainloop()仍然在运行
    
    # 启动登录窗口
    login_window = LoginWindow(login_root, on_login_success)
    login_root.mainloop()

class AdaptiveDialog(tk.Toplevel):
    """自适应对话框类，支持根据屏幕尺寸自动调整大小和字体，特别优化了移动设备体验"""
    def __init__(self, parent, title="对话框", width_percent=0.7, height_percent=0.6):
        # 在Android设备上，我们需要特别处理tk属性
        # 尝试安全地调用父类初始化
        try:
            super().__init__(parent)
        except Exception as e:
            # 如果父类初始化失败，创建一个基本对象并手动设置必要的属性
            import tkinter as tk
            self.parent = parent
            self.title_text = title
            
        # 确保tk属性已初始化，特别针对Android环境优化
        if not hasattr(self, 'tk') or self.tk is None:
            # 尝试从父窗口获取tk属性
            if parent and hasattr(parent, 'tk') and parent.tk is not None:
                self.tk = parent.tk
            elif hasattr(tk, '_default_root') and tk._default_root is not None and hasattr(tk._default_root, 'tk'):
                self.tk = tk._default_root.tk
            else:
                # 对于Android，我们需要一个更安全的后备方案
                # 尝试直接创建一个临时的根窗口来获取tk引用
                try:
                    temp_root = tk.Tk()
                    temp_root.withdraw()  # 隐藏窗口
                    self.tk = temp_root.tk
                    temp_root.destroy()  # 销毁窗口但保留tk引用
                except Exception:
                    # 如果所有尝试都失败，设置一个空对象作为最后的后备
                    class DummyTk:
                        def getvar(self, name, value=None):
                            return value
                        def setvar(self, name, value):
                            pass
                    self.tk = DummyTk()
        
        # 设置标题
        if hasattr(self, 'title'):
            self.title(title)
        
        self.parent = parent
        # 获取屏幕尺寸
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
        
        # 判断是否是移动设备或小屏幕
        self.is_mobile = self.screen_width <= 800 or self.screen_height <= 600
        
        # 移动设备上使用更大的宽度百分比
        width_percent = 0.9 if self.is_mobile else width_percent
        height_percent = 0.95 if self.is_mobile else height_percent
        
        # 设置窗口初始尺寸，根据屏幕大小自适应
        initial_width = int(self.screen_width * width_percent)
        initial_height = int(self.screen_height * height_percent)
        
        # 确保窗口尺寸不会太小
        min_width = 280 if self.is_mobile else 300
        min_height = 350 if self.is_mobile else 400
        initial_width = max(min_width, initial_width)
        initial_height = max(min_height, initial_height)
        
        # 在移动设备上使用全屏或接近全屏的尺寸
        if self.is_mobile:
            # 先设置为指定尺寸
            self.geometry(f"{initial_width}x{initial_height}")
            # 然后请求全屏或最大化（取决于平台支持）
            try:
                self.attributes('-fullscreen', True)
            except tk.TclError:
                # 如果平台不支持全屏模式，至少最大化窗口
                self.state('zoomed')
        else:
            self.geometry(f"{initial_width}x{initial_height}")
        
        # 允许窗口调整大小
        self.resizable(True, True)
        
        # 设置窗口居中
        self.center_window(initial_width, initial_height)
        
        # 使对话框获取焦点，防止用户操作主窗口
        self.transient(parent)
        self.grab_set()
        
        # 绑定窗口大小变化事件
        self.bind("<Configure>", self.on_window_resize)
        
        # 在移动设备上添加返回按钮或ESC键退出全屏
        if self.is_mobile:
            self.bind("<Escape>", lambda e: self.attributes('-fullscreen', False))
        
        # 创建主框架
        padding = 10 if self.is_mobile else 20
        self.main_frame = ttk.Frame(self, padding=padding)
        self.main_frame.pack(fill="both", expand=True, padx=padding, pady=padding)
        
        # 添加响应式布局支持
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # 初始化样式管理器
        self.style = ttk.Style()
        
        # 初始化字体大小
        self.update_font_sizes()
        
    def center_window(self, width, height):
        """将窗口居中显示"""
        x = (self.screen_width // 2) - (width // 2)
        y = (self.screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def update_font_sizes(self):
        """根据屏幕宽度和设备类型更新字体大小"""
        # 获取当前窗口大小
        width = self.winfo_width()
        
        # 为移动设备使用不同的字体计算方式，确保字体更大更易读
        if self.is_mobile:
            base_font_size = max(12, int(width / 25))  # 移动设备上字体更大，最小12号字
        else:
            base_font_size = max(10, int(width / 40))  # 桌面设备上的字体计算方式
        
        # 创建不同大小的字体配置
        self.fonts = {
            'small': ("SimHei", max(10, base_font_size - 2)),  # 确保小字体也有足够的可读性
            'normal': ("SimHei", base_font_size),
            'large': ("SimHei", base_font_size + 2),
            'title': ("SimHei", base_font_size + 4)
        }
        
        # 更新按钮样式，为移动设备优化触摸体验
        if self.is_mobile:
            # 移动设备上按钮字体更大，边框更宽
            self.style.configure("Accent.TButton", 
                                font=(*self.fonts['large'], "bold"),
                                padding=(15, 10))  # 增加内边距使按钮更大
            self.style.configure("TButton", 
                                font=self.fonts['normal'],
                                padding=(12, 8))  # 增加内边距
        else:
            # 桌面设备上的标准样式
            self.style.configure("Accent.TButton", font=(*self.fonts['large'], "bold"))
            self.style.configure("TButton", font=self.fonts['normal'])
        
        # 更新其他组件的字体样式
        self.style.configure("TLabel", font=self.fonts['normal'])
        self.style.configure("TEntry", font=self.fonts['normal'])
        self.style.configure("TCombobox", font=self.fonts['normal'])
        
        # 为移动设备优化输入框，使其更适合触摸
        if self.is_mobile:
            self.style.configure("TEntry", padding=10)  # 增加输入框内边距
            self.style.configure("TCombobox", padding=10)  # 增加下拉框内边距
        
    def on_window_resize(self, event):
        """窗口大小变化时的处理函数"""
        # 避免无限循环调用
        if event.widget == self:
            # 获取新的窗口尺寸
            width = event.width
            height = event.height
            
            # 避免在窗口初始化时处理过小的窗口尺寸
            if width < 100 or height < 100:
                return
                
            # 更新字体大小
            self.update_font_sizes()
            
            # 强制刷新UI
            self.update_idletasks()

class SalaryCalculatorApp:
    def __init__(self, root, user_role, calculator):
        self.root = root
        
        # 确保tk属性已初始化，特别针对Android环境优化
        if not hasattr(self, 'tk') or self.tk is None:
            # 尝试从root窗口获取tk属性
            if hasattr(root, 'tk') and root.tk is not None:
                self.tk = root.tk
            elif hasattr(tk, '_default_root') and tk._default_root is not None and hasattr(tk._default_root, 'tk'):
                self.tk = tk._default_root.tk
            else:
                # 对于Android，我们需要一个更安全的后备方案
                try:
                    # 尝试创建一个临时的根窗口来获取tk引用
                    temp_root = tk.Tk()
                    temp_root.withdraw()  # 隐藏窗口
                    self.tk = temp_root.tk
                    temp_root.destroy()  # 销毁窗口但保留tk引用
                except Exception:
                    # 如果所有尝试都失败，设置一个空对象作为最后的后备
                    class DummyTk:
                        def getvar(self, name, value=None):
                            return value
                        def setvar(self, name, value):
                            pass
                    self.tk = DummyTk()
        
        self.user_role = user_role
        self.calculator = calculator
        self.root.title("工资表计算系统")
        
        # 获取全局屏幕适配实例
        self.screen_adapt = get_screen_adaptation()
        
        # 应用窗口几何设置
        self.screen_adapt.apply_window_geometry(self.root)
        
        # 使用屏幕适配的移动设备标识
        self.is_mobile = self.screen_adapt.is_mobile
        
        # 移除最小尺寸限制，让窗口可以自由调整大小
        # self.root.minsize(1000, 600) 
        
        # 初始化字体配置
        self.initialize_fonts()
        
        # 添加响应式布局支持
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 初始化考勤管理相关变量
        self.status_filter_var = tk.StringVar(value='all')
        self.start_date_var = tk.StringVar(value=datetime.datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        self.end_date_var = tk.StringVar(value=datetime.datetime.now().strftime('%Y-%m-%d'))
        
        # 设置中文字体，使用屏幕适配实例的配置
        self.style = ttk.Style()
        
        # 根据屏幕适配配置设置UI样式
        if self.screen_adapt.is_mobile:
            # 移动设备上字体更大，更适合触摸
            self.style.configure("TButton", font=self.screen_adapt.get_font_config('medium'), padding=(12, 8))
            self.style.configure("TLabel", font=self.screen_adapt.get_font_config('medium'))
            self.style.configure("TEntry", font=self.screen_adapt.get_font_config('medium'), padding=10)
            self.style.configure("TCombobox", font=self.screen_adapt.get_font_config('medium'), padding=10)
            self.style.configure("Treeview", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("Treeview.Heading", font=(*self.screen_adapt.get_font_config('small'), "bold"))
            # 为按钮添加强调样式
            self.style.configure("Accent.TButton", font=(*self.screen_adapt.get_font_config('medium'), "bold"), padding=(15, 10))
        else:
            # 桌面设备上的标准样式
            self.style.configure("TButton", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("TLabel", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("TEntry", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("TCombobox", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("Treeview", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("Treeview.Heading", font=(*self.screen_adapt.get_font_config('small'), "bold"))
        
        # 创建标签页
        self.notebook = ttk.Notebook(root)
        
        # 根据屏幕适配设置边距
        pad_size = self.screen_adapt.get_padding('small') if self.screen_adapt.is_mobile else 5
        self.notebook.pack(fill="both", expand=True, padx=pad_size, pady=pad_size)
        
        # 创建各个标签页
        self.employee_frame = ttk.Frame(self.notebook)
        self.attendance_frame = ttk.Frame(self.notebook)
        self.salary_frame = ttk.Frame(self.notebook)
        self.revenue_frame = ttk.Frame(self.notebook)
        self.profit_frame = ttk.Frame(self.notebook)
        
        # 添加标签页到notebook
        self.notebook.add(self.employee_frame, text="员工管理")
        self.notebook.add(self.attendance_frame, text="考勤管理")
        self.notebook.add(self.salary_frame, text="工资管理")
        self.notebook.add(self.revenue_frame, text="收入管理")
        self.notebook.add(self.profit_frame, text="利润计算")
        
        # 创建用户管理标签页
        self.user_management_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.user_management_frame, text="用户管理")
        
        # 创建备份恢复标签页
        self.backup_restore_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_restore_frame, text="备份恢复")
        
        # 创建税率管理标签页
        self.tax_rate_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tax_rate_frame, text="税率管理")
        
        # 根据用户角色设置权限
        if self.user_role != 'admin':
            # 普通操作员隐藏利润计算、用户管理、备份恢复和税率管理标签页
            # 允许普通操作员访问员工管理和收入管理
            self.notebook.hide(self.profit_frame)
            self.notebook.hide(self.user_management_frame)
            self.notebook.hide(self.backup_restore_frame)
            self.notebook.hide(self.tax_rate_frame)
        else:
            # 管理员初始化用户管理、备份恢复和税率管理页面
            self.init_user_management_frame()
            self.init_backup_restore_frame()
            self.init_tax_rate_frame()
            
            # 初始化进销存管理模块
            from inventory_manager import InventoryManager
            self.inventory_manager = InventoryManager(self.calculator.db_path, self.root, self.notebook, self.user_role, self.calculator.current_user)
        
        # 初始化各个页面
        self.init_employee_frame()
        self.init_attendance_frame()
        self.init_salary_frame()
        self.init_revenue_frame()
        
        # 初始化支出管理
        from expense_manager import ExpenseManager
        self.expense_manager = ExpenseManager(self.calculator.db_path, self.root, self.notebook, self.user_role)
        
        self.init_profit_frame()
        
        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 显示当前用户信息
        self.status_var = tk.StringVar()
        self.status_var.set(f"当前用户: {self.calculator.current_user.username} ({self.user_role})")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
        
        # 设置自动备份（每天19:00）
        if self.user_role == 'admin':
            self.setup_auto_backup()
            
        # 添加屏幕尺寸变化事件处理
        self.root.bind("<Configure>", self.on_window_resize)
        # 初始化屏幕适配
        self.adjust_ui_for_screen_size()
    
    def setup_auto_backup(self):
        """设置自动备份任务，每天19:00执行"""
        def auto_backup():
            """自动备份函数"""
            logger.info("执行自动备份")
            success, msg = self.calculator.backup_database()
            if success:
                logger.info(f"自动备份成功: {msg}")
            else:
                logger.error(f"自动备份失败: {msg}")
            
            # 设置下一天的备份
            self.setup_auto_backup()
        
        # 获取当前时间
        now = datetime.datetime.now()
        
        # 设置目标时间为今天19:40
        target = now.replace(hour=19, minute=40, second=0, microsecond=0)
        
        # 如果今天19:00已经过了，则设置为明天19:00
        if now > target:
            target += datetime.timedelta(days=1)
        
        # 计算时间差
        delta = target - now
        
        # 设置定时器
        self.backup_timer = threading.Timer(delta.total_seconds(), auto_backup)
        self.backup_timer.daemon = True  # 设置为守护线程，主程序结束时自动终止
        self.backup_timer.start()
        logger.info(f"已设置自动备份，下次备份时间: {target}")
        
    def initialize_fonts(self):
        """初始化字体配置"""
        # 使用屏幕适配实例提供的字体配置
        self.fonts = {
            'small': self.screen_adapt.get_font_config('small'),
            'medium': self.screen_adapt.get_font_config('medium'),
            'large': self.screen_adapt.get_font_config('large')
        }
    
    def update_font_size(self):
        """兼容性方法，确保调用update_font_size()时也能正常工作"""
        # 使用屏幕适配实例更新字体
        self.update_font_configuration()
    
    def update_font_configuration(self):
        """更新字体配置 - 使用屏幕适配实例"""
        self.initialize_fonts()
        
        # 更新样式
        if self.screen_adapt.is_mobile:
            self.style.configure("TButton", font=self.screen_adapt.get_font_config('medium'))
            self.style.configure("TLabel", font=self.screen_adapt.get_font_config('medium'))
            self.style.configure("TEntry", font=self.screen_adapt.get_font_config('medium'))
            self.style.configure("TCombobox", font=self.screen_adapt.get_font_config('medium'))
            self.style.configure("Treeview", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("Treeview.Heading", font=(*self.screen_adapt.get_font_config('small'), "bold"))
            self.style.configure("Accent.TButton", font=(*self.screen_adapt.get_font_config('medium'), "bold"))
        else:
            self.style.configure("TButton", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("TLabel", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("TEntry", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("TCombobox", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("Treeview", font=self.screen_adapt.get_font_config('small'))
            self.style.configure("Treeview.Heading", font=(*self.screen_adapt.get_font_config('small'), "bold"))
        
    def update_font_sizes(self):
        """兼容性方法，使用屏幕适配实例更新字体大小"""
        self.update_font_configuration()
    
    def on_window_resize(self, event):
        """窗口大小变化时的处理函数 - 使用屏幕适配"""
        # 避免无限循环调用
        if event.widget == self.root:
            self.adjust_ui_for_screen_size()
    
    def adjust_ui_for_screen_size(self):
        """根据屏幕尺寸调整UI布局 - 使用屏幕适配实例"""
        # 获取当前窗口大小
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # 避免在窗口初始化时处理过小的窗口尺寸
        if width < 100 or height < 100:
            return
            
        logger.info(f"调整UI适应屏幕大小: {width}x{height} (移动设备: {self.is_mobile})")
        
        # 更新字体配置
        self.update_font_configuration()
        
        # 使用屏幕适配设置字体大小
        font_size = self.screen_adapt.get_font_size(width)
        
        # 为matplotlib设置字体大小
        plt.rcParams["font.size"] = font_size
        
        # 根据屏幕适配获取边距
        if self.screen_adapt.is_mobile:
            # 移动设备 - 使用屏幕适配的小边距
            padx = self.screen_adapt.get_padding('small')
            pady = self.screen_adapt.get_padding('small')
        elif width < 1000:
            # 中等屏幕（平板）- 使用中等边距
            padx = 5
            pady = 5
        else:
            # 大屏幕（桌面）- 使用屏幕适配的正常边距
            padx = self.screen_adapt.get_padding('normal')
            pady = self.screen_adapt.get_padding('normal')
        
        # 更新标签页的边距
        if hasattr(self, 'notebook'):
            try:
                # 重新设置notebook的边距
                self.notebook.pack(fill="both", expand=True, padx=padx, pady=pady)
            except Exception as e:
                logger.error(f"更新标签页边距失败: {str(e)}")
        
        # 强制刷新UI
        self.root.update_idletasks()
    
    def on_tab_changed(self, event):
        # 当切换到员工管理标签页时，刷新员工列表
        if self.notebook.select() == str(self.employee_frame):
            self.refresh_employee_list()
        # 当切换到工资管理标签页时，刷新工资表
        elif self.notebook.select() == str(self.salary_frame):
            self.generate_salary_sheet()
        # 当切换到收入管理标签页时，刷新收入列表
        elif self.notebook.select() == str(self.revenue_frame):
            self.refresh_revenue_list()
        # 当切换到利润计算标签页时，刷新利润数据
        elif self.notebook.select() == str(self.profit_frame):
            self.calculate_and_display_profit()
        # 当切换到用户管理标签页时，刷新用户列表
        elif self.notebook.select() == str(self.user_management_frame):
            self.refresh_user_list()
        # 当切换到备份恢复标签页时，刷新备份列表
        elif self.notebook.select() == str(self.backup_restore_frame):
            self.refresh_backup_list()
    
    def init_tax_rate_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.tax_rate_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 添加税率按钮
        ttk.Button(control_frame, text="添加税率", command=self.add_tax_rate).pack(side="left", padx=5)
        
        # 修改税率按钮
        ttk.Button(control_frame, text="修改税率", command=self.edit_tax_rate).pack(side="left", padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_tax_rate_list).pack(side="left", padx=5)
        
        # 税率列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("id", "min_salary", "max_salary", "rate", "deduction")
        self.tax_rate_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.tax_rate_tree.heading("id", text="ID")
        self.tax_rate_tree.heading("min_salary", text="起征点")
        self.tax_rate_tree.heading("max_salary", text="上限")
        self.tax_rate_tree.heading("rate", text="税率")
        self.tax_rate_tree.heading("deduction", text="速算扣除数")
        
        # 设置列宽
        self.tax_rate_tree.column("id", width=50)
        self.tax_rate_tree.column("min_salary", width=100, anchor="e")
        self.tax_rate_tree.column("max_salary", width=100, anchor="e")
        self.tax_rate_tree.column("rate", width=100, anchor="e")
        self.tax_rate_tree.column("deduction", width=100, anchor="e")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tax_rate_tree.yview)
        self.tax_rate_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.tax_rate_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 刷新税率列表
        self.refresh_tax_rate_list()
    
    def refresh_tax_rate_list(self):
        # 清空Treeview
        for item in self.tax_rate_tree.get_children():
            self.tax_rate_tree.delete(item)
        
        # 使用DatabaseManager获取税率列表
        tax_rates = self.calculator.db_manager.execute_query(
            "SELECT id, min_salary, max_salary, rate, deduction FROM tax_rates ORDER BY min_salary",
            fetch_all=True
        )
        
        # 添加到Treeview
        if tax_rates:
            for rate in tax_rates:
                id, min_salary, max_salary, rate_value, deduction = rate
                max_salary_text = "无限" if max_salary == float('inf') else f"{max_salary:.2f}"
                rate_text = f"{rate_value:.2%}"
                self.tax_rate_tree.insert("", tk.END, values=(id, f"{min_salary:.2f}", max_salary_text, rate_text, f"{deduction:.2f}"))
    
    def add_tax_rate(self):
        # 创建添加税率对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加税率", width_percent=0.6, height_percent=0.4)
        
        # 起征点
        min_salary_frame = ttk.Frame(dialog.main_frame)
        min_salary_frame.pack(fill="x", padx=10, pady=5)
        # 为标签设置合适的宽度
        label_width = 18 if dialog.winfo_width() < 500 else 15
        ttk.Label(min_salary_frame, text="起征点: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        min_salary_var = tk.DoubleVar()
        ttk.Entry(min_salary_frame, textvariable=min_salary_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        
        # 上限
        max_salary_frame = ttk.Frame(dialog.main_frame)
        max_salary_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(max_salary_frame, text="上限: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        max_salary_var = tk.DoubleVar()
        ttk.Entry(max_salary_frame, textvariable=max_salary_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Checkbutton(max_salary_frame, text="无限", variable=tk.BooleanVar(), command=lambda: max_salary_var.set(float('inf')) if max_salary_var.get() != float('inf') else max_salary_var.set(0), font=dialog.fonts['normal']).pack(side="left", padx=5)
        
        # 税率
        rate_frame = ttk.Frame(dialog.main_frame)
        rate_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(rate_frame, text="税率: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        rate_var = tk.DoubleVar()
        ttk.Entry(rate_frame, textvariable=rate_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Label(rate_frame, text="%", font=dialog.fonts['normal']).pack(side="left", padx=5)
        
        # 速算扣除数
        deduction_frame = ttk.Frame(dialog.main_frame)
        deduction_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(deduction_frame, text="速算扣除数: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        deduction_var = tk.DoubleVar()
        ttk.Entry(deduction_frame, textvariable=deduction_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 确认按钮
        def confirm():
            try:
                min_salary = min_salary_var.get()
                max_salary = max_salary_var.get()
                rate = rate_var.get() / 100  # 转换为小数
                deduction = deduction_var.get()
                
                # 验证输入
                if min_salary < 0 or max_salary <= min_salary or rate < 0 or rate > 1 or deduction < 0:
                    messagebox.showerror("错误", "请输入有效的税率信息！")
                    return
                
                # 保存到数据库
                result = self.calculator.db_manager.execute_query(
                    "INSERT INTO tax_rates (min_salary, max_salary, rate, deduction) VALUES (?, ?, ?, ?)",
                    (min_salary, max_salary, rate, deduction)
                )
                
                if not result:
                    messagebox.showerror("错误", "添加税率失败，数据库操作未成功！")
                    return
                
                messagebox.showinfo("成功", "税率添加成功！")
                dialog.destroy()
                self.refresh_tax_rate_list()
            except Exception as e:
                messagebox.showerror("错误", f"添加税率失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side="left", padx=10, expand=True)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10, expand=True)
    
    def edit_tax_rate(self):
        # 获取选中的税率
        selected_item = self.tax_rate_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个税率！")
            return
        
        # 获取税率ID
        item_values = self.tax_rate_tree.item(selected_item[0])["values"]
        tax_id = item_values[0]
        
        # 使用DatabaseManager获取税率信息
        rate_info = self.calculator.db_manager.execute_query(
            "SELECT min_salary, max_salary, rate, deduction FROM tax_rates WHERE id=?",
            (tax_id,),
            fetch_one=True
        )
        
        if not rate_info:
            messagebox.showerror("错误", "找不到指定的税率信息！")
            return
        
        min_salary, max_salary, rate, deduction = rate_info
        
        # 创建修改税率对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "修改税率", width_percent=0.6, height_percent=0.4)
        
        # 起征点
        min_salary_frame = ttk.Frame(dialog.main_frame)
        min_salary_frame.pack(fill="x", padx=10, pady=5)
        # 为标签设置合适的宽度
        label_width = 18 if dialog.winfo_width() < 500 else 15
        ttk.Label(min_salary_frame, text="起征点: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        min_salary_var = tk.DoubleVar(value=min_salary)
        ttk.Entry(min_salary_frame, textvariable=min_salary_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        
        # 上限
        max_salary_frame = ttk.Frame(dialog.main_frame)
        max_salary_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(max_salary_frame, text="上限: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        max_salary_var = tk.DoubleVar(value=max_salary)
        ttk.Entry(max_salary_frame, textvariable=max_salary_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        is_infinite = tk.BooleanVar(value=max_salary == float('inf'))
        ttk.Checkbutton(max_salary_frame, text="无限", variable=is_infinite, command=lambda: max_salary_var.set(float('inf')) if is_infinite.get() else max_salary_var.set(0), font=dialog.fonts['normal']).pack(side="left", padx=5)
        
        # 税率
        rate_frame = ttk.Frame(dialog.main_frame)
        rate_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(rate_frame, text="税率: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        rate_var = tk.DoubleVar(value=rate * 100)  # 转换为百分比
        ttk.Entry(rate_frame, textvariable=rate_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Label(rate_frame, text="%", font=dialog.fonts['normal']).pack(side="left", padx=5)
        
        # 速算扣除数
        deduction_frame = ttk.Frame(dialog.main_frame)
        deduction_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(deduction_frame, text="速算扣除数: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        deduction_var = tk.DoubleVar(value=deduction)
        ttk.Entry(deduction_frame, textvariable=deduction_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 确认按钮
        def confirm():
            try:
                new_min_salary = min_salary_var.get()
                new_max_salary = float('inf') if is_infinite.get() else max_salary_var.get()
                new_rate = rate_var.get() / 100  # 转换为小数
                new_deduction = deduction_var.get()
                
                # 验证输入
                if new_min_salary < 0 or new_max_salary <= new_min_salary or new_rate < 0 or new_rate > 1 or new_deduction < 0:
                    messagebox.showerror("错误", "请输入有效的税率信息！")
                    return
                
                # 更新数据库
                result = self.calculator.db_manager.execute_query(
                    "UPDATE tax_rates SET min_salary=?, max_salary=?, rate=?, deduction=? WHERE id=?",
                    (new_min_salary, new_max_salary, new_rate, new_deduction, tax_id)
                )
                
                if not result:
                    messagebox.showerror("错误", "更新税率失败，数据库操作未成功！")
                    return
                
                messagebox.showinfo("成功", "税率更新成功！")
                dialog.destroy()
                self.refresh_tax_rate_list()
            except Exception as e:
                messagebox.showerror("错误", f"更新税率失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side="left", padx=10, expand=True)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10, expand=True)
    
    def init_backup_restore_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.backup_restore_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 创建备份按钮
        ttk.Button(control_frame, text="创建备份", command=self.create_backup).pack(side="left", padx=5)
        
        # 恢复备份按钮
        ttk.Button(control_frame, text="恢复备份", command=self.restore_from_backup).pack(side="left", padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_backup_list).pack(side="left", padx=5)
        
        # 删除备份按钮
        ttk.Button(control_frame, text="删除备份", command=self.delete_backup).pack(side="left", padx=5)
        
        # 备份列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("id", "backup_time", "file_path", "size")
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.backup_tree.heading("id", text="ID")
        self.backup_tree.heading("backup_time", text="备份时间")
        self.backup_tree.heading("file_path", text="文件路径")
        self.backup_tree.heading("size", text="文件大小 (KB)")
        
        # 设置列宽
        self.backup_tree.column("id", width=50)
        self.backup_tree.column("backup_time", width=180)
        self.backup_tree.column("file_path", width=400)
        self.backup_tree.column("size", width=100, anchor="e")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.backup_tree.yview)
        self.backup_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.backup_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 刷新备份列表
        self.refresh_backup_list()
    
    def refresh_backup_list(self):
        # 清空Treeview
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # 获取所有备份记录
        backups = self.calculator.get_all_backups()
        
        # 添加到Treeview
        for backup in backups:
            backup_id, backup_time, file_path, size = backup
            size_kb = round(size / 1024, 2)  # 转换为KB
            self.backup_tree.insert("", tk.END, values=(backup_id, backup_time, file_path, size_kb))
    
    def create_backup(self):
        # 创建备份
        success, msg = self.calculator.backup_database()
        if success:
            messagebox.showinfo("成功", msg)
            self.refresh_backup_list()
        else:
            messagebox.showerror("错误", msg)
    
    def restore_from_backup(self):
        # 获取选中的备份
        selected_item = self.backup_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个备份！")
            return
        
        # 获取备份ID
        item_values = self.backup_tree.item(selected_item[0])["values"]
        backup_id = item_values[0]
        
        # 确认恢复
        if messagebox.askyesno("确认", "确定要恢复选中的备份吗？这将覆盖当前数据库！"):
            success, msg = self.calculator.restore_database(backup_id)
    
    def delete_backup(self):
        # 获取选中的备份
        selected_item = self.backup_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个备份！")
            return
        
        # 获取备份ID和信息
        item_values = self.backup_tree.item(selected_item[0])["values"]
        backup_id = item_values[0]
        backup_time = item_values[1]
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除 {backup_time} 的备份吗？此操作不可恢复！"):
            success, msg = self.calculator.delete_backup(backup_id)
            if success:
                messagebox.showinfo("成功", msg)
                # 刷新列表显示最新数据
                self.refresh_backup_list()
            else:
                messagebox.showerror("错误", msg)
    
    def init_user_management_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.user_management_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 添加用户按钮
        ttk.Button(control_frame, text="添加用户", command=self.add_new_user).pack(side="left", padx=5)
        
        # 删除用户按钮
        ttk.Button(control_frame, text="删除用户", command=self.delete_user).pack(side="left", padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_user_list).pack(side="left", padx=5)
        
        # 用户列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("id", "username", "role", "created_at")
        self.user_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.user_tree.heading("id", text="ID")
        self.user_tree.heading("username", text="用户名")
        self.user_tree.heading("role", text="角色")
        self.user_tree.heading("created_at", text="创建时间")
        
        # 设置列宽
        self.user_tree.column("id", width=50)
        self.user_tree.column("username", width=150)
        self.user_tree.column("role", width=100)
        self.user_tree.column("created_at", width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.user_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 刷新用户列表
        self.refresh_user_list()
    
    def refresh_user_list(self):
        # 清空Treeview
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # 使用DatabaseManager获取用户列表
        user_records = self.calculator.db_manager.execute_query(
            "SELECT id, username, role, created_at FROM users ORDER BY id",
            fetch_all=True
        )
        
        # 添加到Treeview
        if user_records:
            for record in user_records:
                id, username, role, created_at = record
                role_text = "管理员" if role == "admin" else "操作员"
                self.user_tree.insert("", tk.END, values=(id, username, role_text, created_at))
    
    def add_new_user(self):
        # 创建添加用户对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加用户", width_percent=0.5, height_percent=0.35)
        
        # 用户名
        username_frame = ttk.Frame(dialog.main_frame)
        username_frame.pack(fill="x", padx=10, pady=8)
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 10
        ttk.Label(username_frame, text="用户名: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        username_var = tk.StringVar()
        ttk.Entry(username_frame, textvariable=username_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        
        # 密码
        password_frame = ttk.Frame(dialog.main_frame)
        password_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(password_frame, text="密码: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        password_var = tk.StringVar()
        ttk.Entry(password_frame, textvariable=password_var, show="*", font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        
        # 角色选择
        role_frame = ttk.Frame(dialog.main_frame)
        role_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(role_frame, text="角色: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        role_var = tk.StringVar(value="operator")
        role_combo = ttk.Combobox(role_frame, textvariable=role_var, values=["operator", "admin"], state="readonly", font=dialog.fonts['normal'])
        role_combo.pack(side="left", padx=5, fill="x", expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=12)
        
        # 确认按钮
        def confirm():
            try:
                username = username_var.get().strip()
                password = password_var.get().strip()
                role = role_var.get()
                
                if not username or not password:
                    messagebox.showerror("错误", "用户名和密码不能为空！")
                    return
                
                success, msg = self.calculator.add_user(username, password, role)
                if success:
                    messagebox.showinfo("成功", msg)
                    dialog.destroy()
                    self.refresh_user_list()
                else:
                    messagebox.showerror("错误", msg)
            except Exception as e:
                messagebox.showerror("错误", f"添加用户失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side="left", padx=10, expand=True)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10, expand=True)
    
    def delete_user(self):
        # 获取选中的用户
        selected_item = self.user_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个用户！")
            return
        
        # 获取用户ID和用户名
        item_values = self.user_tree.item(selected_item[0])["values"]
        user_id = item_values[0]
        username = item_values[1]
        
        # 不能删除自己
        if username == self.calculator.current_user.username:
            messagebox.showinfo("提示", "不能删除当前登录用户！")
            return
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除用户{username}吗？"):
            try:
                # 使用DatabaseManager删除用户
                result = self.calculator.db_manager.execute_query(
                    "DELETE FROM users WHERE id=?",
                    (user_id,)
                )
                
                if result:
                    messagebox.showinfo("成功", f"用户{username}已删除！")
                    self.refresh_user_list()
                else:
                    messagebox.showerror("错误", f"删除用户{username}失败，数据库操作未成功！")
            except Exception as e:
                messagebox.showerror("错误", f"删除用户失败：{str(e)}")
    
    def init_employee_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.employee_frame)
        # 适配手机屏幕：减少边距
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 添加响应式布局支持
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 适配手机屏幕：调整按钮布局，使用网格布局替代左侧布局
        # 创建按钮网格
        button_grid = ttk.Frame(control_frame)
        button_grid.pack(fill="x")
        
        # 第一行按钮
        btn_frame1 = ttk.Frame(button_grid)
        btn_frame1.pack(fill="x", pady=(0, 5))
        
        ttk.Button(btn_frame1, text="添加员工", command=self.add_employee, width=12).pack(side="left", padx=2)
        ttk.Button(btn_frame1, text="修改员工", command=self.edit_employee, width=12).pack(side="left", padx=2)
        ttk.Button(btn_frame1, text="员工离职", command=self.process_employee_leave, width=12).pack(side="left", padx=2)
        
        # 第二行按钮
        btn_frame2 = ttk.Frame(button_grid)
        btn_frame2.pack(fill="x")
        
        ttk.Button(btn_frame2, text="删除员工", command=self.delete_employee, width=12).pack(side="left", padx=2)
        ttk.Button(btn_frame2, text="刷新列表", command=self.refresh_employee_list, width=12).pack(side="left", padx=2)
        
        # 状态选择框 - 适配手机屏幕：调整位置
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Label(status_frame, text="状态: ", width=8).pack(side="left")
        self.employee_status_var = tk.StringVar(value="在职")
        ttk.Combobox(status_frame, textvariable=self.employee_status_var, values=["在职", "离职", "全部"], width=10).pack(side="left", padx=5)
        ttk.Button(status_frame, text="查询", command=self.filter_employees).pack(side="left", padx=5)
        
        # 员工列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建带水平滚动条的容器 - 适配手机屏幕：添加水平滚动支持
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True)
        
        # 创建Treeview
        columns = ("emp_id", "name", "department", "position", "base_salary", "hire_date", "status", "leave_date")
        self.employee_tree = ttk.Treeview(tree_container, columns=columns, show="headings")
        
        # 设置列标题
        self.employee_tree.heading("emp_id", text="员工ID")
        self.employee_tree.heading("name", text="姓名")
        self.employee_tree.heading("department", text="部门")
        self.employee_tree.heading("position", text="职位")
        self.employee_tree.heading("base_salary", text="基本工资")
        self.employee_tree.heading("hire_date", text="入职日期")
        self.employee_tree.heading("status", text="状态")
        self.employee_tree.heading("leave_date", text="离职日期")
        
        # 设置列宽和对齐方式 - 适配手机屏幕：调整列宽
        self.employee_tree.column("emp_id", width=60, anchor=CENTER)
        self.employee_tree.column("name", width=80, anchor=CENTER)
        self.employee_tree.column("department", width=90, anchor=CENTER)
        self.employee_tree.column("position", width=90, anchor=CENTER)
        self.employee_tree.column("base_salary", width=80, anchor=E)
        self.employee_tree.column("hire_date", width=100, anchor=CENTER)
        self.employee_tree.column("status", width=60, anchor=CENTER)
        self.employee_tree.column("leave_date", width=100)
        
        # 添加垂直滚动条
        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.employee_tree.yview)
        self.employee_tree.configure(yscroll=v_scrollbar.set)
        
        # 添加水平滚动条 - 适配手机屏幕：增加水平滚动功能
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.employee_tree.xview)
        self.employee_tree.configure(xscroll=h_scrollbar.set)
        
        # 布局Treeview和滚动条
        self.employee_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # 绑定双击事件
        self.employee_tree.bind("<Double-1>", lambda event: self.edit_employee())
        
        # 刷新员工列表
        self.refresh_employee_list()
    
    def refresh_employee_list(self):
        logger.info("======= 开始刷新员工列表 =======")
        # 清空Treeview
        logger.info(f"当前Treeview中有 {len(self.employee_tree.get_children())} 条记录，开始清空...")
        for item in self.employee_tree.get_children():
            self.employee_tree.delete(item)
        logger.info("Treeview清空完成")
        
        # 确保employee_status_var的值是有效的
        valid_statuses = ["在职", "离职", "全部"]
        current_status = self.employee_status_var.get()
        if current_status not in valid_statuses:
            logger.warning(f"employee_status_var的值 '{current_status}' 无效，重置为 '在职'")
            self.employee_status_var.set("在职")
            status = "在职"
        else:
            status = current_status
        
        logger.info(f"刷新员工列表，状态查询: {status}")
        
        # 中文状态值映射到英文
        status_map = {
            "全部": "all",
            "在职": "active",
            "离职": "inactive"
        }
        
        # 转换为英文状态值
        status = status_map[status]
        logger.info(f"英文状态值: {status}")
        
        # 获取员工列表（带状态查询）
        if status == "all":
            logger.info("获取所有员工...")
            employees = self.calculator.get_all_employees()
            logger.info(f"获取到所有 {len(employees)} 名员工数据")
        else:
            logger.info(f"获取状态为 '{status}' 的员工...")
            employees = self.calculator.get_all_employees(status)
            logger.info(f"获取到状态为 '{status}' 的 {len(employees)} 名员工数据")
        
        # 添加到Treeview
        added_count = 0
        active_count = 0
        inactive_count = 0
        logger.info("开始添加员工到Treeview...")
        # 强制刷新UI，确保数据正确显示
        self.employee_tree.update_idletasks()
        
        for emp in employees:
            # 详细记录每个员工的状态信息
            logger.info(f"处理员工: {emp.emp_id} - {emp.name}, 状态: {emp.status}")
            status_text = "在职" if emp.status == "active" else "离职"
            
            # 统计状态
            if emp.status == "active":
                active_count += 1
            else:
                inactive_count += 1
            
            # 数据校验：如果状态为离职但没有离职日期，记录警告
            if emp.status == 'inactive' and not emp.leave_date:
                logger.warning(f"员工 {emp.emp_id} - {emp.name} 状态为离职，但没有离职日期！")
            
            # 添加到Treeview
            self.employee_tree.insert("", tk.END,
                values=(emp.emp_id, emp.name, emp.department, emp.position, emp.base_salary,
                        emp.hire_date, status_text, emp.leave_date or ""))
            added_count += 1
            # 添加一条记录后就更新UI，确保显示及时更新
            self.employee_tree.update_idletasks()
        
        logger.info(f"Treeview添加完成，共添加 {added_count} 条记录")
        logger.info(f"其中在职员工: {active_count} 人，离职员工: {inactive_count} 人")
        # 最后再强制刷新一次UI
        self.employee_tree.update_idletasks()
        self.employee_frame.update_idletasks()
        self.root.update_idletasks()
        
        if not employees:
            logger.warning("没有找到员工数据")
            messagebox.showinfo("提示", "当前没有找到员工数据\n请检查数据库或查询条件")
        logger.info("======= 员工列表刷新完成 =======")
    
    def add_employee(self):
        logger.info("======= 开始添加员工 =======")
        # 创建添加员工对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加员工", width_percent=0.6, height_percent=0.5)
        
        # 使用DatabaseManager获取部门和职位列表
        logger.info("获取部门和职位列表...")

        # 获取部门列表
        departments = self.calculator.db_manager.execute_query(
            "SELECT DISTINCT department FROM employees WHERE status='active' ORDER BY department",
            fetch_all=True
        )
        dept_values = [dept[0] for dept in departments if dept[0]]
        logger.info(f"获取到 {len(dept_values)} 个部门")

        # 获取职位列表
        positions = self.calculator.db_manager.execute_query(
            "SELECT DISTINCT position FROM employees WHERE status='active' ORDER BY position",
            fetch_all=True
        )
        position_values = [pos[0] for pos in positions if pos[0]]
        logger.info(f"获取到 {len(position_values)} 个职位")
        
        # 创建表单
        fields = [
            ("员工ID: ", "emp_id"),
            ("姓名: ", "name"),
            ("部门: ", "department"),
            ("职位: ", "position"),
            ("基本工资: ", "base_salary"),
            ("入职日期 (YYYY-MM-DD): ", "hire_date")
        ]
        
        # 存储输入框的引用
        inputs = {}
        
        # 创建输入框
        for i, (label_text, field_name) in enumerate(fields):
            frame = ttk.Frame(dialog.main_frame)
            frame.pack(fill="x", padx=10, pady=5)
            
            # 为标签设置合适的宽度
            label_width = 25 if dialog.winfo_width() < 500 else 20
            ttk.Label(frame, text=label_text, width=label_width, font=dialog.fonts['normal']).pack(side="left")
            
            if field_name == "base_salary":
                var = tk.DoubleVar()
                entry = ttk.Entry(frame, textvariable=var, font=dialog.fonts['normal'])
            elif field_name == "department":
                var = tk.StringVar()
                # 创建部门下拉菜单
                entry = ttk.Combobox(frame, textvariable=var, values=dept_values, state="readonly", font=dialog.fonts['normal'])
            elif field_name == "position":
                var = tk.StringVar()
                # 创建职位下拉菜单
                entry = ttk.Combobox(frame, textvariable=var, values=position_values, state="readonly", font=dialog.fonts['normal'])
            else:
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var, font=dialog.fonts['normal'])
            
            # 为员工ID设置默认值
            if field_name == "emp_id":
                # 获取当前时间戳作为默认ID
                default_id = f"EMP{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                var.set(default_id)
            # 为入职日期设置默认值
            elif field_name == "hire_date":
                var.set(datetime.datetime.now().strftime('%Y-%m-%d'))
            
            entry.pack(side="left", fill="x", expand=True, padx=5)
            inputs[field_name] = var
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                # 获取输入值
                emp_id = inputs["emp_id"].get().strip()
                name = inputs["name"].get().strip()
                department = inputs["department"].get().strip()
                position = inputs["position"].get().strip()
                base_salary = inputs["base_salary"].get()
                hire_date = inputs["hire_date"].get().strip()
                
                logger.info(f"准备添加员工: ID={emp_id}, name={name}, department={department}, position={position}")
                logger.info(f"基本工资={base_salary}, 入职日期={hire_date}")
                
                # 验证输入
                if not all([emp_id, name, department, position, hire_date]):
                    messagebox.showerror("错误", "所有字段都必须填写！")
                    return
                
                # 验证基本工资
                try:
                    base_salary = float(base_salary)
                    if base_salary < 0:
                        raise ValueError
                    logger.info(f"基本工资验证通过: {base_salary}")
                except ValueError:
                    logger.warning("基本工资必须是正数！")
                    messagebox.showerror("错误", "基本工资必须是正数！")
                    return
                
                # 验证日期格式
                try:
                    datetime.datetime.strptime(hire_date, '%Y-%m-%d')
                    logger.info(f"日期格式验证通过: {hire_date}")
                except ValueError:
                    logger.warning("日期格式必须是 YYYY-MM-DD！")
                    messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                    return

                                    
                # 创建员工对象
                logger.info("创建员工对象，状态设置为 'active'")
                employee = Employee(
                    emp_id=emp_id,
                    name=name,
                    department=department,
                    position=position,
                    base_salary=base_salary,
                    hire_date=hire_date,
                    contact='',
                    status='active',
                    leave_date=None
                )
                
                # 添加员工
                logger.info(f"调用calculator.add_employee添加员工...")
                success, message = self.calculator.add_employee(employee)
                if success:
                    logger.info(f"员工添加成功: {message}")
                    messagebox.showinfo("成功", message)
                    dialog.destroy()
                    logger.info("开始刷新员工列表...")
                    self.refresh_employee_list()
                    # 同时刷新考勤列表
                    if hasattr(self, 'attendance_frame'):
                        logger.info("刷新考勤列表...")
                        self.refresh_attendance_list()
                else:
                    logger.warning(f"员工添加失败: {message}")
                    messagebox.showerror("错误", message)
            except Exception as e:
                logger.error(f"添加员工异常: {str(e)}")
                messagebox.showerror("错误", f"添加员工失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10)
        
        # 设置焦点到第一个输入框
        if inputs:
            for entry_var in inputs.values():
                for widget in dialog.main_frame.winfo_children():
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry) and child['textvariable'] == entry_var:
                            child.focus()
                            break
                    else:
                        continue
                    break
                else:
                    continue
                break
    
    def edit_employee(self):
        # 获取选中的员工
        selected_item = self.employee_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个员工！")
            return
        
        # 获取员工ID
        emp_id = self.employee_tree.item(selected_item[0])["values"][0]
        
        # 获取员工信息
        employee = self.calculator.get_employee(emp_id)
        if not employee:
            messagebox.showerror("错误", "员工信息不存在！")
            return
        
        # 创建编辑员工对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "编辑员工", width_percent=0.6, height_percent=0.5)
        
        # 创建表单
        fields = [
            ("员工ID: ", "emp_id", employee.emp_id, True),  # True表示不可编辑
            ("姓名: ", "name", employee.name, False),
            ("部门: ", "department", employee.department, False),
            ("职位: ", "position", employee.position, False),
            ("基本工资: ", "base_salary", employee.base_salary, False),
            ("入职日期 (YYYY-MM-DD): ", "hire_date", employee.hire_date, False)
        ]
        
        # 存储输入框的引用
        inputs = {}
        
        # 创建输入框
        for i, (label_text, field_name, value, readonly) in enumerate(fields):
            frame = ttk.Frame(dialog.main_frame)
            frame.pack(fill="x", padx=10, pady=5)
            
            # 为标签设置合适的宽度
            label_width = 25 if dialog.winfo_width() < 500 else 20
            ttk.Label(frame, text=label_text, width=label_width, font=dialog.fonts['normal']).pack(side="left")
            
            if field_name == "base_salary":
                var = tk.DoubleVar(value=value)
                entry = ttk.Entry(frame, textvariable=var, font=dialog.fonts['normal'])
            else:
                var = tk.StringVar(value=value)
                entry = ttk.Entry(frame, textvariable=var, font=dialog.fonts['normal'])
            
            # 设置只读
            if readonly:
                entry.config(state=tk.DISABLED)
            
            entry.pack(side="left", fill="x", expand=True, padx=5)
            inputs[field_name] = var
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                # 获取输入值
                name = inputs["name"].get().strip()
                department = inputs["department"].get().strip()
                position = inputs["position"].get().strip()
                base_salary = inputs["base_salary"].get()
                hire_date = inputs["hire_date"].get().strip()
                
                # 验证输入
                if not all([name, department, position, hire_date]):
                    messagebox.showerror("错误", "所有字段都必须填写！")
                    return
                
                # 验证基本工资
                try:
                    base_salary = float(base_salary)
                    if base_salary < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("错误", "基本工资必须是正数！")
                    return
                
                # 验证日期格式
                try:
                    datetime.datetime.strptime(hire_date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                    return
                
                # 更新员工信息
                employee.name = name
                employee.department = department
                employee.position = position
                employee.base_salary = base_salary
                employee.hire_date = hire_date
                
                # 保存更新
                if self.calculator.update_employee(employee):
                    messagebox.showinfo("成功", "员工信息更新成功！")
                    dialog.destroy()
                    self.refresh_employee_list()
                    # 刷新其他相关表格
                    if hasattr(self, 'attendance_frame'):
                        self.refresh_attendance_list()
                    if hasattr(self, 'salary_frame'):
                        self.generate_salary_sheet()
                    if hasattr(self, 'revenue_frame'):
                        self.refresh_revenue_list()
                else:
                    messagebox.showerror("错误", "员工信息更新失败！")
            except Exception as e:
                messagebox.showerror("错误", f"更新员工失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side="left", padx=10, expand=True)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10, expand=True)
    
    def process_employee_leave(self):
        # 获取选中的员工
        selected_item = self.employee_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个员工！")
            return
        
        # 获取员工ID和姓名
        item_values = self.employee_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        
        # 获取员工信息
        employee = self.calculator.get_employee(emp_id)
        if not employee:
            messagebox.showerror("错误", "员工信息不存在！")
            return
        
        # 检查员工状态
        if employee.status == 'inactive':
            messagebox.showinfo("提示", f"员工{emp_name}已经是离职状态！")
            return
        
        # 创建离职处理对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "员工离职处理", width_percent=0.5, height_percent=0.4)
        
        # 显示员工信息
        ttk.Label(dialog.main_frame, text=f"员工：{emp_name}", font=dialog.fonts['normal']).pack(padx=10, pady=10)
        
        # 离职日期输入
        date_frame = ttk.Frame(dialog.main_frame)
        date_frame.pack(fill="x", padx=10, pady=10)
        
        # 为标签设置合适的宽度
        label_width = 25 if dialog.winfo_width() < 500 else 20
        ttk.Label(date_frame, text="离职日期 (YYYY-MM-DD): ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        leave_date_var = tk.StringVar(value=datetime.datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=leave_date_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 确认按钮
        def confirm():
            try:
                # 获取离职日期
                leave_date = leave_date_var.get().strip()
                
                # 验证日期格式
                try:
                    datetime.datetime.strptime(leave_date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                    return
                
                # 更新员工状态
                employee.status = 'inactive'
                employee.leave_date = leave_date
                
                # 保存更新
                if self.calculator.update_employee(employee):
                    messagebox.showinfo("成功", f"员工{emp_name}已处理为离职状态！")
                    dialog.destroy()
                    self.refresh_employee_list()
                else:
                    messagebox.showerror("错误", "员工离职处理失败！")
            except Exception as e:
                messagebox.showerror("错误", f"处理离职失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side="left", padx=10, expand=True)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10, expand=True)
    

    
    def delete_employee(self):
        # 获取选中的员工
        selected_item = self.employee_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个员工！")
            return
        
        # 获取员工ID和姓名
        item_values = self.employee_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除员工{emp_name}吗？"):
            try:
                # 使用DatabaseManager删除员工
                result = self.calculator.db_manager.execute_query(
                    "DELETE FROM employees WHERE emp_id=?",
                    (emp_id,)
                )
                
                if result:
                    messagebox.showinfo("成功", f"员工{emp_name}已删除！")
                    self.refresh_employee_list()
                else:
                    messagebox.showerror("错误", f"删除员工{emp_name}失败，数据库操作未成功！")
            except Exception as e:
                messagebox.showerror("错误", f"删除员工失败：{str(e)}")

    def filter_employees(self):
        self.refresh_employee_list()
    
    def init_attendance_frame(self):
        # 首先初始化所有统计变量
        self.total_count_var = tk.StringVar(value="总人数: 0")
        self.present_count_var = tk.StringVar(value="出勤: 0")
        self.absent_count_var = tk.StringVar(value="缺勤: 0")
        self.leave_count_var = tk.StringVar(value="请假: 0")
        self.unrecorded_count_var = tk.StringVar(value="未记录: 0")
        
        # 创建主框架
        main_frame = ttk.Frame(self.attendance_frame)
        # 适配手机屏幕：减少边距
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 添加响应式布局支持
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 顶部控制面板 - 适配手机屏幕：调整布局，使用网格布局替代左右布局
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 日期选择
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(date_frame, text="日期: ", width=8).pack(side="left")
        self.attendance_date_var = tk.StringVar(value=get_network_time().date().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.attendance_date_var, width=15).pack(side="left", padx=5)
        
        # 第一行按钮
        btn_frame1 = ttk.Frame(control_frame)
        btn_frame1.pack(fill="x", pady=(0, 5))
        
        ttk.Button(btn_frame1, text="批量设置出勤", command=self.batch_set_attendance, width=15).pack(side="left", padx=2)
        ttk.Button(btn_frame1, text="删除考勤记录", command=self.delete_attendance_record, width=15).pack(side="left", padx=2)
        ttk.Button(btn_frame1, text="刷新考勤", command=self.refresh_attendance_list, width=10).pack(side="left", padx=2)
        
        # 搜索框
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(search_frame, text="搜索: ", width=8).pack(side="left")
        self.attendance_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.attendance_search_var, width=20).pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(search_frame, text="搜索", command=self.refresh_attendance_list).pack(side="left", padx=5)

        # 查询条件
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(fill="x", pady=(0, 5))

        # 部门查询
        ttk.Label(filter_frame, text="部门: ", width=8).pack(side="left")
        self.dept_filter_var = tk.StringVar(value="all")
        # 动态获取部门列表
        self.load_departments()
        dept_combo = ttk.Combobox(filter_frame, textvariable=self.dept_filter_var, width=12)
        dept_combo.pack(side="left", padx=5)

        # 状态查询
        ttk.Label(filter_frame, text="状态: ", width=8).pack(side="left")
        self.status_filter_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, values=["all", "出勤", "缺勤", "请假"], width=10)
        status_combo.pack(side="left", padx=5)

        # 查询按钮
        ttk.Button(filter_frame, text="查询", command=self.refresh_attendance_list).pack(side="left", padx=5)
        
        # 统计信息面板 - 适配手机屏幕：调整布局，减少边距
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", padx=5, pady=5)
        
        # 布局统计标签 - 适配手机屏幕：减少边距
        ttk.Label(stats_frame, textvariable=self.total_count_var, font=('SimHei', 10, 'bold')).pack(side="left", padx=10)
        ttk.Label(stats_frame, textvariable=self.present_count_var, font=('SimHei', 10, 'bold'), foreground='green').pack(side="left", padx=10)
        ttk.Label(stats_frame, textvariable=self.absent_count_var, font=('SimHei', 10, 'bold'), foreground='red').pack(side="left", padx=10)
        ttk.Label(stats_frame, textvariable=self.leave_count_var, font=('SimHei', 10, 'bold'), foreground='blue').pack(side="left", padx=10)
        ttk.Label(stats_frame, textvariable=self.unrecorded_count_var, font=('SimHei', 10, 'bold'), foreground='orange').pack(side="left", padx=10)
        
        # 考勤列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建带水平滚动条的容器 - 适配手机屏幕：添加水平滚动支持
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True)
        
        # 创建Treeview
        columns = ("emp_id", "name", "department", "position", "status", "note")
        self.attendance_tree = ttk.Treeview(tree_container, columns=columns, show="headings")
        
        # 设置列标题
        self.attendance_tree.heading("emp_id", text="员工ID")
        self.attendance_tree.heading("name", text="姓名")
        self.attendance_tree.heading("department", text="部门")
        self.attendance_tree.heading("position", text="职位")
        self.attendance_tree.heading("status", text="状态")
        self.attendance_tree.heading("note", text="备注")
        
        # 设置列宽 - 适配手机屏幕：调整列宽
        self.attendance_tree.column("emp_id", width=60)
        self.attendance_tree.column("name", width=80)
        self.attendance_tree.column("department", width=90)
        self.attendance_tree.column("position", width=90)
        self.attendance_tree.column("status", width=60)
        self.attendance_tree.column("note", width=150)
        
        # 添加垂直滚动条
        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscroll=v_scrollbar.set)
        
        # 添加水平滚动条 - 适配手机屏幕：增加水平滚动功能
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.attendance_tree.xview)
        self.attendance_tree.configure(xscroll=h_scrollbar.set)
        
        # 布局Treeview和滚动条
        self.attendance_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # 绑定双击事件，编辑考勤
        self.attendance_tree.bind("<Double-1>", lambda event: self.edit_attendance())
        
        # 刷新考勤列表
        self.refresh_attendance_list()
    
    def load_departments(self):
        # 使用DatabaseManager获取部门列表
        departments = self.calculator.db_manager.execute_query(
            "SELECT DISTINCT department FROM employees WHERE status='active' ORDER BY department",
            fetch_all=True
        )
        
        # 添加部门到下拉框
        dept_values = ["all"] + [dept[0] for dept in departments if dept[0]]
        for child in self.attendance_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.Frame):
                        for great_grandchild in grandchild.winfo_children():
                            if isinstance(great_grandchild, ttk.Combobox) and self.dept_filter_var == great_grandchild["textvariable"]:
                                great_grandchild['values'] = dept_values
                                break
                
    def refresh_attendance_list(self):
        try:
            # 清空Treeview
            for item in self.attendance_tree.get_children():
                self.attendance_tree.delete(item)

            # 确保attendance_date_var已初始化
            if not hasattr(self, 'attendance_date_var'):
                self.attendance_date_var = tk.StringVar(value=get_network_time().date().strftime('%Y-%m-%d'))

            # 获取日期
            date = self.attendance_date_var.get()

            try:
                # 验证日期格式
                datetime.datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                return

            # 获取查询条件
            dept_filter = self.dept_filter_var.get()
            # 确保status_filter_var已初始化
            if not hasattr(self, 'status_filter_var'):
                self.status_filter_var = tk.StringVar(value='all')
            status_filter = self.status_filter_var.get()
            # 确保attendance_search_var已初始化
            if not hasattr(self, 'attendance_search_var'):
                self.attendance_search_var = tk.StringVar()
            search_text = self.attendance_search_var.get().lower().strip()

            # 获取所有在职员工
            employees = self.calculator.get_all_employees('active')
            
            # 确保员工列表中没有重复记录
            unique_employees = {emp.emp_id: emp for emp in employees}.values()
            employees = list(unique_employees)
            
            # 添加日志记录
            logger.info(f"获取到 {len(employees)} 名在职员工")
            
            # 添加错误处理和日志记录
            if not employees:
                messagebox.showinfo("提示", "当前没有在职员工记录。\n请检查数据库中是否存在状态为'active'的员工。")
                # 初始化统计变量（如果不存在）
                if not hasattr(self, 'total_count_var'):
                    self.total_count_var = tk.StringVar()
                if not hasattr(self, 'present_count_var'):
                    self.present_count_var = tk.StringVar()
                if not hasattr(self, 'absent_count_var'):
                    self.absent_count_var = tk.StringVar()
                if not hasattr(self, 'leave_count_var'):
                    self.leave_count_var = tk.StringVar()
                if not hasattr(self, 'unrecorded_count_var'):
                    self.unrecorded_count_var = tk.StringVar()
                # 重置统计信息
                self.total_count_var.set(f"总人数: 0")
                self.present_count_var.set(f"出勤: 0")
                self.absent_count_var.set(f"缺勤: 0")
                self.leave_count_var.set(f"请假: 0")
                self.unrecorded_count_var.set(f"未记录: 0")
                return

            # 查询部门
            if dept_filter != "all":
                filtered_employees = [emp for emp in employees if emp.department == dept_filter]
                if not filtered_employees:
                    messagebox.showinfo("提示", f"所选部门 '{dept_filter}' 中没有在职员工。")
                    # 初始化统计变量（如果不存在）
                    if not hasattr(self, 'total_count_var'):
                        self.total_count_var = tk.StringVar()
                    # 重置统计信息
                    self.total_count_var.set(f"总人数: 0")
                    return
                else:
                    employees = filtered_employees

            # 使用DatabaseManager获取考勤记录

            # 初始化统计计数器
            total_count = 0
            present_count = 0
            absent_count = 0
            leave_count = 0
            unrecorded_count = 0

            # 批量获取所有员工的考勤记录以提高性能
            attendance_records = {}
            try:
                if employees:
                    emp_ids = [emp.emp_id for emp in employees]
                    placeholders = ', '.join(['?' for _ in emp_ids])
                    query = f"SELECT emp_id, status, note FROM attendance WHERE emp_id IN ({placeholders}) AND date=?"
                    params = emp_ids + [date]
                    logger.info(f"执行考勤查询: {query}")
                    logger.info(f"查询参数: {params}")
                    results = self.calculator.db_manager.execute_query(query, params, fetch_all=True)
                if results:
                    logger.info(f"获取到 {len(results)} 条考勤记录")
                    for row in results:
                        try:
                            emp_id, status, note = row
                            attendance_records[emp_id] = (status, note)
                        except ValueError as ve:
                            logger.error(f"解析考勤记录失败: {row}, 错误: {str(ve)}")
            except Exception as e:
                logger.error(f"批量获取考勤记录失败: {str(e)}")
                messagebox.showerror("错误", f"获取考勤数据失败: {str(e)}")
                return
            
            # 添加到Treeview
            for emp in employees:
                # 获取考勤记录
                record = attendance_records.get(emp.emp_id)

                total_count += 1

                if record:
                    try:
                        status, note = record
                    except ValueError:
                        # 如果解包失败，默认值
                        status = record[0]
                        note = record[1] if len(record) > 1 else ""

                    # 转换状态为中文
                    status_text = {
                        "present": "出勤",
                        "absent": "缺勤",
                        "leave": "请假"
                    }.get(status, "")

                    # 更新统计数据
                    if status == "present":
                        present_count += 1
                    elif status == "absent":
                        absent_count += 1
                    elif status == "leave":
                        leave_count += 1
                else:
                    # 如果没有记录，显示未记录
                    status_text = "未记录"
                    note = ""
                    unrecorded_count += 1

                # 状态查询
                if status_filter != "all" and status_text != status_filter:
                    continue

                # 搜索查询
                if search_text and not (
                    search_text in emp.emp_id.lower() or 
                    search_text in emp.name.lower() or 
                    search_text in emp.department.lower() or 
                    search_text in emp.position.lower() or
                    search_text in status_text.lower() or
                    search_text in (note.lower() if note else "")
                ):
                    continue

                self.attendance_tree.insert("", "end",
                    values=(emp.emp_id, emp.name, emp.department, emp.position, status_text, note))

            # 初始化统计变量（如果不存在）
            if not hasattr(self, 'total_count_var'):
                self.total_count_var = tk.StringVar()
            if not hasattr(self, 'present_count_var'):
                self.present_count_var = tk.StringVar()
            if not hasattr(self, 'absent_count_var'):
                self.absent_count_var = tk.StringVar()
            if not hasattr(self, 'leave_count_var'):
                self.leave_count_var = tk.StringVar()
            if not hasattr(self, 'unrecorded_count_var'):
                self.unrecorded_count_var = tk.StringVar()
            
            # 更新统计信息显示
            self.total_count_var.set(f"总人数: {total_count}")
            self.present_count_var.set(f"出勤: {present_count}")
            self.absent_count_var.set(f"缺勤: {absent_count}")
            self.leave_count_var.set(f"请假: {leave_count}")
            self.unrecorded_count_var.set(f"未记录: {unrecorded_count}")

        except Exception as e:
            messagebox.showerror("错误", f"刷新考勤列表失败：{str(e)}")
    
    def delete_attendance_record(self):
        # 获取选中的考勤记录
        selected_item = self.attendance_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个考勤记录！")
            return

        # 获取员工信息
        item_values = self.attendance_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        status = item_values[4]
        date = self.attendance_date_var.get()

        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除 {emp_name} ({emp_id}) 在 {date} 的考勤记录吗？"):
            try:
                # 调用计算器类的方法删除考勤记录
                success = self.calculator.delete_attendance(emp_id, date)
                if success:
                    messagebox.showinfo("成功", f"已删除 {emp_name} 的考勤记录！")
                    self.refresh_attendance_list()
                else:
                    messagebox.showerror("错误", "删除考勤记录失败，请重试！")
            except Exception as e:
                messagebox.showerror("错误", f"删除考勤记录失败：{str(e)}")

    def edit_attendance(self):
        # 获取选中的考勤记录
        selected_item = self.attendance_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个员工！")
            return
        
        # 获取员工信息
        item_values = self.attendance_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        current_status = item_values[4]
        current_note = item_values[5]
        
        # 获取日期
        date = self.attendance_date_var.get()
        
        # 创建编辑考勤对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "编辑考勤", width_percent=0.5, height_percent=0.35)
        
        # 显示员工信息和日期
        info_frame = ttk.Frame(dialog.main_frame)
        info_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(info_frame, text=f"员工：{emp_name}", font=dialog.fonts['heading']).pack(pady=2, fill="x")
        ttk.Label(info_frame, text=f"日期：{date}", font=dialog.fonts['heading']).pack(pady=2, fill="x")
        
        # 考勤状态选择
        status_frame = ttk.Frame(dialog.main_frame)
        status_frame.pack(fill="x", padx=10, pady=8)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 10
        ttk.Label(status_frame, text="考勤状态: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        status_var = tk.StringVar()
        
        # 转换中文状态回英文
        status_mapping = {
            "出勤": "present",
            "缺勤": "absent",
            "请假": "leave",
            "": ""
        }
        
        reverse_mapping = {v: k for k, v in status_mapping.items()}
        status_var.set(status_mapping.get(current_status, ""))
        
        status_combo = ttk.Combobox(status_frame, textvariable=status_var, 
                                   values=["", "present", "absent", "leave"], 
                                   width=12, font=dialog.fonts['normal'])
        status_combo.pack(side="left", padx=5, fill="x", expand=True)
        
        # 备注输入
        note_frame = ttk.Frame(dialog.main_frame)
        note_frame.pack(fill="x", padx=10, pady=8)
        
        ttk.Label(note_frame, text="备注: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        note_var = tk.StringVar(value=current_note)
        ttk.Entry(note_frame, textvariable=note_var, font=dialog.fonts['normal']).pack(side="left", fill="x", expand=True, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=12)
        
        # 确认按钮
        def confirm():
            try:
                # 获取考勤信息
                status = status_var.get()
                note = note_var.get().strip()
                
                # 获取当前登录用户
                current_username = self.calculator.current_user.username if self.calculator.current_user else "未知用户"
                
                # 在备注中添加当前登录用户信息
                if note:
                    note += f" [操作人: {current_username}]"
                else:
                    note = f"操作人: {current_username}"
                
                # 创建考勤对象
                attendance = Attendance(
                    emp_id=emp_id,
                    date=date,
                    status=status,
                    note=note
                )
                
                # 添加或更新考勤记录
                self.calculator.add_attendance(attendance)
                
                messagebox.showinfo("成功", "考勤记录已更新！")
                dialog.destroy()
                self.refresh_attendance_list()
            except Exception as e:
                messagebox.showerror("错误", f"更新考勤失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side="left", padx=10, expand=True)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10, expand=True)
    
    def batch_set_attendance(self):
        # 获取日期
        date = self.attendance_date_var.get()
        
        # 创建批量设置对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "批量设置出勤", width_percent=0.5, height_percent=0.3)
        
        # 显示日期
        info_frame = ttk.Frame(dialog.main_frame)
        info_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(info_frame, text=f"设置日期：{date} 的考勤状态", font=dialog.fonts['heading']).pack(fill="x")
        
        # 考勤状态选择
        status_frame = ttk.Frame(dialog.main_frame)
        status_frame.pack(fill="x", padx=10, pady=10)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 10
        ttk.Label(status_frame, text="考勤状态: ", width=label_width, font=dialog.fonts['normal']).pack(side="left", padx=10)
        status_var = tk.StringVar(value="present")
        
        status_combo = ttk.Combobox(status_frame, textvariable=status_var, 
                                   values=["present", "absent", "leave"], 
                                   width=12, font=dialog.fonts['normal'])
        status_combo.pack(side="left", padx=5, fill="x", expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                # 获取考勤状态
                status = status_var.get()
                
                # 获取当前登录用户
                current_username = self.calculator.current_user.username if self.calculator.current_user else "未知用户"
                
                # 获取所有在职员工
                employees = self.calculator.get_all_employees('active')
                
                # 批量设置考勤
                for emp in employees:
                    attendance = Attendance(
                        emp_id=emp.emp_id,
                        date=date,
                        status=status,
                        note=f"批量设置 [操作人: {current_username}]"
                    )
                    self.calculator.add_attendance(attendance)
                
                messagebox.showinfo("成功", f"已为{len(employees)}名员工批量设置考勤！")
                dialog.destroy()
                self.refresh_attendance_list()
            except Exception as e:
                messagebox.showerror("错误", f"批量设置失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side="left", padx=10, expand=True)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10, expand=True)
    
    def init_salary_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.salary_frame)
        # 适配手机屏幕：减少边距
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 添加响应式布局支持
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 顶部控制面板 - 适配手机屏幕：调整布局
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=X, padx=5, pady=5)
        
        # 月份选择
        month_frame = ttk.Frame(control_frame)
        month_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(month_frame, text="月份: ", width=8).pack(side="left")
        self.salary_month_var = tk.StringVar(value=datetime.datetime.now().strftime('%Y-%m'))
        ttk.Entry(month_frame, textvariable=self.salary_month_var, width=12).pack(side="left", padx=5)
        
        # 第一行按钮 - 适配手机屏幕：调整按钮布局为网格
        btn_frame1 = ttk.Frame(control_frame)
        btn_frame1.pack(fill="x", pady=(0, 5))
        
        ttk.Button(btn_frame1, text="生成工资表", command=self.generate_salary_sheet, width=12).pack(side="left", padx=2)
        ttk.Button(btn_frame1, text="批量标记发放", command=self.batch_mark_paid, width=12).pack(side="left", padx=2)
        
        # 第二行按钮 - 适配手机屏幕：增加管理员按钮布局
        btn_frame2 = ttk.Frame(control_frame)
        btn_frame2.pack(fill="x", pady=(0, 5))
        
        # 管理员按钮
        if self.user_role == 'admin':
            ttk.Button(btn_frame2, text="取消标记发放", command=self.mark_unpaid, width=12).pack(side="left", padx=2)
            ttk.Button(btn_frame2, text="批量取消标记发放", command=self.batch_mark_unpaid, width=12).pack(side="left", padx=2)
        
        # 第三行按钮 - 适配手机屏幕：添加功能按钮布局
        btn_frame3 = ttk.Frame(control_frame)
        btn_frame3.pack(fill="x", pady=(0, 5))
        
        ttk.Button(btn_frame3, text="导出Excel", command=self.export_to_excel, width=12).pack(side="left", padx=2)
        ttk.Button(btn_frame3, text="打印个人工资表", command=self.print_individual_salary_sheet, width=12).pack(side="left", padx=2)
        
        # 管理员可见的删除按钮
        if self.user_role == 'admin':
            ttk.Button(btn_frame3, text="删除员工ID", command=self.delete_employee_id, width=12).pack(side="left", padx=2)
        
        # 工资列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建带水平滚动条的容器 - 适配手机屏幕：添加水平滚动支持
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True)
        
        # 创建Treeview
        columns = ("emp_id", "name", "base_salary", "bonus", "deduction", "tax", "final_salary", "status", "payment_date")
        self.salary_tree = ttk.Treeview(tree_container, columns=columns, show="headings")
        
        # 设置列标题
        self.salary_tree.heading("emp_id", text="员工ID")
        self.salary_tree.heading("name", text="姓名")
        self.salary_tree.heading("base_salary", text="基本工资")
        self.salary_tree.heading("bonus", text="奖金")
        self.salary_tree.heading("deduction", text="扣款")
        self.salary_tree.heading("tax", text="个人所得税")
        self.salary_tree.heading("final_salary", text="实发工资")
        self.salary_tree.heading("status", text="状态")
        self.salary_tree.heading("payment_date", text="发放日期")
        
        # 设置列宽和对齐方式 - 适配手机屏幕：调整列宽
        self.salary_tree.column("emp_id", width=60)
        self.salary_tree.column("name", width=80)
        self.salary_tree.column("base_salary", width=80, anchor="e")
        self.salary_tree.column("bonus", width=60, anchor="e")
        self.salary_tree.column("deduction", width=60, anchor="e")
        self.salary_tree.column("tax", width=80, anchor="e")
        self.salary_tree.column("final_salary", width=80, anchor="e")
        self.salary_tree.column("status", width=60, anchor="center")
        self.salary_tree.column("payment_date", width=90)
        
        # 添加垂直滚动条
        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.salary_tree.yview)
        self.salary_tree.configure(yscroll=v_scrollbar.set)
        
        # 添加水平滚动条 - 适配手机屏幕：增加水平滚动功能
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.salary_tree.xview)
        self.salary_tree.configure(xscroll=h_scrollbar.set)
        
        # 布局Treeview和滚动条
        self.salary_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # 绑定双击事件，标记发放
        self.salary_tree.bind("<Double-1>", lambda event: self.mark_paid())
        
        # 绑定右键菜单
        self.salary_tree.bind("<Button-3>", self.show_salary_menu)
    
    def edit_deduction(self):
        # 获取选中的工资记录
        selected_item = self.salary_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条工资记录！")
            return
        
        # 获取员工ID、姓名、当前扣款和月份
        item_values = self.salary_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        current_deduction = item_values[4]  # deduction是第5列（索引4）
        month = self.salary_month_var.get()
        
        # 检查是否是总计行
        if not emp_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 创建编辑扣款对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "编辑扣款", width_percent=0.5, height_percent=0.3)
        
        # 显示员工信息
        info_frame = ttk.Frame(dialog.main_frame)
        info_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(info_frame, text=f"员工：{emp_name}", font=dialog.fonts['heading']).pack(pady=2, fill="x")
        ttk.Label(info_frame, text=f"月份：{month}", font=dialog.fonts['heading']).pack(pady=2, fill="x")
        
        # 扣款输入框
        deduction_frame = ttk.Frame(dialog.main_frame)
        deduction_frame.pack(fill=X, padx=10, pady=8)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 10
        ttk.Label(deduction_frame, text="扣款金额: ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT)
        deduction_var = tk.StringVar(value=str(current_deduction))
        deduction_entry = ttk.Entry(deduction_frame, textvariable=deduction_var, font=dialog.fonts['normal'])
        deduction_entry.pack(side=LEFT, padx=5, fill="x", expand=True)
        
        # 添加提示标签
        hint_frame = ttk.Frame(dialog.main_frame)
        hint_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(hint_frame, text="提示：输入0或留空表示无扣款", font=(dialog.fonts['small'][0], dialog.fonts['small'][1], "italic"), foreground="gray").pack(fill="x")
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill=X, padx=10, pady=12)
        
        # 确认按钮
        def confirm():
            try:
                # 获取扣款金额
                deduction_str = deduction_var.get().strip()
                if not deduction_str:
                    deduction = 0
                else:
                    deduction = float(deduction_str)
                    if deduction < 0:
                        raise ValueError("扣款不能为负数")
                
                # 特别处理扣款为0的情况，确保正确转换为float类型的0.0
                deduction = float(deduction)  # 确保总是float类型
                
                # 更新数据库中的扣款信息
                result = self.update_employee_deduction(emp_id, month, deduction)
                
                if result:
                    # 刷新工资表显示
                    self.generate_salary_sheet()
                    dialog.destroy()
                    messagebox.showinfo("成功", "扣款已成功更新！")
                else:
                    messagebox.showerror("错误", "更新扣款失败！")
            except ValueError as e:
                messagebox.showerror("输入错误", str(e))
            except Exception as e:
                messagebox.showerror("错误", f"更新扣款时出现错误：{str(e)}")
        
        # 取消按钮
        def cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="取消", command=cancel).pack(side=RIGHT, padx=5)
        ttk.Button(button_frame, text="确认", command=confirm).pack(side=RIGHT, padx=5)
    
    def update_employee_deduction(self, emp_id, month, new_deduction):
        """更新员工的扣款金额并重新计算最终工资"""
        try:
            conn = sqlite3.connect(self.calculator.db_path)
            cursor = conn.cursor()
            
            # 获取当前工资记录
            cursor.execute(
                "SELECT base_salary, bonus FROM salaries WHERE emp_id=? AND month=?",
                (emp_id, month)
            )
            salary_data = cursor.fetchone()
            
            if not salary_data:
                conn.close()
                logger.warning(f"未找到员工 {emp_id} 在 {month} 月份的工资记录")
                return False
            
            base_salary, bonus = salary_data
            
            # 重新计算个人所得税（基于新的应纳税所得额）
            taxable_income = base_salary + bonus - new_deduction
            tax = self.calculator.calculate_tax(taxable_income)
            
            # 重新计算最终工资
            final_salary = base_salary + bonus - new_deduction - tax
            final_salary = round(final_salary, 2)
            
            # 更新数据库
            cursor.execute(
                """UPDATE salaries 
                SET deduction=?, final_salary=? 
                WHERE emp_id=? AND month=?""",
                (new_deduction, final_salary, emp_id, month)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"已更新员工 {emp_id} 在 {month} 月份的扣款为: {new_deduction}")
            return True
        except Exception as e:
            logger.error(f"更新扣款失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def delete_employee_id(self):
        """删除选中的员工ID（仅管理员有权限）"""
        if self.user_role != 'admin':
            messagebox.showerror("错误", "只有管理员才有权限删除员工ID！")
            return
        
        # 获取选中的员工
        selected_item = self.salary_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个员工！")
            return
        
        # 获取员工ID
        item_values = self.salary_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        month = self.salary_month_var.get()
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除员工 {emp_name} ({emp_id}) 在 {month} 月份的工资记录吗？"):
            try:
                # 删除工资记录
                result = self.calculator.db_manager.execute_query(
                    "DELETE FROM salaries WHERE emp_id=? AND month=?",
                    (emp_id, month)
                )
                
                if result:
                    messagebox.showinfo("成功", f"员工 {emp_name} ({emp_id}) 的工资记录已删除！")
                    self.generate_salary_sheet()  # 重新生成工资表
                else:
                    messagebox.showerror("错误", f"删除员工 {emp_name} ({emp_id}) 的工资记录失败！")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败：{str(e)}")
    
    def generate_salary_sheet(self):
        """生成工资表并显示"""
        # 获取月份
        month = self.salary_month_var.get()
        logger.info(f"用户 {self.calculator.current_user.username} 触发生成 {month} 月份工资表")
        
        try:
            # 验证月份格式
            year, month_num = map(int, month.split('-'))
            if month_num < 1 or month_num > 12:
                raise ValueError
        except ValueError:
            logger.warning(f"用户 {self.calculator.current_user.username} 输入无效月份格式: {month}")
            messagebox.showerror("错误", "月份格式必须是 YYYY-MM！")
            return
        
        try:
            # 生成工资表
            salary_sheet = self.calculator.generate_salary_sheet(month)
            
            # 清空Treeview
            for item in self.salary_tree.get_children():
                self.salary_tree.delete(item)
            
            # 添加到Treeview
            total_salary = 0
            total_tax = 0
            total_bonus = 0
            total_deduction = 0
            for salary in salary_sheet:
                # 获取发放状态
                result = self.calculator.db_manager.execute_query(
                    "SELECT status, payment_date FROM salaries WHERE emp_id=? AND month=?",
                    (salary['emp_id'], month),
                    fetch_one=True
                )
                
                status = result[0] if result else "unpaid"
                payment_date = result[1] if result and result[1] else ""
                
                # 转换状态为中文
                status_text = "已发放" if status == "paid" else "未发放"
                
                # 检查salary字典中是否包含tax键
                tax = salary.get('tax', 0)
                
                self.salary_tree.insert("", tk.END,
                    values=(salary['emp_id'], salary['name'], round(salary['base_salary'], 2),
                            round(salary['bonus'], 2), round(salary['deduction'], 2), round(tax, 2),
                            round(salary['final_salary'], 2), status_text, payment_date))
                
                total_salary += salary['final_salary']
                total_tax += tax
                total_bonus += salary['bonus']
                total_deduction += salary['deduction']
            
            # 显示总计
            self.salary_tree.insert("", tk.END,
                values=("", "总计", "", round(total_bonus, 2), round(total_deduction, 2), 
                        round(total_tax, 2), round(total_salary, 2), "", ""))
            
            logger.info(f"{month} 月份工资表显示完成，共 {len(salary_sheet)} 条记录，总工资: {total_salary}，总税额: {total_tax}，总奖金: {total_bonus}，总扣款: {total_deduction}")
            messagebox.showinfo("成功", f"工资表生成成功，共{len(salary_sheet)}名员工！")
        except Exception as e:
            logger.error(f"生成工资表失败: {str(e)}")
            messagebox.showerror("错误", f"生成工资表失败：{str(e)}")
    
    def print_individual_salary_sheet(self):
        """打印个人工资表"""
        # 获取选中的工资记录
        selected_item = self.salary_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条工资记录！")
            return
        
        # 获取员工ID和月份
        item_values = self.salary_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        month = self.salary_month_var.get()
        base_salary = item_values[2]
        bonus = item_values[3]
        deduction = item_values[4]
        tax = item_values[5]
        final_salary = item_values[6]
        status = item_values[7]
        payment_date = item_values[8]
        
        # 检查是否是总计行
        if not emp_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        try:
            # 导入必要的库
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            import tempfile
            import os
            import subprocess
            import logging
            
            # 配置日志
            logging.basicConfig(level=logging.DEBUG, 
                               filename='salary_print.log',
                               format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            logger = logging.getLogger('salary_print')
            
            # 获取员工详细信息
            emp_info = self.calculator.db_manager.execute_query(
                "SELECT department, position, hire_date FROM employees WHERE emp_id=?",
                (emp_id,),
                fetch_one=True
            )
            
            if not emp_info:
                messagebox.showerror("错误", f"未找到员工{emp_name}的详细信息！")
                return
            
            department, position, hire_date = emp_info
            
            # 将字符串类型的数值转换为浮点数
            try:
                base_salary = float(base_salary) if base_salary else 0.0
                bonus = float(bonus) if bonus else 0.0
                deduction = float(deduction) if deduction else 0.0
                tax = float(tax) if tax else 0.0
                final_salary = float(final_salary) if final_salary else 0.0
            except (ValueError, TypeError):
                # 如果转换失败，使用默认值
                base_salary = 0.0
                bonus = 0.0
                deduction = 0.0
                tax = 0.0
                final_salary = 0.0
            
            # 创建临时PDF文件
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                pdf_path = temp_pdf.name
                logger.info(f"创建临时PDF文件: {pdf_path}")
                
                # 创建PDF文档和样式
                doc = SimpleDocTemplate(pdf_path, pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()
                
                # 使用默认样式，避免字体问题
                body_style = styles['BodyText']
                heading_style = styles['Heading1']
                heading_style.alignment = 1  # 居中
                
                # 添加文本内容(使用简单的文本格式)
                elements.append(Paragraph(f"{month}月份工资表", heading_style))
                elements.append(Spacer(1, 24))
                
                elements.append(Paragraph("===== 员工信息 ====", body_style))
                elements.append(Paragraph(f"员工ID: {emp_id}", body_style))
                elements.append(Paragraph(f"姓名: {emp_name}", body_style))
                elements.append(Paragraph(f"部门: {department or ''}", body_style))
                elements.append(Paragraph(f"职位: {position or ''}", body_style))
                elements.append(Paragraph(f"入职日期: {hire_date or ''}", body_style))
                elements.append(Spacer(1, 24))
                
                elements.append(Paragraph("===== 工资详情 ====", body_style))
                elements.append(Paragraph(f"基本工资: {base_salary:.2f} 元", body_style))
                elements.append(Paragraph(f"奖金: {bonus:.2f} 元", body_style))
                elements.append(Paragraph(f"扣款: {deduction:.2f} 元", body_style))
                elements.append(Paragraph(f"个人所得税: {tax:.2f} 元", body_style))
                elements.append(Paragraph(f"实发工资: {final_salary:.2f} 元", body_style))
                elements.append(Spacer(1, 24))
                
                elements.append(Paragraph("===== 发放信息 ====", body_style))
                elements.append(Paragraph(f"发放状态: {status}", body_style))
                elements.append(Paragraph(f"发放日期: {payment_date or '未发放'}", body_style))
                
                # 构建PDF
                doc.build(elements)
                logger.info("成功构建PDF文件")
                
                # 打印PDF文件
                if os.name == 'nt':  # Windows系统
                    os.startfile(pdf_path, 'print')
                else:  # 非Windows系统
                    subprocess.run(['lp', pdf_path])
                logger.info(f"成功发送{emp_name}的工资表到打印机")
                messagebox.showinfo("成功", f"{emp_name}的个人工资表已发送到打印机！\n临时文件: {pdf_path}")
                
        except ImportError as e:
            logging.error(f"缺少必要的库: {str(e)}")
            messagebox.showerror("错误", f"缺少必要的库: {str(e)}\n请安装reportlab库以支持打印功能。\n\npip install reportlab")
        except Exception as e:
            logging.error(f"打印工资表失败: {str(e)}")
            messagebox.showerror("错误", f"打印工资表失败：{str(e)}\n\n详细错误信息已记录到salary_print.log文件中。")
    
    def show_salary_menu(self, event):
        # 选中点击的项
        item = self.salary_tree.identify_row(event.y)
        if item:
            self.salary_tree.selection_set(item)
            
            # 创建右键菜单
            menu = tk.Menu(self.root, tearoff=0)
            
            # 添加编辑奖金选项（对操作管理员和管理员都可用）
            menu.add_command(label="编辑奖金", command=self.edit_bonus)
            
            # 添加编辑扣款选项（对操作管理员和管理员都可用）
            menu.add_command(label="编辑扣款", command=self.edit_deduction)
            
            # 添加标记发放选项
            menu.add_command(label="标记发放", command=self.mark_paid)
            
            # 如果是管理员，添加其他选项
            if self.user_role == 'admin':
                menu.add_separator()
                menu.add_command(label="取消标记发放", command=self.mark_unpaid)
                menu.add_command(label="删除工资记录", command=self.delete_employee_id)
            
            # 显示菜单
            menu.post(event.x_root, event.y_root)
    
    def edit_bonus(self):
        # 获取选中的工资记录
        selected_item = self.salary_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条工资记录！")
            return
        
        # 获取员工ID、姓名、当前奖金和月份
        item_values = self.salary_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        current_bonus = item_values[3]
        month = self.salary_month_var.get()
        
        # 检查是否是总计行
        if not emp_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 创建编辑奖金对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "编辑奖金", width_percent=0.6, height_percent=0.5)
        
        # 为标签设置合适的宽度
        label_width = 10 if dialog.winfo_width() < 400 else 12
        
        # 显示员工信息
        ttk.Label(dialog.main_frame, text=f"员工：{emp_name}", font=dialog.fonts['normal']).pack(padx=10, pady=5)
        ttk.Label(dialog.main_frame, text=f"月份：{month}", font=dialog.fonts['normal']).pack(padx=10)
        
        # 奖金输入框
        bonus_frame = ttk.Frame(dialog.main_frame)
        bonus_frame.pack(fill=X, padx=10, pady=8)
        
        ttk.Label(bonus_frame, text="奖金金额: ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT)
        bonus_var = tk.StringVar(value=str(current_bonus))
        bonus_entry = ttk.Entry(bonus_frame, textvariable=bonus_var, font=dialog.fonts['normal'])
        bonus_entry.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        # 添加提示标签
        ttk.Label(dialog.main_frame, text="提示：输入0或留空表示无奖金", font=dialog.fonts['small'], foreground="gray").pack(padx=10, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill=X, padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                # 获取奖金金额
                bonus_str = bonus_var.get().strip()
                if not bonus_str:
                    bonus = 0
                else:
                    bonus = float(bonus_str)
                    if bonus < 0:
                        raise ValueError("奖金不能为负数")
                
                # 特别处理奖金为0的情况，确保正确转换为float类型的0.0
                bonus = float(bonus)  # 确保总是float类型
                
                # 增加日志记录，便于调试
                logger.info(f"尝试更新员工 {emp_id} 在 {month} 月份的奖金为: {bonus}")
                
                # 更新奖金
                if self.calculator.update_employee_bonus(emp_id, month, bonus):
                    messagebox.showinfo("成功", f"已更新{emp_name}的奖金为：{bonus}元！")
                    dialog.destroy()
                    self.generate_salary_sheet()
                else:
                    # 检查是否因为记录不存在导致失败
                    check_result = self.calculator.db_manager.execute_query(
                        "SELECT id FROM salaries WHERE emp_id=? AND month=?",
                        (emp_id, month),
                        fetch_one=True
                    )
                    if not check_result:
                        messagebox.showerror("错误", f"未找到{emp_name}在{month}月份的工资记录！\n请先生成工资表。")
                    else:
                        messagebox.showerror("错误", "更新奖金失败，请重试！")
            except ValueError as e:
                messagebox.showerror("错误", f"请输入有效的奖金金额：{str(e)}")
            except Exception as e:
                logger.error(f"更新奖金失败: {str(e)}")
                messagebox.showerror("错误", f"更新奖金失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm, style='Accent.TButton').pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def mark_paid(self):
        # 获取选中的工资记录
        selected_item = self.salary_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条工资记录！")
            return
        
        # 获取员工ID和月份
        item_values = self.salary_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        month = self.salary_month_var.get()
        
        # 检查是否是总计行
        if not emp_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 确认标记发放
        if messagebox.askyesno("确认", f"确定要标记{emp_name}的工资为已发放吗？"):
            try:
                # 先检查工资记录是否存在
                result = self.calculator.db_manager.execute_query(
                    "SELECT id FROM salaries WHERE emp_id=? AND month=?",
                    (emp_id, month),
                    fetch_one=True
                )
                
                if not result:
                    messagebox.showerror("错误", f"未找到{emp_name}在{month}月份的工资记录！\n请先生成工资表。")
                    return
                
                if self.calculator.mark_salary_paid(emp_id, month):
                    messagebox.showinfo("成功", f"已标记{emp_name}的工资为已发放！")
                    self.generate_salary_sheet()
                else:
                    messagebox.showerror("错误", "标记发放失败，请重试！")
            except Exception as e:
                messagebox.showerror("错误", f"标记发放失败：{str(e)}")
    
    def batch_mark_paid(self):
        # 获取月份
        month = self.salary_month_var.get()
        
        # 确认批量标记发放
        if messagebox.askyesno("确认", f"确定要批量标记{month}月份所有员工的工资为已发放吗？"):
            try:
                # 获取工资表中的员工ID
                emp_ids = []
                for item in self.salary_tree.get_children():
                    emp_id = self.salary_tree.item(item)["values"][0]
                    if emp_id:  # 跳过总计行
                        emp_ids.append(emp_id)
                
                # 批量标记发放
                success_count = 0
                for emp_id in emp_ids:
                    if self.calculator.mark_salary_paid(emp_id, month):
                        success_count += 1
                
                messagebox.showinfo("成功", f"已成功标记{success_count}名员工的工资为已发放！")
                self.generate_salary_sheet()
            except Exception as e:
                messagebox.showerror("错误", f"批量标记发放失败：{str(e)}")
    
    def mark_unpaid(self):
        # 获取选中的工资记录
        selected_item = self.salary_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条工资记录！")
            return
        
        # 获取员工ID和月份
        item_values = self.salary_tree.item(selected_item[0])["values"]
        emp_id = item_values[0]
        emp_name = item_values[1]
        month = self.salary_month_var.get()
        
        # 检查是否是总计行
        if not emp_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 确认取消标记发放
        if messagebox.askyesno("确认", f"确定要取消标记{emp_name}的工资发放状态吗？"):
            try:
                # 先检查工资记录是否存在
                result = self.calculator.db_manager.execute_query(
                    "SELECT id FROM salaries WHERE emp_id=? AND month=?",
                    (emp_id, month),
                    fetch_one=True
                )
                
                if not result:
                    messagebox.showerror("错误", f"未找到{emp_name}在{month}月份的工资记录！\n请先生成工资表。")
                    return
                
                if self.calculator.mark_salary_unpaid(emp_id, month):
                    messagebox.showinfo("成功", f"已取消标记{emp_name}的工资发放状态！")
                    self.generate_salary_sheet()
                else:
                    messagebox.showerror("错误", "取消标记失败，请重试！")
            except Exception as e:
                messagebox.showerror("错误", f"取消标记失败：{str(e)}")
    
    def batch_mark_unpaid(self):
        # 获取月份
        month = self.salary_month_var.get()
        
        # 确认批量取消标记发放
        if messagebox.askyesno("确认", f"确定要批量取消标记{month}月份所有员工的工资发放状态吗？"):
            try:
                # 获取工资表中的员工ID
                emp_ids = []
                for item in self.salary_tree.get_children():
                    emp_id = self.salary_tree.item(item)["values"][0]
                    if emp_id:  # 跳过总计行
                        emp_ids.append(emp_id)
                
                # 批量取消标记发放
                success_count = 0
                for emp_id in emp_ids:
                    if self.calculator.mark_salary_unpaid(emp_id, month):
                        success_count += 1
                
                messagebox.showinfo("成功", f"已成功取消标记{success_count}名员工的工资发放状态！")
                self.generate_salary_sheet()
            except Exception as e:
                messagebox.showerror("错误", f"批量取消标记发放失败：{str(e)}")
    
    def export_to_excel(self):
        # 获取月份
        month = self.salary_month_var.get()
        
        try:
            # 验证月份格式
            year, month_num = map(int, month.split('-'))
            if month_num < 1 or month_num > 12:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "月份格式必须是 YYYY-MM！")
            return
        
        try:
            # 创建Excel工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = f"{month}工资表"
            
            # 添加表头
            headers = ["员工ID", "姓名", "基本工资", "奖金", "扣款", "个人所得税", "实发工资", "状态", "发放日期"]
            ws.append(headers)
            
            # 添加数据
            total_salary = 0
            total_tax = 0
            for item in self.salary_tree.get_children():
                values = self.salary_tree.item(item)["values"]
                ws.append(values)
                if values[0]:  # 不是总计行
                    total_salary += values[6] if isinstance(values[6], (int, float)) else 0
                    total_tax += values[5] if isinstance(values[5], (int, float)) else 0
            
            # 添加总计
            ws.append(["", "总计", "", "", "", total_tax, total_salary, "", ""])
            
            # 保存文件
            filename = f"{month}工资表.xlsx"
            wb.save(filename)
            
            messagebox.showinfo("成功", f"工资表已导出至 {filename}！")
        except Exception as e:
            messagebox.showerror("错误", f"导出Excel失败：{str(e)}")
    
    def init_report_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.report_frame)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=X, padx=5, pady=5)
        
        # 年份选择
        year_frame = ttk.Frame(control_frame)
        year_frame.pack(side=LEFT, padx=5)
        
        ttk.Label(year_frame, text="年份: ").pack(side=LEFT)
        current_year = datetime.datetime.now().year
        self.report_year_var = tk.StringVar(value=str(current_year))
        ttk.Entry(year_frame, textvariable=self.report_year_var, width=6).pack(side=LEFT, padx=5)
        
        # 报表类型选择
        report_type_frame = ttk.Frame(control_frame)
        report_type_frame.pack(side=LEFT, padx=5)
        
        ttk.Label(report_type_frame, text="报表类型: ").pack(side=LEFT)
        self.report_type_var = tk.StringVar(value="salary")
        report_type_combo = ttk.Combobox(report_type_frame, textvariable=self.report_type_var, 
                                       values=["salary", "revenue", "profit", "attendance"], 
                                       state="readonly", width=10)
        report_type_combo.pack(side=LEFT, padx=5)
        
        # 导出按钮
        ttk.Button(control_frame, text="导出报表", command=self.export_report).pack(side=LEFT, padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新图表", command=self.update_charts).pack(side=LEFT, padx=5)
        
        # 创建图表框架
        charts_frame = ttk.Frame(main_frame)
        charts_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 上方图表
        top_frame = ttk.LabelFrame(charts_frame, text="趋势图")
        top_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建趋势图
        self.fig1, self.ax1 = plt.subplots(figsize=(10, 4), dpi=100)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=top_frame)
        self.canvas1.get_tk_widget().pack(fill=BOTH, expand=True)
        
        # 下方图表
        bottom_frame = ttk.Frame(charts_frame)
        bottom_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 左侧图表
        left_bottom_frame = ttk.LabelFrame(bottom_frame, text="分布图表")
        left_bottom_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建分布图
        self.fig2, self.ax2 = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=left_bottom_frame)
        self.canvas2.get_tk_widget().pack(fill=BOTH, expand=True)
        
        # 右侧图表
        right_bottom_frame = ttk.LabelFrame(bottom_frame, text="对比图表")
        right_bottom_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建对比图
        self.fig3, self.ax3 = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=right_bottom_frame)
        self.canvas3.get_tk_widget().pack(fill=BOTH, expand=True)
    
    def update_charts(self):
        # 获取年份和报表类型
        year = self.report_year_var.get()
        report_type = self.report_type_var.get()
        
        try:
            year = int(year)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的年份！")
            return
        
        try:
            # 连接数据库
            conn = sqlite3.connect(self.calculator.db_path)
            
            # 清空所有图表
            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            
            if report_type == "salary":
                # 工资报表
                # 更新月度工资总额趋势图
                self.update_salary_trend_chart(conn, year)
                # 更新部门工资分布图表
                self.update_department_salary_chart(conn, year)
                # 更新员工工资对比图表
                self.update_employee_salary_comparison_chart(conn, year)
            elif report_type == "revenue":
                # 收入报表
                # 更新月度收入趋势图
                self.update_revenue_trend_chart(conn, year)
                # 更新部门收入分布图表
                self.update_department_revenue_chart(conn, year)
                # 更新收入来源对比图表
                self.update_revenue_source_chart(conn, year)
            elif report_type == "profit":
                # 利润报表
                # 更新月度利润趋势图
                self.update_profit_trend_chart(conn, year)
                # 更新利润构成图表
                self.update_profit_composition_chart(conn, year)
                # 更新同比环比分析图表
                self.update_profit_analysis_chart(conn, year)
            elif report_type == "attendance":
                # 考勤报表
                # 更新月度出勤率趋势图
                self.update_attendance_trend_chart(conn, year)
                # 更新部门出勤分布图表
                self.update_department_attendance_chart(conn, year)
                # 更新员工出勤对比图表
                self.update_employee_attendance_chart(conn, year)
            
            # 绘制所有图表
            self.fig1.tight_layout()
            self.canvas1.draw()
            self.fig2.tight_layout()
            self.canvas2.draw()
            self.fig3.tight_layout()
            self.canvas3.draw()
            
            conn.close()
        except Exception as e:
            messagebox.showerror("错误", f"更新图表失败：{str(e)}")
    
    def update_salary_trend_chart(self, conn, year):
        # 获取月度工资数据
        months = []
        totals = []
        
        for month in range(1, 13):
            month_str = f"{year}-{month:02d}"
            cursor = conn.cursor()
            cursor.execute(
                """SELECT SUM(final_salary) FROM salaries 
                WHERE month=? AND status='paid'""",
                (month_str,)
            )
            total = cursor.fetchone()[0] or 0
            months.append(f"{month}月")
            totals.append(total)
        
        # 绘制柱状图
        self.ax1.bar(months, totals)
        self.ax1.set_title(f"{year}年月度工资总额趋势")
        self.ax1.set_xlabel("月份")
        self.ax1.set_ylabel("工资总额 (元)")
        self.ax1.tick_params(axis='x', rotation=45)
        
        # 添加数据标签
        for i, v in enumerate(totals):
            if v > 0:
                self.ax1.text(i, v, f"{v:.0f}", ha='center', va='bottom')
    
    def update_department_salary_chart(self, conn, year):
        # 获取部门工资数据
        departments = {}
        
        # 获取所有部门
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM employees")
        dept_rows = cursor.fetchall()
        
        for dept_row in dept_rows:
            dept = dept_row[0]
            departments[dept] = 0
        
        # 计算各部门工资总额
        for month in range(1, 13):
            month_str = f"{year}-{month:02d}"
            cursor = conn.cursor()
            cursor.execute(
                """SELECT e.department, SUM(s.final_salary) 
                FROM salaries s 
                JOIN employees e ON s.emp_id = e.emp_id 
                WHERE s.month=? AND s.status='paid' 
                GROUP BY e.department""",
                (month_str,)
            )
            dept_salary_rows = cursor.fetchall()
            
            for dept, salary in dept_salary_rows:
                departments[dept] += salary or 0
        
        # 提取部门和对应的工资总额
        dept_list = list(departments.keys())
        salary_list = list(departments.values())
        
        # 绘制饼图
        self.ax2.pie(salary_list, labels=dept_list, autopct='%1.1f%%', startangle=90)
        self.ax2.set_title(f"{year}年各部门工资分布")
        self.ax2.axis('equal')  # 使饼图为正圆形
    
    def update_employee_salary_comparison_chart(self, conn, year):
        # 获取Top 10员工工资数据
        cursor = conn.cursor()
        cursor.execute(
            """SELECT e.name, SUM(s.final_salary) as total_salary 
            FROM salaries s 
            JOIN employees e ON s.emp_id = e.emp_id 
            WHERE s.month LIKE ? AND s.status='paid' 
            GROUP BY e.emp_id 
            ORDER BY total_salary DESC 
            LIMIT 10""",
            (f"{year}%",)
        )
        employee_salary_rows = cursor.fetchall()
        
        if not employee_salary_rows:
            self.ax3.text(0.5, 0.5, "无数据", ha='center', va='center')
            return
        
        # 提取员工姓名和工资
        names = [row[0] for row in employee_salary_rows]
        salaries = [row[1] for row in employee_salary_rows]
        
        # 绘制条形图
        self.ax3.barh(names, salaries)
        self.ax3.set_title(f"{year}年工资Top 10员工")
        self.ax3.set_xlabel("工资总额 (元)")
        self.ax3.set_ylabel("员工姓名")
    
    def update_revenue_trend_chart(self, conn, year):
        # 获取月度收入数据
        months = []
        totals = []
        
        for month in range(1, 13):
            month_str = f"{year}-{month:02d}-01"
            next_month = month + 1
            next_year = year
            if next_month > 12:
                next_month = 1
                next_year += 1
            next_month_str = f"{next_year}-{next_month:02d}-01"
            
            cursor = conn.cursor()
            cursor.execute(
                """SELECT SUM(amount) FROM revenue 
                WHERE date >= ? AND date < ?""",
                (month_str, next_month_str)
            )
            total = cursor.fetchone()[0] or 0
            months.append(f"{month}月")
            totals.append(total)
        
        # 绘制折线图
        self.ax1.plot(months, totals, marker='o')
        self.ax1.set_title(f"{year}年月度收入趋势")
        self.ax1.set_xlabel("月份")
        self.ax1.set_ylabel("收入总额 (元)")
        self.ax1.tick_params(axis='x', rotation=45)
        self.ax1.grid(True)
    
    def update_department_revenue_chart(self, conn, year):
        # 获取部门收入数据
        departments = {}
        
        # 获取所有部门
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM employees")
        dept_rows = cursor.fetchall()
        
        for dept_row in dept_rows:
            dept = dept_row[0]
            departments[dept] = 0
        
        # 计算各部门收入总额
        cursor = conn.cursor()
        cursor.execute(
            """SELECT e.department, SUM(r.amount) 
            FROM revenue r 
            JOIN employees e ON r.emp_id = e.emp_id 
            WHERE r.date LIKE ? 
            GROUP BY e.department""",
            (f"{year}%",)
        )
        dept_revenue_rows = cursor.fetchall()
        
        for dept, revenue in dept_revenue_rows:
            if dept in departments:
                departments[dept] += revenue or 0
        
        # 提取部门和对应的收入总额
        dept_list = list(departments.keys())
        revenue_list = list(departments.values())
        
        # 绘制饼图
        self.ax2.pie(revenue_list, labels=dept_list, autopct='%1.1f%%', startangle=90)
        self.ax2.set_title(f"{year}年各部门收入分布")
        self.ax2.axis('equal')  # 使饼图为正圆形
    
    def update_revenue_source_chart(self, conn, year):
        # 获取收入来源数据（按描述分类）
        sources = {}
        
        cursor = conn.cursor()
        cursor.execute(
            """SELECT description, SUM(amount) 
            FROM revenue 
            WHERE date LIKE ? 
            GROUP BY description""",
            (f"{year}%",)
        )
        source_rows = cursor.fetchall()
        
        for desc, amount in source_rows:
            source = desc[:10] + '...' if len(desc) > 10 else desc
            sources[source] = amount or 0
        
        # 提取来源和对应的收入
        source_list = list(sources.keys())
        amount_list = list(sources.values())
        
        # 绘制条形图
        self.ax3.bar(source_list, amount_list)
        self.ax3.set_title(f"{year}年收入来源分布")
        self.ax3.set_xlabel("收入来源")
        self.ax3.set_ylabel("收入金额 (元)")
        self.ax3.tick_params(axis='x', rotation=45)
    
    def update_profit_trend_chart(self, conn, year):
        # 获取月度利润数据
        months = []
        profits = []
        
        for month in range(1, 13):
            month_str = f"{year}-{month:02d}-01"
            next_month = month + 1
            next_year = year
            if next_month > 12:
                next_month = 1
                next_year += 1
            next_month_str = f"{next_year}-{next_month:02d}-01"
            
            # 计算收入
            cursor = conn.cursor()
            cursor.execute(
                """SELECT SUM(amount) FROM revenue 
                WHERE date >= ? AND date < ?""",
                (month_str, next_month_str)
            )
            revenue = cursor.fetchone()[0] or 0
            
            # 计算工资支出
            cursor.execute(
                """SELECT SUM(final_salary) FROM salaries 
                WHERE payment_date >= ? AND payment_date < ?""",
                (month_str, next_month_str)
            )
            salary = cursor.fetchone()[0] or 0
            
            # 利润 = 收入 - 工资支出
            profit = revenue - salary
            months.append(f"{month}月")
            profits.append(profit)
        
        # 绘制折线图
        self.ax1.plot(months, profits, marker='o')
        self.ax1.axhline(y=0, color='r', linestyle='-')
        self.ax1.set_title(f"{year}年月度利润趋势")
        self.ax1.set_xlabel("月份")
        self.ax1.set_ylabel("利润 (元)")
        self.ax1.tick_params(axis='x', rotation=45)
        self.ax1.grid(True)
    
    def update_profit_composition_chart(self, conn, year):
        # 获取年度总收入和总支出
        cursor = conn.cursor()
        cursor.execute(
            """SELECT SUM(amount) FROM revenue 
            WHERE date LIKE ?""",
            (f"{year}%",)
        )
        total_revenue = cursor.fetchone()[0] or 0
        
        cursor.execute(
            """SELECT SUM(final_salary) FROM salaries 
            WHERE payment_date LIKE ?""",
            (f"{year}%",)
        )
        total_salary = cursor.fetchone()[0] or 0
        
        # 其他支出（假设为总收入的10%用于演示）
        other_expenses = total_revenue * 0.1
        
        # 计算利润
        profit = total_revenue - total_salary - other_expenses
        
        # 数据准备
        labels = ['收入', '工资支出', '其他支出', '利润']
        values = [total_revenue, -total_salary, -other_expenses, profit]
        colors = ['green', 'red', 'orange', 'blue']
        
        # 绘制堆叠柱状图
        self.ax2.bar(labels, values, color=colors)
        self.ax2.axhline(y=0, color='black', linestyle='-')
        self.ax2.set_title(f"{year}年利润构成")
        self.ax2.set_ylabel("金额 (元)")
    
    def update_profit_analysis_chart(self, conn, year):
        # 同比分析（与去年对比）
        last_year = year - 1
        
        # 获取今年收入
        cursor = conn.cursor()
        cursor.execute(
            """SELECT SUM(amount) FROM revenue 
            WHERE date LIKE ?""",
            (f"{year}%",)
        )
        this_year_revenue = cursor.fetchone()[0] or 0
        
        # 获取去年收入
        cursor.execute(
            """SELECT SUM(amount) FROM revenue 
            WHERE date LIKE ?""",
            (f"{last_year}%",)
        )
        last_year_revenue = cursor.fetchone()[0] or 0
        
        # 获取今年利润
        cursor.execute(
            """SELECT SUM(amount) - (SELECT SUM(final_salary) FROM salaries WHERE payment_date LIKE ?) 
            FROM revenue 
            WHERE date LIKE ?""",
            (f"{year}%", f"{year}%",)
        )
        this_year_profit = cursor.fetchone()[0] or 0
        
        # 获取去年利润
        cursor.execute(
            """SELECT SUM(amount) - (SELECT SUM(final_salary) FROM salaries WHERE payment_date LIKE ?) 
            FROM revenue 
            WHERE date LIKE ?""",
            (f"{last_year}%", f"{last_year}%",)
        )
        last_year_profit = cursor.fetchone()[0] or 0
        
        # 数据准备
        labels = ['收入', '利润']
        this_year_values = [this_year_revenue, this_year_profit]
        last_year_values = [last_year_revenue, last_year_profit]
        
        # 绘制对比条形图
        x = range(len(labels))
        width = 0.35
        
        self.ax3.bar([i - width/2 for i in x], last_year_values, width, label=f'{last_year}年')
        self.ax3.bar([i + width/2 for i in x], this_year_values, width, label=f'{year}年')
        
        self.ax3.set_title(f"{year}年与{last_year}年对比分析")
        self.ax3.set_ylabel("金额 (元)")
        self.ax3.set_xticks(x)
        self.ax3.set_xticklabels(labels)
        self.ax3.legend()
    
    def export_report(self):
        # 获取年份和报表类型
        year = self.report_year_var.get()
        report_type = self.report_type_var.get()
        
        try:
            year = int(year)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的年份！")
            return
        
        try:
            # 创建Excel工作簿
            wb = Workbook()
            ws = wb.active
            
            # 连接数据库
            conn = sqlite3.connect(self.calculator.db_path)
            cursor = conn.cursor()
            
            if report_type == "salary":
                # 工资报表
                ws.title = f"{year}年工资报表"
                
                # 添加表头
                ws.append(["月份", "工资总额", "部门分布", "备注"])
                
                # 添加月度工资数据
                for month in range(1, 13):
                    month_str = f"{year}-{month:02d}"
                    cursor.execute(
                        """SELECT SUM(final_salary) FROM salaries 
                        WHERE month=? AND status='paid'""",
                        (month_str,)
                    )
                    total = cursor.fetchone()[0] or 0
                    
                    # 获取部门分布
                    cursor.execute(
                        """SELECT e.department, SUM(s.final_salary) 
                        FROM salaries s 
                        JOIN employees e ON s.emp_id = e.emp_id 
                        WHERE s.month=? AND s.status='paid' 
                        GROUP BY e.department""",
                        (month_str,)
                    )
                    dept_dist = cursor.fetchall()
                    dept_str = ", ".join([f"{dept}: {salary:.2f}" for dept, salary in dept_dist])
                    
                    ws.append([f"{month}月", total, dept_str, ""])
            elif report_type == "revenue":
                # 收入报表
                ws.title = f"{year}年收入报表"
                
                # 添加表头
                ws.append(["月份", "收入总额", "部门分布", "备注"])
                
                # 添加月度收入数据
                for month in range(1, 13):
                    month_str = f"{year}-{month:02d}-01"
                    next_month = month + 1
                    next_year = year
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                    next_month_str = f"{next_year}-{next_month:02d}-01"
                    
                    cursor.execute(
                        """SELECT SUM(amount) FROM revenue 
                        WHERE date >= ? AND date < ?""",
                        (month_str, next_month_str)
                    )
                    total = cursor.fetchone()[0] or 0
                    
                    # 获取部门分布
                    cursor.execute(
                        """SELECT e.department, SUM(r.amount) 
                        FROM revenue r 
                        JOIN employees e ON r.emp_id = e.emp_id 
                        WHERE r.date >= ? AND r.date < ? 
                        GROUP BY e.department""",
                        (month_str, next_month_str)
                    )
                    dept_dist = cursor.fetchall()
                    dept_str = ", ".join([f"{dept}: {amount:.2f}" for dept, amount in dept_dist])
                    
                    ws.append([f"{month}月", total, dept_str, ""])
            elif report_type == "profit":
                # 利润报表
                ws.title = f"{year}年利润报表"
                
                # 添加表头
                ws.append(["月份", "收入", "工资支出", "其他支出", "利润", "备注"])
                
                # 添加月度利润数据
                for month in range(1, 13):
                    month_str = f"{year}-{month:02d}-01"
                    next_month = month + 1
                    next_year = year
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                    next_month_str = f"{next_year}-{next_month:02d}-01"
                    
                    # 计算收入
                    cursor.execute(
                        """SELECT SUM(amount) FROM revenue 
                        WHERE date >= ? AND date < ?""",
                        (month_str, next_month_str)
                    )
                    revenue = cursor.fetchone()[0] or 0
                    
                    # 计算工资支出
                    cursor.execute(
                        """SELECT SUM(final_salary) FROM salaries 
                        WHERE payment_date >= ? AND payment_date < ?""",
                        (month_str, next_month_str)
                    )
                    salary = cursor.fetchone()[0] or 0
                    
                    # 其他支出（假设为收入的10%）
                    other_expenses = revenue * 0.1
                    
                    # 计算利润
                    profit = revenue - salary - other_expenses
                    
                    ws.append([f"{month}月", revenue, salary, other_expenses, profit, ""])
            elif report_type == "attendance":
                # 考勤报表
                ws.title = f"{year}年考勤报表"
                
                # 添加表头
                ws.append(["月份", "工作日总数", "员工总数", "出勤总天数", "出勤率", "备注"])
                
                # 添加月度考勤数据
                for month in range(1, 13):
                    month_str = f"{year}-{month:02d}"
                    # 计算工作日总数
                    _, days_in_month = calendar.monthrange(year, month)
                    weekdays = 0
                    for day in range(1, days_in_month + 1):
                        date = datetime.date(year, month, day)
                        if date.weekday() < 5:  # 0-4表示周一到周五
                            weekdays += 1
                    
                    # 计算员工总数
                    cursor.execute("SELECT COUNT(*) FROM employees WHERE status='active'")
                    total_employees = cursor.fetchone()[0] or 0
                    
                    # 计算出勤总天数
                    cursor.execute(
                        """SELECT COUNT(*) FROM attendance 
                        WHERE date LIKE ? AND status='present'""",
                        (f"{month_str}%",)
                    )
                    present_days = cursor.fetchone()[0] or 0
                    
                    # 计算出勤率
                    attendance_rate = (present_days / (total_employees * weekdays)) * 100 if (total_employees * weekdays) > 0 else 0
                    
                    ws.append([f"{month}月", weekdays, total_employees, present_days, f"{attendance_rate:.2f}%", ""])
            
            # 保存文件
            filename = f"{year}_{report_type}_report.xlsx"
            wb.save(filename)
            
            conn.close()
            
            messagebox.showinfo("成功", f"报表已导出至 {filename}！")
        except Exception as e:
            messagebox.showerror("错误", f"导出报表失败：{str(e)}")

    def init_revenue_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.revenue_frame)
        # 适配手机屏幕：减少边距
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 添加响应式布局支持
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 顶部控制面板 - 适配手机屏幕：调整布局
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=X, padx=5, pady=5)
        
        # 第一行按钮 - 适配手机屏幕：调整按钮布局为网格
        btn_frame1 = ttk.Frame(control_frame)
        btn_frame1.pack(fill="x", pady=(0, 5))
        
        ttk.Button(btn_frame1, text="添加收入", command=self.add_revenue, width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame1, text="删除收入", command=self.delete_revenue_record, width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame1, text="打印发票", command=self.print_invoice, width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame1, text="刷新列表", command=self.refresh_revenue_list, width=10).pack(side=LEFT, padx=2)
        
        # 日期范围选择 - 适配手机屏幕：调整日期选择布局
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(fill="x", pady=(0, 5))
        
        # 起始日期
        start_date_subframe = ttk.Frame(date_frame)
        start_date_subframe.pack(fill="x", pady=(0, 3))
        ttk.Label(start_date_subframe, text="起始日期: ", width=10).pack(side=LEFT)
        self.start_date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))  # 默认当天
        ttk.Entry(start_date_subframe, textvariable=self.start_date_var, width=15).pack(side=LEFT, padx=5)
        
        # 结束日期和统计方式
        end_date_subframe = ttk.Frame(date_frame)
        end_date_subframe.pack(fill="x", pady=(0, 3))
        ttk.Label(end_date_subframe, text="结束日期: ", width=10).pack(side=LEFT)
        self.end_date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))  # 默认当天
        ttk.Entry(end_date_subframe, textvariable=self.end_date_var, width=15).pack(side=LEFT, padx=5)
        
        # 统计选项和查询按钮
        stats_subframe = ttk.Frame(date_frame)
        stats_subframe.pack(fill="x")
        ttk.Label(stats_subframe, text="统计方式: ", width=10).pack(side=LEFT)
        self.statistics_var = tk.StringVar(value="总计")
        stats_combo = ttk.Combobox(stats_subframe, textvariable=self.statistics_var, values=["总计", "按员工"], width=12, state="readonly")
        stats_combo.pack(side=LEFT, padx=5)
        
        # 查询按钮
        ttk.Button(stats_subframe, text="查询", command=self.refresh_revenue_list, width=8).pack(side=LEFT, padx=5)
        
        # 收入列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建带水平滚动条的容器 - 适配手机屏幕：添加水平滚动支持
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True)
        
        # 创建Treeview
        columns = ("id", "date", "emp_id", "emp_name", "amount", "description", "added_by")
        self.revenue_tree = ttk.Treeview(tree_container, columns=columns, show="headings")
        
        # 设置列标题
        self.revenue_tree.heading("id", text="ID")
        self.revenue_tree.heading("date", text="日期")
        self.revenue_tree.heading("emp_id", text="员工ID")
        self.revenue_tree.heading("emp_name", text="员工姓名")
        self.revenue_tree.heading("amount", text="金额")
        self.revenue_tree.heading("description", text="描述")
        self.revenue_tree.heading("added_by", text="添加人")
        
        # 设置列宽 - 适配手机屏幕：调整列宽
        self.revenue_tree.column("id", width=50)
        self.revenue_tree.column("date", width=90)
        self.revenue_tree.column("emp_id", width=70)
        self.revenue_tree.column("emp_name", width=80)
        self.revenue_tree.column("amount", width=80, anchor=E)
        self.revenue_tree.column("description", width=150)
        self.revenue_tree.column("added_by", width=80)
        
        # 添加垂直滚动条
        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.revenue_tree.yview)
        self.revenue_tree.configure(yscroll=v_scrollbar.set)
        
        # 添加水平滚动条 - 适配手机屏幕：增加水平滚动功能
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.revenue_tree.xview)
        self.revenue_tree.configure(xscroll=h_scrollbar.set)
        
        # 布局Treeview和滚动条
        self.revenue_tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # 绑定双击事件，编辑收入记录
        self.revenue_tree.bind("<Double-1>", lambda event: self.edit_revenue())
    
    def refresh_revenue_list(self):
        # 清空Treeview
        for item in self.revenue_tree.get_children():
            self.revenue_tree.delete(item)

        # 获取日期范围
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        
        # 获取统计方式并转换为英文值
        statistics_type = getattr(self, 'statistics_var', None)
        if statistics_type:
            statistics_type_display = statistics_type.get()
            # 映射中文显示到英文值
            statistics_type_map = {"总计": "total", "按员工": "by_employee"}
            statistics_type = statistics_type_map.get(statistics_type_display, "total")
        else:
            statistics_type = 'total'  # 默认总计

        # 添加调试信息
        logger.info(f"刷新收入列表，日期范围: {start_date} 至 {end_date}，统计方式: {statistics_type}")
        
        try:
            # 验证日期格式
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
            return

        if statistics_type == 'by_employee':
            # 按员工ID统计总收入和记录数
            try:
                # 确保记录数统计准确，使用COUNT(*)来计算
                employee_revenue = self.calculator.db_manager.execute_query(
                    """SELECT r.emp_id, e.name, SUM(r.amount) as total_amount, COUNT(*) as record_count 
                       FROM revenue r 
                       LEFT JOIN employees e ON r.emp_id = e.emp_id 
                       WHERE r.date BETWEEN ? AND ? 
                       GROUP BY r.emp_id, e.name 
                       ORDER BY total_amount DESC""",
                    (start_date, end_date),
                    fetch_all=True
                )
            except Exception as e:
                logger.error(f"按员工统计收入失败: {str(e)}")
                messagebox.showerror("错误", f"获取收入数据失败: {str(e)}")
                return

            # 添加调试信息验证记录数
            logger.info(f"按员工统计结果: {employee_revenue}")

            # 添加到Treeview
            total_amount = 0
            total_records = 0  # 累计总记录数
            if employee_revenue:
                # 清空现有Treeview中的所有内容
                for item in self.revenue_tree.get_children():
                    self.revenue_tree.delete(item)
                
                # 重新设置列标题以适应员工统计模式
                # 隐藏不需要的列，设置需要的列宽度，优化记录数列的显示
                self.revenue_tree.heading("id", text="员工ID")
                self.revenue_tree.column("id", width=80)
                self.revenue_tree.heading("date", text="员工姓名")
                self.revenue_tree.column("date", width=150)
                self.revenue_tree.heading("emp_id", text="总收入")
                self.revenue_tree.column("emp_id", width=100, anchor=E)
                self.revenue_tree.heading("emp_name", text="记录数")
                self.revenue_tree.column("emp_name", width=100, anchor=E)  # 增加列宽并右对齐
                # 隐藏其他列
                for col in ["amount", "description", "added_by"]:
                    self.revenue_tree.heading(col, text="")
                    self.revenue_tree.column(col, width=0)
                
                # 直接添加数据，不添加表头行
                for record in employee_revenue:
                    emp_id, emp_name, amount, record_count = record
                    # 确保数据正确映射到调整后的列
                    self.revenue_tree.insert("", tk.END,
                        values=(emp_id or "", emp_name or "", amount, record_count, "", "", ""))
                    total_amount += amount or 0
                    total_records += record_count or 0  # 累加所有员工的记录数
                
                # 显示总计，包括总金额和总记录数
                self.revenue_tree.insert("", tk.END,
                    values=("总计", "", total_amount, total_records, "", "", ""))
            else:
                messagebox.showinfo("提示", f"在 {start_date} 至 {end_date} 期间没有找到收入记录。\n请检查日期范围或添加新的收入记录。")
        else:
            # 明细显示模式，但隐藏ID列
            # 设置列标题和宽度，隐藏ID列
            self.revenue_tree.heading("id", text="")
            self.revenue_tree.column("id", width=0)
            self.revenue_tree.heading("date", text="日期")
            self.revenue_tree.column("date", width=120)
            self.revenue_tree.heading("emp_id", text="员工ID")
            self.revenue_tree.column("emp_id", width=80)
            self.revenue_tree.heading("emp_name", text="员工姓名")
            self.revenue_tree.column("emp_name", width=100)
            self.revenue_tree.heading("amount", text="金额")
            self.revenue_tree.column("amount", width=100, anchor=E)
            self.revenue_tree.heading("description", text="描述")
            self.revenue_tree.column("description", width=250)
            self.revenue_tree.heading("added_by", text="添加人")
            self.revenue_tree.column("added_by", width=100)
            
            # 显示明细，包含ID字段用于删除和编辑操作
            try:
                revenue_records = self.calculator.db_manager.execute_query(
                    """SELECT r.id, r.date, r.emp_id, e.name, r.amount, r.description, r.added_by 
                       FROM revenue r 
                       LEFT JOIN employees e ON r.emp_id = e.emp_id 
                       WHERE r.date BETWEEN ? AND ? 
                       ORDER BY r.date DESC""",
                    (start_date, end_date),
                    fetch_all=True
                )
            except Exception as e:
                logger.error(f"查询收入记录失败: {str(e)}")
                messagebox.showerror("错误", f"获取收入数据失败: {str(e)}")
                return

            # 添加调试信息
            logger.info(f"查询结果: {revenue_records}")

            # 添加调试信息
            logger.info(f"查询到 {len(revenue_records)} 条收入记录")

            # 添加到Treeview，包含ID但不显示
            total_amount = 0
            for record in revenue_records:
                revenue_id, date, emp_id, emp_name, amount, description, added_by = record
                # 第一个值为ID，对应隐藏的ID列
                self.revenue_tree.insert("", tk.END,
                    values=(revenue_id, date, emp_id or "", emp_name or "", amount, description, added_by))
                total_amount += amount
            
            # 如果没有记录，显示提示信息
            if not revenue_records:
                messagebox.showinfo("提示", f"在 {start_date} 至 {end_date} 期间没有找到收入记录。\n请检查日期范围或添加新的收入记录。")

            # 显示总计
            self.revenue_tree.insert("", tk.END,
                values=("", "总计", "", "", total_amount, "", ""))

    def edit_revenue(self):
        # 获取选中的收入记录
        selected_item = self.revenue_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条收入记录！")
            return
        
        # 获取记录值
        item_values = self.revenue_tree.item(selected_item[0])["values"]
        revenue_id = item_values[0]
        current_date = item_values[1]
        current_emp_id = item_values[2]
        current_amount = item_values[4]
        current_description = item_values[5]
        
        # 检查是否是总计行
        if not revenue_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 创建编辑收入对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "编辑收入记录", width_percent=0.7, height_percent=0.6)
        
        # 获取所有在职员工
        employees = self.calculator.get_all_employees('active')
        # 查询出职位为"主播"的员工
        anchor_employees = [emp for emp in employees if emp.position == "主播"]

        # 创建表单字段 - 日期
        date_frame = ttk.Frame(dialog.main_frame)
        date_frame.pack(fill=X, padx=10, pady=8)
        # 为标签设置合适的宽度
        label_width = 18 if dialog.winfo_width() < 500 else 20
        ttk.Label(date_frame, text="日期 (YYYY-MM-DD): ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT)
        date_var = tk.StringVar(value=current_date)
        date_entry = ttk.Entry(date_frame, textvariable=date_var, font=dialog.fonts['normal'])
        date_entry.pack(side=LEFT, fill=X, expand=True)

        # 获取当天日期
        current_date = date_var.get()

        # 批量获取主播员工的考勤记录
        attendance_records = {}
        if anchor_employees:
            emp_ids = [emp.emp_id for emp in anchor_employees]
            placeholders = ', '.join(['?' for _ in emp_ids])
            query = f"SELECT emp_id, status FROM attendance WHERE emp_id IN ({placeholders}) AND date=?"
            params = emp_ids + [current_date]
            try:
                results = self.calculator.db_manager.execute_query(query, params, fetch_all=True)
                if results:
                    for row in results:
                        emp_id, status = row
                        attendance_records[emp_id] = status
            except Exception as e:
                logger.error(f"批量获取考勤记录失败: {str(e)}")
        
        # 获取当天已添加收入的员工ID列表
        revenue_emp_ids = []
        try:
            query = "SELECT emp_id FROM revenue WHERE date=? AND emp_id IS NOT NULL AND emp_id != ''"
            params = [current_date]
            results = self.calculator.db_manager.execute_query(query, params, fetch_all=True)
            if results:
                revenue_emp_ids = [row[0] for row in results]
        except Exception as e:
            logger.error(f"获取当天已添加收入的员工失败: {str(e)}")

        # 查询出当天出勤且未添加收入的主播员工
        present_anchor_employees = []
        for emp in anchor_employees:
            status = attendance_records.get(emp.emp_id)
            # 只保留出勤状态的主播，或者没有考勤记录的主播，且未添加收入
            if (status is None or status == "present") and emp.emp_id not in revenue_emp_ids:
                present_anchor_employees.append(emp)

        employee_list = [('', '无关联员工')] + [(emp.emp_id, f"{emp.emp_id} - {emp.name}") for emp in present_anchor_employees]
        
        # 员工选择
        emp_frame = ttk.Frame(dialog.main_frame)
        emp_frame.pack(fill=X, padx=10, pady=8)
        ttk.Label(emp_frame, text="员工: ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT)
        emp_var = tk.StringVar(value=current_emp_id)
        emp_combo = ttk.Combobox(emp_frame, textvariable=emp_var, state="readonly", font=dialog.fonts['normal'])
        emp_combo['values'] = [emp[1] for emp in employee_list]
        # 设置当前值的索引
        for i, emp in enumerate(employee_list):
            if emp[0] == current_emp_id:
                emp_combo.current(i)
                break
        emp_combo.pack(side=LEFT, fill=X, expand=True)
        
        # 金额
        amount_frame = ttk.Frame(dialog.main_frame)
        amount_frame.pack(fill=X, padx=10, pady=8)
        ttk.Label(amount_frame, text="金额: ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT)
        amount_var = tk.StringVar(value=str(current_amount))
        amount_entry = ttk.Entry(amount_frame, textvariable=amount_var, font=dialog.fonts['normal'])
        amount_entry.pack(side=LEFT, fill=X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(dialog.main_frame)
        desc_frame.pack(fill=X, padx=10, pady=8)
        ttk.Label(desc_frame, text="描述: ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT)
        desc_var = tk.StringVar(value=current_description)
        desc_entry = ttk.Entry(desc_frame, textvariable=desc_var, font=dialog.fonts['normal'])
        desc_entry.pack(side=LEFT, fill=X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill=X, padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                date = date_var.get().strip()
                # 验证日期格式
                datetime.datetime.strptime(date, '%Y-%m-%d')
                
                # 获取选中的员工ID
                emp_index = emp_combo.current()
                emp_id = employee_list[emp_index][0]
                
                # 获取金额
                try:
                    amount = float(amount_var.get().strip())
                    if amount < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("错误", "金额必须是非负数！")
                    return
                
                description = desc_var.get().strip()
                
                # 更新收入记录
                success, message = self.calculator.update_revenue(revenue_id, date, emp_id, amount, description)
                if success:
                    messagebox.showinfo("成功", message)
                    dialog.destroy()
                    self.refresh_revenue_list()
                else:
                    messagebox.showerror("错误", message)
            except ValueError:
                messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
            except Exception as e:
                messagebox.showerror("错误", f"编辑收入记录失败: {str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=LEFT, padx=10)

    def delete_revenue_record(self):
        # 获取选中的收入记录
        selected_item = self.revenue_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条收入记录！")
            return
        
        # 获取记录值
        item_values = self.revenue_tree.item(selected_item[0])["values"]
        revenue_id = item_values[0]
        emp_name = item_values[3]
        date = item_values[1]
        
        # 检查是否是总计行
        if not revenue_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除 {emp_name} 在 {date} 的收入记录吗？"):
            try:
                success, message = self.calculator.delete_revenue(revenue_id)
                if success:
                    messagebox.showinfo("成功", message)
                    self.refresh_revenue_list()
                else:
                    messagebox.showerror("错误", message)
            except Exception as e:
                messagebox.showerror("错误", f"删除收入记录失败: {str(e)}")

    def print_invoice(self):
        # 获取选中的收入记录
        selected_item = self.revenue_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条收入记录！")
            return
        
        # 获取记录值
        item_values = self.revenue_tree.item(selected_item[0])["values"]
        revenue_id = item_values[0]
        date = item_values[1]
        emp_id = item_values[2]
        emp_name = item_values[3]
        # 安全地转换金额为浮点数，处理空字符串情况
        try:
            amount = float(item_values[4]) if item_values[4] else 0.0
        except ValueError:
            messagebox.showerror("错误", "金额格式不正确！请确保金额是有效的数字。")
            return
        description = item_values[5]
        added_by = item_values[6]
        
        # 检查是否是总计行
        if not revenue_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 创建发票对话框 - 使用自适应对话框类
        invoice_window = AdaptiveDialog(self.root, f"发票 #{revenue_id}", width_percent=0.7, height_percent=0.5)
        
        # 创建发票内容框架
        content_frame = ttk.Frame(invoice_window.main_frame, padding=15)
        content_frame.pack(fill=BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(content_frame, text="收入发票", font=invoice_window.fonts['title'])
        title_label.pack(pady=15)
        
        # 发票信息
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(fill=X, pady=10)
        
        # 左侧信息
        left_frame = ttk.Frame(info_frame)
        left_frame.pack(side=LEFT, fill=X, expand=True)
        
        ttk.Label(left_frame, text=f"发票编号: {revenue_id}", font=invoice_window.fonts['normal']).pack(anchor=W, pady=3)
        ttk.Label(left_frame, text=f"日期: {date}", font=invoice_window.fonts['normal']).pack(anchor=W, pady=3)
        ttk.Label(left_frame, text=f"添加人: {added_by}", font=invoice_window.fonts['normal']).pack(anchor=W, pady=3)
        
        # 右侧信息
        right_frame = ttk.Frame(info_frame)
        right_frame.pack(side=RIGHT, fill=X, expand=True)
        
        ttk.Label(right_frame, text=f"员工ID: {emp_id}", font=invoice_window.fonts['normal']).pack(anchor=E, pady=3)
        ttk.Label(right_frame, text=f"员工姓名: {emp_name}", font=invoice_window.fonts['normal']).pack(anchor=E, pady=3)
        
        # 分隔线
        ttk.Separator(content_frame).pack(fill=X, pady=10)
        
        # 项目描述
        desc_frame = ttk.Frame(content_frame)
        desc_frame.pack(fill=X, pady=10)
        
        # 计算合适的wraplength
        wraplength = int(invoice_window.winfo_width() * 0.8) if invoice_window.winfo_width() > 0 else 450
        
        ttk.Label(desc_frame, text="项目描述:", font=invoice_window.fonts['heading']).pack(anchor=W)
        ttk.Label(desc_frame, text=description, font=invoice_window.fonts['normal'], wraplength=wraplength).pack(anchor=W, pady=5)
        
        # 金额
        amount_frame = ttk.Frame(content_frame)
        amount_frame.pack(fill=X, pady=10)
        
        ttk.Label(amount_frame, text="金额:", font=invoice_window.fonts['heading']).pack(side=LEFT)
        ttk.Label(amount_frame, text=f"¥ {amount:.2f}", font=invoice_window.fonts['title'], foreground="red").pack(side=RIGHT)
        
        # 按钮框架
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=X, pady=20)
        
        # 导入发票打印模块
        try:
            from invoice_printer import print_invoice
        except ImportError:
            messagebox.showerror("错误", "未找到invoice_printer模块。请确保该文件存在于d:\\dhm目录下。")
            
        # 打印按钮
        def print_invoice_action():
            print_invoice(revenue_id, date, emp_id, emp_name, amount, description, added_by, invoice_window)
        ttk.Button(button_frame, text="打印", command=print_invoice_action).pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text="关闭", command=invoice_window.destroy).pack(side=RIGHT, padx=10)
    
    def add_revenue(self):
        # 创建添加收入对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加收入", width_percent=0.7, height_percent=0.6)
        
        # 创建日期变量
        date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))

        # 获取所有在职员工
        employees = self.calculator.get_all_employees('active')
        # 查询出职位为"主播"的员工
        anchor_employees = [emp for emp in employees if emp.position == "主播"]

        # 获取当天日期
        current_date = date_var.get()

        # 批量获取主播员工的考勤记录
        attendance_records = {}
        if anchor_employees:
            emp_ids = [emp.emp_id for emp in anchor_employees]
            placeholders = ', '.join(['?' for _ in emp_ids])
            query = f"SELECT emp_id, status FROM attendance WHERE emp_id IN ({placeholders}) AND date=?"
            params = emp_ids + [current_date]
            try:
                results = self.calculator.db_manager.execute_query(query, params, fetch_all=True)
                if results:
                    for row in results:
                        emp_id, status = row
                        attendance_records[emp_id] = status
            except Exception as e:
                logger.error(f"批量获取考勤记录失败: {str(e)}")

        # 查询出当天出勤的主播员工
        present_anchor_employees = []
        for emp in anchor_employees:
            status = attendance_records.get(emp.emp_id)
            # 只保留出勤状态的主播，或者没有考勤记录的主播
            if status is None or status == "present":
                present_anchor_employees.append(emp)
        
        # 查询当天已添加收入的员工ID列表
        revenue_emp_ids = []
        try:
            query = "SELECT emp_id FROM revenue WHERE date=? AND emp_id IS NOT NULL AND emp_id != ''"
            params = [current_date]
            results = self.calculator.db_manager.execute_query(query, params, fetch_all=True)
            if results:
                revenue_emp_ids = [row[0] for row in results]
        except Exception as e:
            logger.error(f"获取当天已添加收入的员工失败: {str(e)}")
        
        # 构建员工列表，排除当天已添加收入的员工
        employee_list = [('', '无关联员工')] + [(emp.emp_id, f"{emp.emp_id} - {emp.name}") for emp in present_anchor_employees if emp.emp_id not in revenue_emp_ids]
        
        # 为标签设置合适的宽度
        label_width = 18 if dialog.winfo_width() < 500 else 20
        
        # 创建表单字段（日期字段已在前面创建）
        
        # 员工选择
        emp_frame = ttk.Frame(dialog.main_frame)
        emp_frame.pack(fill=X, padx=10, pady=8)
        ttk.Label(emp_frame, text="关联员工: ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT)
        emp_var = tk.StringVar(value="")
        emp_combo = ttk.Combobox(emp_frame, textvariable=emp_var, font=dialog.fonts['normal'])
        emp_combo['values'] = [emp[1] for emp in employee_list]
        emp_combo['state'] = 'readonly'
        emp_combo.pack(side=LEFT, fill=X, expand=True)
        
        # 金额
        amount_frame = ttk.Frame(dialog.main_frame)
        amount_frame.pack(fill=X, padx=10, pady=8)
        ttk.Label(amount_frame, text="金额: ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT)
        amount_var = tk.DoubleVar()
        amount_entry = ttk.Entry(amount_frame, textvariable=amount_var, font=dialog.fonts['normal'])
        amount_entry.pack(side=LEFT, fill=X, expand=True)
        
        # 描述文本框使用多行输入
        desc_frame = ttk.Frame(dialog.main_frame)
        desc_frame.pack(fill=BOTH, expand=True, padx=10, pady=8)
        ttk.Label(desc_frame, text="描述: ", width=label_width, font=dialog.fonts['normal']).pack(side=LEFT, anchor=N)
        desc_text = scrolledtext.ScrolledText(desc_frame, wrap=WORD, height=5, font=dialog.fonts['normal'])
        desc_text.pack(side=LEFT, fill=BOTH, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill=X, padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                # 获取输入值
                date = date_var.get().strip()
                amount = amount_var.get()
                description = desc_text.get("1.0", tk.END).strip()
                
                # 获取选中的员工ID
                emp_index = emp_combo.current()
                emp_id = employee_list[emp_index][0] if emp_index >= 0 else ""
                
                # 验证输入
                if not date or not amount:
                    messagebox.showerror("错误", "日期和金额不能为空！")
                    return
                
                # 验证金额
                try:
                    amount = float(amount)
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("错误", "金额必须是正数！")
                    return
                
                # 验证日期格式
                try:
                    datetime.datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                    return
                
                # 添加收入记录
                success, msg = self.calculator.add_revenue(date, emp_id, amount, description)
                if success:
                    messagebox.showinfo("成功", msg)
                    dialog.destroy()
                    self.refresh_revenue_list()
                else:
                    messagebox.showerror("错误", msg)
            except Exception as e:
                messagebox.showerror("错误", f"添加收入失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def init_profit_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.profit_frame)
        # 适配手机屏幕：减少边距
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 添加响应式布局支持
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 顶部控制面板 - 适配手机屏幕：调整布局
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=X, padx=5, pady=5)
        
        # 日期范围选择 - 适配手机屏幕：调整日期选择布局为垂直排列
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(fill="x", pady=(0, 5))
        
        # 起始日期
        start_date_subframe = ttk.Frame(date_frame)
        start_date_subframe.pack(fill="x", pady=(0, 3))
        ttk.Label(start_date_subframe, text="起始日期: ", width=10).pack(side=LEFT)
        self.profit_start_date_var = tk.StringVar(value=(datetime.date.today().replace(day=1)).strftime('%Y-%m-%d'))
        ttk.Entry(start_date_subframe, textvariable=self.profit_start_date_var, width=15).pack(side=LEFT, padx=5)
        
        # 结束日期
        end_date_subframe = ttk.Frame(date_frame)
        end_date_subframe.pack(fill="x", pady=(0, 3))
        ttk.Label(end_date_subframe, text="结束日期: ", width=10).pack(side=LEFT)
        self.profit_end_date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(end_date_subframe, textvariable=self.profit_end_date_var, width=15).pack(side=LEFT, padx=5)
        
        # 计算类型和按钮 - 适配手机屏幕：调整单选按钮和计算按钮布局
        calc_type_subframe = ttk.Frame(date_frame)
        calc_type_subframe.pack(fill="x")
        
        self.salary_query_type = tk.StringVar(value="month")
        ttk.Radiobutton(calc_type_subframe, text="按月计算", variable=self.salary_query_type, value="month").pack(side=LEFT, padx=5)
        ttk.Radiobutton(calc_type_subframe, text="按支付日期", variable=self.salary_query_type, value="payment_date").pack(side=LEFT, padx=5)
        
        # 计算利润按钮 - 适配手机屏幕：调整按钮宽度
        ttk.Button(calc_type_subframe, text="计算利润", command=self.calculate_and_display_profit, width=10).pack(side=LEFT, padx=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="利润计算结果")
        result_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建结果标签 - 适配手机屏幕：调整字体大小和包装长度
        self.profit_result_var = tk.StringVar()
        self.profit_result_var.set("请选择日期范围并点击'计算利润'按钮")
        ttk.Label(result_frame, textvariable=self.profit_result_var, font=("SimHei", 11), wraplength=400).pack(padx=10, pady=10)
        
        # 创建图表 - 适配手机屏幕：调整图表大小
        chart_frame = ttk.LabelFrame(main_frame, text="收支图表")
        chart_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 适配手机屏幕：调整图表尺寸以适应小屏幕
        self.fig3, self.ax3 = plt.subplots(figsize=(5, 3), dpi=100)
        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=chart_frame)
        self.canvas3.get_tk_widget().pack(fill=BOTH, expand=True)
    
    def calculate_and_display_profit(self):
        # 获取日期范围
        start_date = self.profit_start_date_var.get()
        end_date = self.profit_end_date_var.get()
        
        try:
            # 验证日期格式
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
            return
        
        try:
            # 获取工资查询类型
            salary_query_type = self.salary_query_type.get()
            
            # 计算利润
            profit_data = self.calculator.calculate_profit(start_date, end_date, salary_query_type)
            
            # 检查是否有错误
            if isinstance(profit_data, tuple) and profit_data[0] is False:
                messagebox.showerror("错误", profit_data[1])
                return
            
            # 更新结果标签
            result_text = f"日期范围: {start_date} 至 {end_date}\n"
            result_text += f"总收入: {profit_data['total_revenue']:.2f} 元\n"
            result_text += f"总工资支出: {profit_data['total_salary']:.2f} 元\n"
            result_text += f"其他支出: {profit_data['total_other_expenses']:.2f} 元\n"
            result_text += f"总支出: {profit_data['total_expenses']:.2f} 元\n"
            result_text += f"利润: {profit_data['profit']:.2f} 元\n"
            result_text += f"工资计算方式: {'按月计算' if self.salary_query_type.get() == 'month' else '按支付日期'}"
            
            # 如果没有工资记录，显示提示
            if profit_data['total_salary'] == 0:
                result_text += "\n\n提示: 当前没有找到工资记录。请先在工资管理中生成工资表。"
            
            self.profit_result_var.set(result_text)
            
            # 更新图表
            self.ax3.clear()
            
            # 绘制柱状图
            labels = ['总收入', '总工资支出', '其他支出', '利润']
            values = [profit_data['total_revenue'], profit_data['total_salary'], profit_data['total_other_expenses'], profit_data['profit']]
            colors = ['green', 'red', 'orange', 'blue']
            
            self.ax3.bar(labels, values, color=colors)
            self.ax3.set_title(f"{start_date} 至 {end_date} 收支情况")
            self.ax3.set_ylabel("金额 (元)")
            
            # 添加数据标签
            for i, v in enumerate(values):
                self.ax3.text(i, v, f"{v:.2f}", ha='center', va='bottom')
            
            self.fig3.tight_layout()
            self.canvas3.draw()
        except Exception as e:
            messagebox.showerror("错误", f"计算利润失败：{str(e)}")
    
    def setup_salary_reminder(self):
        # 设置工资发放提醒功能
        def check_salary_date():
            # 使用网络时间
            today = get_network_time().date()
            
            # 检查是否是14号（提前一天提醒）
            if today.day == 14:
                messagebox.showinfo("工资发放提醒", "明天是15号，该准备发放工资了！")
            # 检查是否是15号（当天提醒）
            elif today.day == 15:
                messagebox.showinfo("工资发放提醒", "今天是15号，记得发放工资！")
            # 检查是否是16号（延后一天提醒）
            elif today.day == 16:
                messagebox.showinfo("工资发放提醒", "昨天是15号，工资发放了吗？")
            
            # 24小时后再次检查
            self.root.after(24 * 60 * 60 * 1000, check_salary_date)
        
        # 立即检查一次
        check_salary_date()
    
    # 修改考勤管理功能，限制普通操作员只能修改当天的考勤记录
    def init_attendance_frame(self):
        # 尝试导入tkcalendar库
        try:
            from tkcalendar import DateEntry
            has_calendar = True
        except ImportError:
            has_calendar = False
            logger.warning("tkcalendar库未安装，无法使用日期选择器功能。")
        
        # 创建主框架
        main_frame = ttk.Frame(self.attendance_frame)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=X, padx=5, pady=5)
        
        # 日期选择 - 使用下拉菜单
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(side=LEFT, padx=5)
        
        ttk.Label(date_frame, text="日期: ").pack(side=LEFT)
        
        # 获取当前日期
        today = get_network_time().date()
        current_year = today.year
        current_month = today.month
        current_day = today.day
        
        # 创建年份下拉菜单
        self.year_var = tk.StringVar(value=str(current_year))
        years = [str(year) for year in range(current_year - 5, current_year + 5)]
        year_combo = ttk.Combobox(date_frame, textvariable=self.year_var, values=years, width=5, state='readonly')
        year_combo.pack(side=LEFT, padx=2)
        
        # 创建月份下拉菜单
        self.month_var = tk.StringVar(value=str(current_month).zfill(2))
        months = [str(month).zfill(2) for month in range(1, 13)]
        month_combo = ttk.Combobox(date_frame, textvariable=self.month_var, values=months, width=3, state='readonly')
        month_combo.pack(side=LEFT, padx=2)
        
        # 创建日期下拉菜单
        self.day_var = tk.StringVar(value=str(current_day).zfill(2))
        # 初始化日期下拉菜单（默认31天，后面会根据月份更新）
        days = [str(day).zfill(2) for day in range(1, 32)]
        self.day_combo = ttk.Combobox(date_frame, textvariable=self.day_var, values=days, width=3, state='readonly')
        self.day_combo.pack(side=LEFT, padx=2)
        
        # 如果是普通操作员，禁用日期修改
        if self.user_role != 'admin':
            year_combo.config(state='disabled')
            month_combo.config(state='disabled')
            self.day_combo.config(state='disabled')
        
        # 更新日期下拉菜单的逻辑
        def update_days(*args):
            try:
                year = int(self.year_var.get())
                month = int(self.month_var.get())
                # 获取当月天数
                days_in_month = calendar.monthrange(year, month)[1]
                # 更新日期下拉菜单
                days = [str(day).zfill(2) for day in range(1, days_in_month + 1)]
                self.day_combo['values'] = days
                # 如果当前选择的日期超过了当月天数，则重置为1
                current_day = int(self.day_var.get())
                if current_day > days_in_month:
                    self.day_var.set('01')
            except ValueError:
                pass
        
        # 绑定年份和月份变化事件
        self.year_var.trace('w', update_days)
        self.month_var.trace('w', update_days)
        
        # 初始化日期组合
        self.attendance_date_var = tk.StringVar(value=f"{current_year}-{str(current_month).zfill(2)}-{str(current_day).zfill(2)}")
        
        # 绑定日期变化事件，确保日期唯一性
        def check_date_uniqueness(*args):
            selected_date = f"{self.year_var.get()}-{self.month_var.get()}-{self.day_var.get()}"
            self.attendance_date_var.set(selected_date)
            
            # 检查日期唯一性（查询数据库中是否已存在该日期的考勤记录）
            try:
                result = self.calculator.db_manager.execute_query(
                    "SELECT COUNT(*) FROM attendance WHERE date=?",
                    (selected_date,),
                    fetch_one=True
                )
                if result and result[0] > 0:
                    messagebox.showwarning("警告", f"{selected_date} 的考勤记录已存在！\n请选择其他日期或删除已存在的记录。")
            except Exception as e:
                logger.error(f"检查日期唯一性失败: {str(e)}")
        
        # 绑定日期组件变化事件
        self.year_var.trace('w', check_date_uniqueness)
        self.month_var.trace('w', check_date_uniqueness)
        self.day_var.trace('w', check_date_uniqueness)
        
        # 批量设置按钮
        ttk.Button(control_frame, text="批量设置出勤", command=self.batch_set_attendance).pack(side=LEFT, padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新考勤", command=self.refresh_attendance_list).pack(side=LEFT, padx=5)
        
        # 部门查询
        dept_frame = ttk.Frame(control_frame)
        dept_frame.pack(side=RIGHT, padx=5)
        
        ttk.Label(dept_frame, text="部门: ").pack(side=LEFT)
        self.dept_filter_var = tk.StringVar(value="all")
        # 这里应该动态获取部门列表，但为了简化，先使用静态列表
        dept_combo = ttk.Combobox(dept_frame, textvariable=self.dept_filter_var, values=["all"], width=15)
        dept_combo.pack(side=LEFT, padx=5)
        ttk.Button(dept_frame, text="查询", command=self.refresh_attendance_list).pack(side=LEFT, padx=5)
        
        # 考勤列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("emp_id", "name", "department", "position", "status", "note")
        self.attendance_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.attendance_tree.heading("emp_id", text="员工ID")
        self.attendance_tree.heading("name", text="姓名")
        self.attendance_tree.heading("department", text="部门")
        self.attendance_tree.heading("position", text="职位")
        self.attendance_tree.heading("status", text="状态")
        self.attendance_tree.heading("note", text="备注")
        
        # 设置列宽
        self.attendance_tree.column("emp_id", width=80)
        self.attendance_tree.column("name", width=100)
        self.attendance_tree.column("department", width=120)
        self.attendance_tree.column("position", width=120)
        self.attendance_tree.column("status", width=80)
        self.attendance_tree.column("note", width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.attendance_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定双击事件，编辑考勤
        self.attendance_tree.bind("<Double-1>", lambda event: self.edit_attendance())
        
        # 刷新考勤列表
        self.refresh_attendance_list()

if __name__ == "__main__":
    # 启动应用
    main()