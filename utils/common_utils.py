import sqlite3
import datetime
import re
import tkinter as tk
from tkinter import messagebox
import logging
import sqlite3

# 配置日志
# 设置文件处理器使用UTF-8编码
file_handler = logging.FileHandler('salary_system.log', encoding='utf-8')
# 设置控制台处理器使用UTF-8编码
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        stream_handler
    ]
)
logger = logging.getLogger('salary_system')

class DatabaseManager:
    """数据库管理类，封装通用的数据库操作"""
    def __init__(self, db_path):
        self.db_path = db_path

    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            # 设置连接的编码为UTF-8
            conn.text_factory = lambda x: str(x, 'utf-8', 'ignore')
            return conn
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            messagebox.showerror("错误", f"数据库连接失败: {str(e)}")
            return None

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """执行SQL查询
        
        在使用本地时间时，只允许读操作（SELECT），限制写操作（INSERT、UPDATE、DELETE）
        """
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            
            # 检查是否使用本地时间，并且操作类型是写操作
            query_upper = query.strip().upper()
            is_write_operation = query_upper.startswith('INSERT') or \
                                query_upper.startswith('UPDATE') or \
                                query_upper.startswith('DELETE') or \
                                query_upper.startswith('CREATE') or \
                                query_upper.startswith('DROP') or \
                                query_upper.startswith('ALTER')
            
            # 直接访问全局变量
            global using_local_time
            if using_local_time and is_write_operation:
                logger.warning(f"使用本地时间时禁止执行写操作: {query[:100]}...")
                messagebox.showwarning("警告", "当前使用的是本地时间，为了数据安全，禁止执行数据库写操作！\n请检查网络连接后重试。")
                return None

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            conn.commit()

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return True
        except sqlite3.Error as e:
            logger.error(f"查询执行失败: {str(e)}")
            messagebox.showerror("错误", f"数据库操作失败: {str(e)}")
            return None
        finally:
            conn.close()

class Validator:
    """数据验证类"""
    @staticmethod
    def is_valid_emp_id(emp_id):
        """验证员工ID格式"""
        pattern = r'^EMP\d{14}$'
        return bool(re.match(pattern, emp_id))

    @staticmethod
    def is_valid_name(name):
        """验证姓名"""
        return bool(name and len(name) <= 50 and re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', name))

    @staticmethod
    def is_valid_date(date_str, format='%Y-%m-%d'):
        """验证日期格式"""
        try:
            datetime.datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_salary(salary):
        """验证工资是否为正数"""
        try:
            salary = float(salary)
            return salary >= 0
        except ValueError:
            return False

    @staticmethod
    def is_valid_phone(phone):
        """验证手机号格式"""
        if not phone:
            return True
        return bool(re.match(r'^1[3-9]\d{9}$', phone))

    @staticmethod
    def is_valid_month_format(month_str):
        """验证月份格式是否为YYYY-MM"""
        pattern = r'^\d{4}-\d{2}$'
        if not re.match(pattern, month_str):
            return False
        try:
            year, month = map(int, month_str.split('-'))
            return 1 <= month <= 12
        except ValueError:
            return False

def generate_emp_id():
    """生成唯一员工ID"""
    return f"EMP{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

# 全局变量，用于标记是否使用的是本地时间
using_local_time = False

def get_network_time():
    """获取网络时间，若失败则返回本地时间，并设置using_local_time标志"""
    global using_local_time
    try:
        # 尝试从多个NTP服务器获取时间，增加成功率
        try:
            import ntplib
            ntp_servers = ['pool.ntp.org', 'time.nist.gov', 'ntp.aliyun.com']
            
            for server in ntp_servers:
                try:
                    client = ntplib.NTPClient()
                    response = client.request(server, timeout=2)
                    # 计算网络时间
                    ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
                    using_local_time = False
                    logger.info(f"成功获取网络时间: {ntp_time} from {server}")
                    return ntp_time
                except:
                    continue
            
            # 所有NTP服务器都失败
            local_time = datetime.datetime.now()
            using_local_time = True
            logger.warning(f"无法获取网络时间，使用本地时间: {local_time}")
            return local_time
        except ImportError:
            # ntplib库未安装
            local_time = datetime.datetime.now()
            using_local_time = True
            logger.warning(f"ntplib库未安装，使用本地时间: {local_time}")
            return local_time
    except Exception as e:
        # 其他错误
        local_time = datetime.datetime.now()
        using_local_time = True
        logger.error(f"获取网络时间异常: {str(e)}, 使用本地时间: {local_time}")
        return local_time

def is_using_local_time():
    """检查当前是否使用的是本地时间"""
    global using_local_time
    return using_local_time

# 添加一个函数来手动切换到本地时间（用于测试）
def force_use_local_time():
    """强制使用本地时间（用于测试）"""
    global using_local_time
    using_local_time = True
    logger.info("已强制切换到本地时间模式")
    return using_local_time

# 添加一个函数来重置时间模式
def reset_time_mode():
    """重置时间模式，重新尝试获取网络时间"""
    global using_local_time
    using_local_time = False
    logger.info("已重置时间模式，将重新尝试获取网络时间")
    # 立即尝试获取网络时间
    get_network_time()
    # 检查最新状态
    logger.info(f"重置后时间模式状态: {'本地时间' if using_local_time else '网络时间'}")
    return using_local_time

# 导出常用函数和类
__all__ = [
    'DatabaseManager',
    'Validator',
    'generate_emp_id',
    'get_network_time',
    'is_using_local_time',
    'force_use_local_time',
    'reset_time_mode',
    'logger'
]