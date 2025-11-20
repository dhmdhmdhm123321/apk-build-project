# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime
import os

# 导入自适应对话框类
from salary_calculator import AdaptiveDialog

class InventoryManager:
    def __init__(self, db_path, root, notebook, user_role, current_user=None):
        self.db_path = db_path
        self.root = root
        self.notebook = notebook
        self.user_role = user_role
        self.current_user = current_user
        
        # 创建进销存标签页
        self.inventory_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.inventory_frame, text="进销存管理")
        
        # 初始化数据库表
        self.init_database()
        
        # 如果不是管理员，隐藏进销存管理标签页
        if self.user_role != 'admin':
            self.notebook.hide(self.inventory_frame)
        else:
            self.init_inventory_frame()
    
    def init_database(self):
        """初始化进销存数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建产品表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT,
            purchase_price REAL,
            selling_price REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建库存表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建进货记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total_amount REAL,
            purchase_date TIMESTAMP,
            supplier TEXT,
            created_by TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建销售记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total_amount REAL,
            sale_date TIMESTAMP,
            customer TEXT,
            created_by TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建客户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_code TEXT UNIQUE NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_inventory_frame(self):
        """初始化进销存管理界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.inventory_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建标签页切换
        self.inventory_notebook = ttk.Notebook(main_frame)
        self.inventory_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建各个子标签页
        self.product_frame = ttk.Frame(self.inventory_notebook)
        self.purchase_frame = ttk.Frame(self.inventory_notebook)
        self.sale_frame = ttk.Frame(self.inventory_notebook)
        self.stock_frame = ttk.Frame(self.inventory_notebook)
        self.customer_frame = ttk.Frame(self.inventory_notebook)  # 客户管理标签页
        self.profit_frame = ttk.Frame(self.inventory_notebook)    # 利润报表标签页
        
        # 添加子标签页
        self.inventory_notebook.add(self.product_frame, text="产品管理")
        self.inventory_notebook.add(self.purchase_frame, text="进货管理")
        self.inventory_notebook.add(self.sale_frame, text="销售管理")
        self.inventory_notebook.add(self.stock_frame, text="库存查询")
        self.inventory_notebook.add(self.customer_frame, text="客户管理")
        self.inventory_notebook.add(self.profit_frame, text="利润报表")
        
        # 初始化各个子页面
        self.init_product_frame()
        self.init_purchase_frame()
        self.init_sale_frame()
        self.init_stock_frame()
        self.init_customer_frame()  # 初始化客户管理页面
        self.init_profit_frame()    # 初始化利润报表页面
    
    def init_product_frame(self):
        """初始化产品管理页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.product_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 添加产品按钮
        ttk.Button(control_frame, text="添加产品", command=self.add_product).pack(side="left", padx=5)
        
        # 修改产品按钮
        ttk.Button(control_frame, text="修改产品", command=self.edit_product).pack(side="left", padx=5)
        
        # 删除产品按钮
        ttk.Button(control_frame, text="删除产品", command=self.delete_product).pack(side="left", padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_product_list).pack(side="left", padx=5)
        
        # 产品列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("product_code", "name", "category", "unit", "purchase_price", "selling_price", "description")
        self.product_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.product_tree.heading("product_code", text="产品编码")
        self.product_tree.heading("name", text="产品名称")
        self.product_tree.heading("category", text="类别")
        self.product_tree.heading("unit", text="单位")
        self.product_tree.heading("purchase_price", text="进价")
        self.product_tree.heading("selling_price", text="售价")
        self.product_tree.heading("description", text="描述")
        
        # 设置列宽
        self.product_tree.column("product_code", width=120)
        self.product_tree.column("name", width=150)
        self.product_tree.column("category", width=100)
        self.product_tree.column("unit", width=80)
        self.product_tree.column("purchase_price", width=80, anchor="center")
        self.product_tree.column("selling_price", width=80, anchor="center")
        self.product_tree.column("description", width=300)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.product_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定双击事件，编辑产品
        self.product_tree.bind("<Double-1>", lambda event: self.edit_product())
        
        # 刷新产品列表
        self.refresh_product_list()
    
    def refresh_product_list(self):
        """刷新产品列表"""
        # 清空Treeview
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # 连接数据库获取产品列表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""SELECT id, product_code, name, category, unit, purchase_price, selling_price, description 
                          FROM products 
                          ORDER BY name""")
        products = cursor.fetchall()
        conn.close()
        
        # 添加到Treeview，将ID作为item的iid，而不是显示在列中
        for product in products:
            id, product_code, name, category, unit, purchase_price, selling_price, description = product
            self.product_tree.insert("", "end", iid=id,
                values=(product_code, name, category, unit, purchase_price, selling_price, description))
    
    def add_product(self):
        """添加产品"""
        # 创建添加产品对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加产品", width_percent=0.7, height_percent=0.7)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 15
        
        # 产品编码
        code_frame = ttk.Frame(dialog.main_frame)
        code_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(code_frame, text="产品编码: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        code_var = ttk.Entry(code_frame, state="disabled", font=dialog.fonts['normal'])
        code_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 产品名称
        name_frame = ttk.Frame(dialog.main_frame)
        name_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(name_frame, text="产品名称: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        name_var = ttk.Entry(name_frame, font=dialog.fonts['normal'])
        name_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 自动生成产品编码的函数
        def generate_product_code(event=None):
            name = name_var.get().strip()
            if not name:
                code_var.config(state="normal")
                code_var.delete(0, tk.END)
                code_var.config(state="disabled")
                return
            
            # 导入pypinyin库用于获取汉字拼音首字母
            import pypinyin
            
            # 获取产品名称所有中文字符的拼音首字母大写
            def get_pinyin首字母(text):
                pinyin首字母 = ''
                # 汉字拼音首字母映射表（常用字）
                pinyin_map = {
                    # 基础汉字
                    '一':'Y', '乙':'Y', '二':'E', '十':'S', '丁':'D', '厂':'C', '七':'Q', '卜':'B', '人':'R', '入':'R', 
                    '八':'B', '九':'J', '几':'J', '儿':'E', '了':'L', '力':'L', '乃':'N', '刀':'D', '又':'Y',
                    # 常用汉字
                    '大':'D', '小':'X', '多':'D', '少':'S', '上':'S', '下':'X', '左':'Z', '右':'Y', '前':'Q', '后':'H', 
                    '中':'Z', '天':'T', '地':'D', '日':'R', '月':'Y', '水':'S', '火':'H', '风':'F', '雨':'Y', '雷':'L', 
                    '电':'D', '金':'J', '木':'M', '土':'T', '东':'D', '南':'N', '西':'X', '北':'B', '春':'C', '夏':'X', 
                    '秋':'Q', '冬':'D', '子':'Z', '丑':'C', '寅':'Y', '卯':'M', '辰':'C', '巳':'S', '午':'W', '未':'W', 
                    '申':'S', '酉':'Y', '戌':'X', '亥':'H', '鼠':'S', '牛':'N', '虎':'H', '兔':'T', '龙':'L', '蛇':'S', 
                    '马':'M', '羊':'Y', '猴':'H', '鸡':'J', '狗':'G', '猪':'Z',
                    # 数字
                    '壹':'Y', '贰':'E', '叁':'S', '肆':'S', '伍':'W', '陆':'L', '柒':'Q', '捌':'B', '玖':'J', '拾':'S',
                    # 常见物品名称
                    '桌':'Z', '椅':'Y', '书':'S', '笔':'B', '纸':'Z', '杯':'B', '盘':'P', '碗':'W', '刀':'D', '叉':'C',
                    '打':'D', '印':'Y', '机':'J',
                    '筷':'K', '勺':'S', '瓶':'P', '箱':'X', '袋':'D', '盒':'H', '包':'B', '柜':'G', '床':'C', '灯':'D',
                    '门':'M', '窗':'C', '墙':'Q', '地':'D', '天':'T', '车':'C', '船':'C', '机':'J', '手':'S', '脚':'J',
                    '头':'T', '身':'S', '心':'X', '眼':'Y', '耳':'E', '口':'K', '鼻':'B', '舌':'S', '指':'Z', '掌':'Z',
                    '杯':'B', '壶':'H', '锅':'G', '铲':'C', '勺':'S', '盘':'P', '碗':'W', '筷':'K', '刀':'D', '叉':'C',
                    '纸':'Z', '笔':'B', '墨':'M', '砚':'Y', '书':'S', '本':'B', '尺':'C', '规':'G', '盒':'H', '包':'B',
                    '箱':'X', '袋':'D', '瓶':'P', '罐':'G', '桶':'T', '坛':'T', '缸':'G', '盆':'P', '碗':'W', '杯':'B',
                    '床':'C', '桌':'Z', '椅':'Y', '凳':'D', '柜':'G', '架':'J', '箱':'X', '盒':'H', '包':'B', '袋':'D',
                    '衣':'Y', '裤':'K', '鞋':'X', '帽':'M', '袜':'W', '巾':'J', '被':'B', '褥':'R', '枕':'Z', '毯':'T',
                    '灯':'D', '泡':'P', '管':'G', '座':'Z', '架':'J', '台':'T', '扇':'S', '热':'R', '冷':'L', '暖':'N',
                    '锅':'G', '铲':'C', '勺':'S', '刀':'D', '叉':'C', '筷':'K', '碗':'W', '盘':'P', '杯':'B', '壶':'H',
                    '米':'M', '面':'M', '油':'Y', '盐':'Y', '酱':'J', '醋':'C', '茶':'C', '酒':'J', '糖':'T', '果':'G',
                    '肉':'R', '鱼':'Y', '菜':'C', '蛋':'D', '奶':'N', '豆':'D', '米':'M', '面':'M', '粮':'L', '油':'Y',
                    '水':'S', '电':'D', '气':'Q', '煤':'M', '柴':'C', '火':'H', '光':'G', '热':'R', '冷':'L', '风':'F',
                    '雨':'Y', '雪':'X', '雷':'L', '电':'D', '霜':'S', '露':'L', '云':'Y', '雾':'W', '冰':'B', '霜':'S',
                    # 品牌名称常见字
                    '华':'H', '美':'M', '丽':'L', '雅':'Y', '佳':'J', '优':'Y', '良':'L', '好':'H', '精':'J', '品':'P',
                    '高':'G', '端':'D', '新':'X', '奇':'Q', '特':'T', '强':'Q', '大':'D', '小':'X', '多':'D', '少':'S',
                    '长':'C', '短':'D', '宽':'K', '窄':'Z', '厚':'H', '薄':'B', '重':'Z', '轻':'Q', '快':'K', '慢':'M',
                    '上':'S', '下':'X', '左':'Z', '右':'Y', '前':'Q', '后':'H', '里':'L', '外':'W', '东':'D', '南':'N',
                    '西':'X', '北':'B', '中':'Z', '内':'N', '外':'W', '里':'L', '表':'B', '正':'Z', '反':'F', '方':'F',
                    '圆':'Y', '直':'Z', '弯':'W', '高':'G', '低':'D', '矮':'A', '胖':'P', '瘦':'S', '美':'M', '丑':'C',
                    '好':'H', '坏':'H', '优':'Y', '劣':'L', '善':'S', '恶':'E', '是':'S', '非':'F', '对':'D', '错':'C',
                    '真':'Z', '假':'J', '实':'S', '虚':'X', '有':'Y', '无':'W', '多':'D', '少':'S', '大':'D', '小':'X',
                    '长':'C', '短':'D', '粗':'C', '细':'X', '厚':'H', '薄':'B', '深':'S', '浅':'Q', '远':'Y', '近':'J',
                    '快':'K', '慢':'M', '强':'Q', '弱':'R', '硬':'Y', '软':'R', '冷':'L', '热':'R', '干':'G', '湿':'S',
                    '饱':'B', '饿':'E', '渴':'K', '困':'K', '醒':'X', '睡':'S', '生':'S', '死':'S', '病':'B', '痛':'T',
                    '康':'K', '乐':'L', '悲':'B', '喜':'X', '怒':'N', '哀':'A', '惧':'J', '爱':'A', '恨':'H', '情':'Q',
                    '仇':'C', '恩':'E', '怨':'Y', '愁':'C', '苦':'K', '甜':'T', '酸':'S', '辣':'L', '咸':'X', '淡':'D',
                    '香':'X', '臭':'C', '浓':'N', '淡':'D', '清':'Q', '浊':'Z', '明':'M', '暗':'A', '亮':'L', '黑':'H',
                    '白':'B', '红':'H', '黄':'H', '绿':'L', '蓝':'L', '紫':'Z', '青':'Q', '灰':'H', '粉':'F', '橙':'C',
                    '金':'J', '银':'Y', '铜':'T', '铁':'T', '铝':'L', '锡':'X', '铅':'Q', '锌':'X', '镁':'M', '钛':'T'
                }
                
                for char in text:
                    if '\u4e00' <= char <= '\u9fff':  # 中文字符
                        # 使用pypinyin获取拼音首字母，并转换为大写
                        # errors='ignore'表示忽略无法转换的字符
                        # strict=False表示更宽松的拼音匹配
                        pinyin = pypinyin.lazy_pinyin(char, errors='ignore', strict=False)
                        if pinyin and pinyin[0]:
                            pinyin首字母 += pinyin[0][0].upper()
                        else:
                            pinyin首字母 += 'Z'  # 默认使用Z
                    else:
                        # 非中文字符直接转为大写
                        pinyin首字母 += char.upper()
                return pinyin首字母
            
            # 提取产品名称中所有中文的拼音首字母大写
            prefix = get_pinyin首字母(name)
            
            # 获取当前时间，格式为年月日时分秒
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            
            # 组合生成产品编码
            product_code = prefix + timestamp
            
            # 更新产品编码输入框
            code_var.config(state="normal")
            code_var.delete(0, tk.END)
            code_var.insert(0, product_code)
            code_var.config(state="disabled")
        
        # 绑定产品名称输入事件，自动生成产品编码
        name_var.bind("<KeyRelease>", generate_product_code)
        
        # 类别
        category_frame = ttk.Frame(dialog.main_frame)
        category_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(category_frame, text="类别: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        category_var = ttk.Combobox(category_frame, font=dialog.fonts['normal'])
        category_var['validate'] = 'key'
        category_var['validatecommand'] = (category_var.register(lambda s: True), '%P')
        
        # 获取所有产品类别及其使用次数，并按使用次数排序
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT category, COUNT(*) as count FROM products GROUP BY category ORDER BY count DESC")
        category_counts = cursor.fetchall()
        conn.close()
        
        # 创建类别列表，如果没有任何类别，则使用默认类别
        default_categories = ["电子产品", "办公用品", "食品饮料", "服装鞋帽", "家居用品", "其他"]
        
        if category_counts:
            # 优先显示使用过的类别
            used_categories = [category[0] for category in category_counts]
            # 添加未使用过的默认类别
            all_categories = used_categories + [cat for cat in default_categories if cat not in used_categories]
        else:
            all_categories = default_categories
        
        category_var['values'] = all_categories
        if all_categories:
            category_var.current(0)
        
        category_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 单位
        unit_frame = ttk.Frame(dialog.main_frame)
        unit_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(unit_frame, text="单位: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        unit_var = ttk.Combobox(unit_frame, font=dialog.fonts['normal'])
        unit_var['validate'] = 'key'
        unit_var['validatecommand'] = (unit_var.register(lambda s: True), '%P')
        
        # 获取所有产品单位及其使用次数，并按使用次数排序
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT unit, COUNT(*) as count FROM products GROUP BY unit ORDER BY count DESC")
        unit_counts = cursor.fetchall()
        conn.close()
        
        # 创建单位列表，如果没有任何单位，则使用默认单位
        default_units = ["个", "件", "箱", "袋", "瓶", "盒", "kg", "g", "其他"]
        
        if unit_counts:
            # 优先显示使用过的单位
            used_units = [unit[0] for unit in unit_counts]
            # 添加未使用过的默认单位
            all_units = used_units + [u for u in default_units if u not in used_units]
        else:
            all_units = default_units
        
        unit_var['values'] = all_units
        if all_units:
            unit_var.current(0)
        
        unit_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 进价
        purchase_price_frame = ttk.Frame(dialog.main_frame)
        purchase_price_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(purchase_price_frame, text="进价: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        purchase_price_var = ttk.Entry(purchase_price_frame, font=dialog.fonts['normal'])
        purchase_price_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 售价
        selling_price_frame = ttk.Frame(dialog.main_frame)
        selling_price_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(selling_price_frame, text="售价: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        selling_price_var = ttk.Entry(selling_price_frame, font=dialog.fonts['normal'])
        selling_price_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(dialog.main_frame)
        desc_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(desc_frame, text="描述: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        desc_var = ttk.Entry(desc_frame, font=dialog.fonts['normal'])
        desc_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 如果有总金额，显示出来
        # total_amount在添加产品功能中默认不存在，这里留空
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                product_code = code_var.get().strip()
                name = name_var.get().strip()
                category = category_var.get()
                unit = unit_var.get()
                purchase_price = float(purchase_price_var.get().strip()) if purchase_price_var.get().strip() else 0
                selling_price = float(selling_price_var.get().strip()) if selling_price_var.get().strip() else 0
                description = desc_var.get().strip()
                
                # 自动添加操作者信息
                if self.current_user and hasattr(self.current_user, 'username'):
                    operator_info = f"[操作者: {self.current_user.username}]"
                elif self.current_user and isinstance(self.current_user, dict) and 'username' in self.current_user:
                    operator_info = f"[操作者: {self.current_user['username']}]"
                else:
                    operator_info = "[操作者: 未知]"
                
                # 在描述末尾添加操作者信息
                if description:
                    description = f"{description} {operator_info}"
                else:
                    description = operator_info
                
                # 验证输入
                if not product_code:
                    messagebox.showerror("错误", "请先输入产品名称，系统会自动生成产品编码！")
                    return
                
                if not name:
                    messagebox.showerror("错误", "产品名称不能为空！")
                    return
                
                if purchase_price < 0 or selling_price < 0:
                    messagebox.showerror("错误", "价格不能为负数！")
                    return
                
                # 连接数据库添加产品
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                try:
                    # 检查产品名称是否已存在
                    cursor.execute("SELECT COUNT(*) FROM products WHERE name = ?", (name,))
                    exists = cursor.fetchone()[0] > 0
                    
                    if exists:
                        messagebox.showerror("错误", f"产品 '{name}' 已存在！")
                        conn.close()
                        return
                    
                    # 检查并更新类别下拉列表
                    # 再次获取所有产品类别及其使用次数，并按使用次数排序
                    cursor.execute("SELECT category, COUNT(*) as count FROM products GROUP BY category ORDER BY count DESC")
                    category_counts = cursor.fetchall()
                    
                    # 创建新的类别列表
                    if category_counts:
                        # 优先显示使用过的类别
                        used_categories = [category[0] for category in category_counts]
                        # 添加未使用过的默认类别和用户新输入的类别
                        all_categories = used_categories + [cat for cat in default_categories if cat not in used_categories]
                        # 如果用户输入的类别不在现有类别列表中，添加到列表
                        if category not in all_categories:
                            all_categories.append(category)
                    else:
                        all_categories = default_categories
                        if category not in all_categories:
                            all_categories.append(category)
                    
                    # 更新下拉列表
                    category_var['values'] = all_categories
                    
                    # 检查并更新单位下拉列表
                    # 再次获取所有产品单位及其使用次数，并按使用次数排序
                    cursor.execute("SELECT unit, COUNT(*) as count FROM products GROUP BY unit ORDER BY count DESC")
                    unit_counts = cursor.fetchall()
                    
                    # 创建新的单位列表
                    if unit_counts:
                        # 优先显示使用过的单位
                        used_units = [unit[0] for unit in unit_counts]
                        # 添加未使用过的默认单位和用户新输入的单位
                        all_units = used_units + [u for u in default_units if u not in used_units]
                        # 如果用户输入的单位不在现有单位列表中，添加到列表
                        if unit not in all_units:
                            all_units.append(unit)
                    else:
                        all_units = default_units
                        if unit not in all_units:
                            all_units.append(unit)
                    
                    # 更新下拉列表
                    unit_var['values'] = all_units
                    
                    # 添加产品
                    cursor.execute(
                        "INSERT INTO products (product_code, name, category, unit, purchase_price, selling_price, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (product_code, name, category, unit, purchase_price, selling_price, description)
                    )
                    
                    # 获取新添加的产品ID
                    product_id = cursor.lastrowid
                    
                    # 初始化库存
                    cursor.execute("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)", (product_id, 0))
                    
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("成功", "产品添加成功！")
                    dialog.destroy()
                    self.refresh_product_list()
                    self.refresh_stock_list()
                except sqlite3.IntegrityError:
                    conn.close()
                    messagebox.showerror("错误", "产品编码已存在！")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字！")
            except Exception as e:
                messagebox.showerror("错误", f"添加产品失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10)
    
    def edit_product(self):
        """修改产品"""
        # 获取选中的产品
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个产品！")
            return
        
        # 获取产品ID (从item的iid中获取)
        product_id = selected_item[0]
        
        # 连接数据库获取产品详细信息
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT product_code, name, category, unit, purchase_price, selling_price, description FROM products WHERE id=?",
            (product_id,)
        )
        product_info = cursor.fetchone()
        conn.close()
        
        if not product_info:
            messagebox.showerror("错误", "找不到指定的产品信息！")
            return
        
        product_code, name, category, unit, purchase_price, selling_price, description = product_info
        
        # 创建修改产品对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "修改产品", width_percent=0.7, height_percent=0.6)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 15
        
        # 产品编码
        code_frame = ttk.Frame(dialog.main_frame)
        code_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(code_frame, text="产品编码: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        code_var = ttk.Entry(code_frame, state="disabled", font=dialog.fonts['normal'])
        code_var.insert(0, product_code)
        code_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 产品名称
        name_frame = ttk.Frame(dialog.main_frame)
        name_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(name_frame, text="产品名称: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        name_var = ttk.Entry(name_frame, font=dialog.fonts['normal'])
        name_var.insert(0, name)
        name_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 类别
        category_frame = ttk.Frame(dialog.main_frame)
        category_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(category_frame, text="类别: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        
        # 从数据库获取类别使用次数并排序
        conn_category = sqlite3.connect(self.db_path)
        cursor_category = conn_category.cursor()
        cursor_category.execute("SELECT category, COUNT(*) as count FROM products GROUP BY category ORDER BY count DESC")
        category_results = cursor_category.fetchall()
        conn_category.close()
        
        # 创建类别下拉列表，包含已使用的类别和默认类别
        default_categories = ["电子产品", "办公用品", "食品饮料", "服装鞋帽", "家居用品", "其他"]
        category_list = [item[0] for item in category_results]
        for default_cat in default_categories:
            if default_cat not in category_list:
                category_list.append(default_cat)
        
        category_var = ttk.Combobox(category_frame, values=category_list, font=dialog.fonts['normal'])
        try:
            category_var.current(category_list.index(category))
        except ValueError:
            category_var.set(category)
        category_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 单位
        unit_frame = ttk.Frame(dialog.main_frame)
        unit_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(unit_frame, text="单位: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        
        # 从数据库获取单位使用次数并排序
        conn_unit = sqlite3.connect(self.db_path)
        cursor_unit = conn_unit.cursor()
        cursor_unit.execute("SELECT unit, COUNT(*) as count FROM products GROUP BY unit ORDER BY count DESC")
        unit_results = cursor_unit.fetchall()
        conn_unit.close()
        
        # 创建单位下拉列表，包含已使用的单位和默认单位
        default_units = ["个", "件", "箱", "袋", "瓶", "盒", "kg", "g", "其他"]
        unit_list = [item[0] for item in unit_results]
        for default_unit in default_units:
            if default_unit not in unit_list:
                unit_list.append(default_unit)
        
        unit_var = ttk.Combobox(unit_frame, values=unit_list, font=dialog.fonts['normal'])
        try:
            unit_var.current(unit_list.index(unit))
        except ValueError:
            unit_var.set(unit)
        unit_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 进价
        purchase_price_frame = ttk.Frame(dialog.main_frame)
        purchase_price_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(purchase_price_frame, text="进价: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        purchase_price_var = ttk.Entry(purchase_price_frame, font=dialog.fonts['normal'])
        purchase_price_var.insert(0, purchase_price)
        purchase_price_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 售价
        selling_price_frame = ttk.Frame(dialog.main_frame)
        selling_price_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(selling_price_frame, text="售价: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        selling_price_var = ttk.Entry(selling_price_frame, font=dialog.fonts['normal'])
        selling_price_var.insert(0, selling_price)
        selling_price_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(dialog.main_frame)
        desc_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(desc_frame, text="描述: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        desc_var = ttk.Entry(desc_frame, font=dialog.fonts['normal'])
        desc_var.insert(0, description)
        desc_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                new_product_code = code_var.get().strip()
                new_name = name_var.get().strip()
                new_category = category_var.get()
                new_unit = unit_var.get()
                new_purchase_price = float(purchase_price_var.get().strip()) if purchase_price_var.get().strip() else 0
                new_selling_price = float(selling_price_var.get().strip()) if selling_price_var.get().strip() else 0
                new_description = desc_var.get().strip()
                
                # 自动添加操作者信息
                if self.current_user and hasattr(self.current_user, 'username'):
                    operator_info = f"[操作者: {self.current_user.username}]"
                elif self.current_user and isinstance(self.current_user, dict) and 'username' in self.current_user:
                    operator_info = f"[操作者: {self.current_user['username']}]"
                else:
                    operator_info = "[操作者: 未知]"
                
                # 检查描述中是否已包含操作者信息
                if not any(keyword in new_description for keyword in ['[操作者:', '【操作者:']):
                    # 在描述末尾添加操作者信息
                    if new_description:
                        new_description = f"{new_description} {operator_info}"
                    else:
                        new_description = operator_info
                
                # 验证输入
                if not new_name:
                    messagebox.showerror("错误", "产品名称不能为空！")
                    return
                
                if new_purchase_price < 0 or new_selling_price < 0:
                    messagebox.showerror("错误", "价格不能为负数！")
                    return
                
                # 连接数据库更新产品
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                try:
                    cursor.execute(
                        "UPDATE products SET name=?, category=?, unit=?, purchase_price=?, selling_price=?, description=? WHERE id=?",
                        (new_name, new_category, new_unit, new_purchase_price, new_selling_price, new_description, product_id)
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("成功", "产品更新成功！")
                    dialog.destroy()
                    self.refresh_product_list()
                    self.refresh_stock_list()
                except sqlite3.IntegrityError:
                    conn.close()
                    messagebox.showerror("错误", "产品编码已存在！")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字！")
            except Exception as e:
                messagebox.showerror("错误", f"更新产品失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10)
    
    def delete_product(self):
        """删除产品"""
        # 获取选中的产品
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个产品！")
            return
        
        # 获取产品ID (从item的iid中获取)
        product_id = selected_item[0]
        # 获取产品名称
        item_values = self.product_tree.item(selected_item[0])["values"]
        product_name = item_values[1]
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除产品 '{product_name}' 吗？\n删除后相关的进货、销售记录和库存数据也会被删除！"):
            return
        
        try:
            # 连接数据库删除产品
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除产品（级联删除相关记录）
            cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "产品删除成功！")
            self.refresh_product_list()
            self.refresh_stock_list()
            self.refresh_purchase_list()
            self.refresh_sale_list()
        except Exception as e:
            messagebox.showerror("错误", f"删除产品失败：{str(e)}")
    
    def init_purchase_frame(self):
        """初始化进货管理页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.purchase_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 添加进货按钮
        ttk.Button(control_frame, text="添加进货", command=self.add_purchase).pack(side="left", padx=5)
        
        # 删除进货记录按钮
        ttk.Button(control_frame, text="删除记录", command=self.delete_purchase_record).pack(side="left", padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_purchase_list).pack(side="left", padx=5)
        
        # 日期范围选择
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(side="right", padx=5)
        
        ttk.Label(date_frame, text="起始日期: ").pack(side="left")
        self.purchase_start_date_var = tk.StringVar(value=(datetime.date.today().replace(day=1)).strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.purchase_start_date_var, width=12).pack(side="left", padx=5)
        
        ttk.Label(date_frame, text="结束日期: ").pack(side="left")
        self.purchase_end_date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.purchase_end_date_var, width=12).pack(side="left", padx=5)
        
        ttk.Button(date_frame, text="查询", command=self.refresh_purchase_list).pack(side="left", padx=5)
        
        # 进货列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview - 删除ID列
        columns = ("product_name", "quantity", "unit_price", "total_amount", "purchase_date", "supplier", "created_by")
        self.purchase_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题 - 删除ID列标题
        self.purchase_tree.heading("product_name", text="产品名称")
        self.purchase_tree.heading("quantity", text="数量")
        self.purchase_tree.heading("unit_price", text="单价")
        self.purchase_tree.heading("total_amount", text="总金额")
        self.purchase_tree.heading("purchase_date", text="进货日期")
        self.purchase_tree.heading("supplier", text="供应商")
        self.purchase_tree.heading("created_by", text="创建人")
        
        # 设置列宽 - 删除ID列宽度设置
        self.purchase_tree.column("product_name", width=150)
        self.purchase_tree.column("quantity", width=80, anchor="center")
        self.purchase_tree.column("unit_price", width=80, anchor="center")
        self.purchase_tree.column("total_amount", width=100, anchor="center")
        self.purchase_tree.column("purchase_date", width=120)
        self.purchase_tree.column("supplier", width=120)
        self.purchase_tree.column("created_by", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.purchase_tree.yview)
        self.purchase_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.purchase_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 刷新进货列表
        self.refresh_purchase_list()
    
    def refresh_purchase_list(self):
        """刷新进货列表"""
        # 清空Treeview
        for item in self.purchase_tree.get_children():
            self.purchase_tree.delete(item)
        
        # 获取日期范围
        start_date = self.purchase_start_date_var.get()
        end_date = self.purchase_end_date_var.get()
        
        try:
            # 验证日期格式
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
            return
        
        # 连接数据库获取进货记录
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT p.id, pr.name, p.quantity, p.unit_price, p.total_amount, p.purchase_date, p.supplier, p.created_by 
               FROM purchases p 
               JOIN products pr ON p.product_id = pr.id 
               WHERE p.purchase_date BETWEEN ? AND ? 
               ORDER BY p.purchase_date DESC""",
            (start_date, end_date)
        )
        purchase_records = cursor.fetchall()
        conn.close()
        
        # 添加到Treeview - 将ID作为iid，不显示在列中
        total_amount = 0
        for record in purchase_records:
            id, product_name, quantity, unit_price, total, purchase_date, supplier, created_by = record
            self.purchase_tree.insert("", "end", iid=id,
                values=(product_name, quantity, unit_price, total, purchase_date, supplier, created_by))
            total_amount += total
        
        # 显示总计 - 将总计金额放在总金额列下方
        self.purchase_tree.insert("", "end",
            values=("总计", "", "", total_amount, "", "", ""))
    
    def add_purchase(self):
        """添加进货记录"""
        # 连接数据库获取产品列表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM products ORDER BY name")
        products = cursor.fetchall()
        conn.close()
        
        if not products:
            messagebox.showinfo("提示", "请先添加产品！")
            return
        
        # 创建添加进货对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加进货记录", width_percent=0.7, height_percent=0.7)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 15
        
        # 产品选择
        product_frame = ttk.Frame(dialog.main_frame)
        product_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(product_frame, text="产品: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        product_var = tk.StringVar()
        product_combo = ttk.Combobox(product_frame, textvariable=product_var, state="normal", font=dialog.fonts['normal'])
        
        # 提取产品名称列表
        product_names = [product[1] for product in products]
        product_combo['values'] = product_names
        if products:
            product_combo.current(0)
        product_combo.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 产品搜索功能
        def on_product_input(event):
            try:
                from pypinyin import lazy_pinyin
                
                input_text = product_var.get().lower()
                if not input_text:
                    product_combo['values'] = product_names
                    return
                
                # 模糊匹配并按相似度排序
                matched_products = []
                for product_name in product_names:
                    # 原始名称匹配
                    if input_text in product_name.lower():
                        # 计算匹配度（包含位置越靠前，匹配度越高）
                        match_position = product_name.lower().find(input_text)
                        # 将匹配度和产品名称一起保存
                        matched_products.append((match_position, product_name))
                    else:
                        # 拼音首字母匹配
                        try:
                            # 获取产品名称的拼音首字母
                            pinyin_initials = ''.join([s[0] for s in lazy_pinyin(product_name) if s])
                            if input_text in pinyin_initials.lower():
                                # 对于拼音首字母匹配，给一个较高的匹配位置值，表示优先级稍低
                                match_position = 100 + pinyin_initials.lower().find(input_text)
                                matched_products.append((match_position, product_name))
                        except:
                            # 如果拼音转换失败，忽略此匹配
                            pass
                
                # 按匹配度排序（匹配位置越靠前，排序越靠前）
                matched_products.sort(key=lambda x: x[0])
                # 提取排序后的产品列表
                sorted_products = [product for _, product in matched_products]
                
                # 更新下拉菜单
                product_combo['values'] = sorted_products
                if sorted_products:
                    product_combo.event_generate('<Down>')  # 触发下拉菜单显示
            except Exception as e:
                pass
        
        # 绑定输入事件
        product_combo.bind('<KeyRelease>', on_product_input)
        
        # 类别
        category_frame = ttk.Frame(dialog.main_frame)
        category_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(category_frame, text="类别: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(category_frame, textvariable=category_var, state="normal", font=dialog.fonts['normal'])
        category_combo.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 获取所有产品类别
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
        all_categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # 类别搜索功能
        def on_category_input(event):
            try:
                input_text = category_var.get().lower()
                if not input_text:
                    category_combo['values'] = []
                    return
                
                # 模糊匹配并按相似度排序
                matched_categories = []
                for category in all_categories:
                    if input_text in category.lower():
                        # 计算匹配度（包含位置越靠前，匹配度越高）
                        match_position = category.lower().find(input_text)
                        # 将匹配度和类别一起保存
                        matched_categories.append((match_position, category))
                
                # 按匹配度排序（匹配位置越靠前，排序越靠前）
                matched_categories.sort(key=lambda x: x[0])
                # 提取排序后的类别列表
                sorted_categories = [category for _, category in matched_categories]
                
                # 更新下拉菜单
                category_combo['values'] = sorted_categories
                if sorted_categories:
                    category_combo.event_generate('<Down>')  # 触发下拉菜单显示
            except Exception as e:
                pass
        
        # 绑定输入事件
        category_combo.bind('<KeyRelease>', on_category_input)
        
        # 数量
        quantity_frame = ttk.Frame(dialog.main_frame)
        quantity_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(quantity_frame, text="数量: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        quantity_var = ttk.Entry(quantity_frame, font=dialog.fonts['normal'])
        quantity_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 单价
        unit_price_frame = ttk.Frame(dialog.main_frame)
        unit_price_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(unit_price_frame, text="单价: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        unit_price_var = ttk.Entry(unit_price_frame, font=dialog.fonts['normal'])
        unit_price_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 获取所选产品的类别信息和进价并更新下拉框和单价输入框
        def update_category_and_price(event=None):
            selected_product = product_var.get()
            if selected_product:
                try:
                    # 连接数据库获取所选产品的类别和进价
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT category, purchase_price FROM products WHERE name = ?", (selected_product,))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        # 显示产品管理中的类别信息
                        category_combo['values'] = [result[0]]
                        category_combo.current(0)
                        # 设置单价为产品管理中的进价，并设为可写状态
                        unit_price_var.delete(0, tk.END)
                        unit_price_var.insert(0, str(result[1]))
                        unit_price_var.config(state="normal")
                    else:
                        category_combo['values'] = []
                        category_var.set("")
                except Exception as e:
                    messagebox.showerror("错误", f"获取产品信息失败：{str(e)}")
                    category_combo['values'] = []
                    category_var.set("")
            else:
                category_combo['values'] = []
                category_var.set("")
        
        # 绑定产品选择事件，自动更新类别和单价
        product_combo.bind("<<ComboboxSelected>>", update_category_and_price)
        
        # 初始化时更新类别和单价
        if products:
            update_category_and_price()
        
        # 进货日期
        date_frame = ttk.Frame(dialog.main_frame)
        date_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(date_frame, text="进货日期: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=date_var, font=dialog.fonts['normal']).pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 供应商
        supplier_frame = ttk.Frame(dialog.main_frame)
        supplier_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(supplier_frame, text="供应商: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        supplier_var = ttk.Entry(supplier_frame, font=dialog.fonts['normal'])
        supplier_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                # 获取选中的产品名称
                selected_product_name = product_var.get()
                
                # 查找产品ID
                product_id = None
                for product in products:
                    if product[1] == selected_product_name:
                        product_id = product[0]
                        break
                
                if not product_id:
                    messagebox.showerror("错误", "找不到选中的产品！")
                    return
                
                quantity = int(quantity_var.get().strip())
                unit_price = float(unit_price_var.get().strip())
                purchase_date = date_var.get().strip()
                supplier = supplier_var.get().strip()
                created_by = "admin"  # 这里应该从当前登录用户获取
                
                # 获取产品原始进价
                conn_get_price = sqlite3.connect(self.db_path)
                cursor_get_price = conn_get_price.cursor()
                cursor_get_price.execute("SELECT purchase_price FROM products WHERE id = ?", (product_id,))
                original_price = cursor_get_price.fetchone()[0]
                conn_get_price.close()
                
                update_product_price = False
                
                # 如果用户修改了单价，询问是否同步更新产品管理中的单价
                if abs(unit_price - original_price) > 0.01:  # 考虑浮点精度问题
                    result = messagebox.askyesno("确认修改", f"您修改了单价（原始价: {original_price}，新价: {unit_price}）\n是否同时更新产品管理中的单价？")
                    if result:
                        update_product_price = True
                
                # 验证输入
                if quantity <= 0:
                    messagebox.showerror("错误", "数量必须大于0！")
                    return
                
                if unit_price < 0:
                    messagebox.showerror("错误", "单价不能为负数！")
                    return
                
                if not purchase_date:
                    messagebox.showerror("错误", "进货日期不能为空！")
                    return
                
                # 验证日期格式
                try:
                    datetime.datetime.strptime(purchase_date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                    return
                
                # 计算总金额
                total_amount = quantity * unit_price
                
                # 连接数据库添加进货记录
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                try:
                    # 检查是否已存在同一天相同产品的进货记录
                    cursor.execute(
                        "SELECT id, quantity, unit_price FROM purchases WHERE product_id = ? AND purchase_date = ?",
                        (product_id, purchase_date)
                    )
                    existing_record = cursor.fetchone()
                    
                    if existing_record:
                        # 存在相同记录，累加数量
                        existing_id, existing_quantity, existing_price = existing_record
                        new_quantity = existing_quantity + quantity
                        # 如果单价有变化，使用新的单价重新计算总金额
                        new_unit_price = unit_price if abs(unit_price - existing_price) > 0.01 else existing_price
                        new_total_amount = new_quantity * new_unit_price
                        
                        # 更新现有记录
                        cursor.execute(
                            "UPDATE purchases SET quantity = ?, unit_price = ?, total_amount = ?, supplier = ? WHERE id = ?",
                            (new_quantity, new_unit_price, new_total_amount, supplier, existing_id)
                        )
                        
                        # 更新库存（注意：这里只需要增加新的数量，因为库存已经包含了原有的数量）
                        cursor.execute(
                            "UPDATE inventory SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
                            (quantity, product_id)
                        )
                    else:
                        # 不存在相同记录，插入新记录
                        cursor.execute(
                            "INSERT INTO purchases (product_id, quantity, unit_price, total_amount, purchase_date, supplier, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (product_id, quantity, unit_price, total_amount, purchase_date, supplier, created_by)
                        )
                        
                        # 更新库存
                        cursor.execute(
                            "UPDATE inventory SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
                            (quantity, product_id)
                        )
                    
                    # 如果用户确认，同步更新产品管理中的单价
                    if update_product_price:
                        cursor.execute(
                            "UPDATE products SET purchase_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (unit_price, product_id)
                        )
                    
                    conn.commit()
                    conn.close()
                    
                    # 根据操作类型显示不同的成功消息
                    if existing_record:
                        messagebox.showinfo("成功", "进货记录已更新，数量已累加！")
                    else:
                        messagebox.showinfo("成功", "进货记录添加成功！")
                    
                    dialog.destroy()
                    self.refresh_purchase_list()
                    self.refresh_stock_list()
                except Exception as e:
                    conn.close()
                    messagebox.showerror("错误", f"添加进货记录失败：{str(e)}")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字！")
            except Exception as e:
                messagebox.showerror("错误", f"添加进货记录失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10)
    
    def delete_purchase_record(self):
        """删除进货记录"""
        # 获取选中的进货记录
        selected_item = self.purchase_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条进货记录！")
            return
        
        # 获取进货ID（从item的iid中获取）
        purchase_id = selected_item[0]
        
        # 如果是总计行（iid为空字符串），不删除
        if purchase_id == "":
            messagebox.showinfo("提示", "不能删除总计行！")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", "确定要删除这条进货记录吗？\n删除后库存也会相应减少！"):
            return
        
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取进货记录的产品ID和数量
            cursor.execute(
                "SELECT product_id, quantity FROM purchases WHERE id=?",
                (purchase_id,)
            )
            purchase_info = cursor.fetchone()
            
            if not purchase_info:
                conn.close()
                messagebox.showerror("错误", "找不到指定的进货记录！")
                return
            
            product_id, quantity = purchase_info
            
            # 删除进货记录
            cursor.execute(
                "DELETE FROM purchases WHERE id=?",
                (purchase_id,)
            )
            
            # 更新库存
            cursor.execute(
                "UPDATE inventory SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
                (quantity, product_id)
            )
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "进货记录删除成功！")
            self.refresh_purchase_list()
            self.refresh_stock_list()
        except Exception as e:
            messagebox.showerror("错误", f"删除进货记录失败：{str(e)}")
    
    def init_sale_frame(self):
        """初始化销售管理页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.sale_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 添加销售按钮
        ttk.Button(control_frame, text="添加销售", command=self.add_sale).pack(side="left", padx=5)
        
        # 删除销售记录按钮
        ttk.Button(control_frame, text="删除记录", command=self.delete_sale_record).pack(side="left", padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_sale_list).pack(side="left", padx=5)
        
        # 日期范围选择
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(side="right", padx=5)
        
        ttk.Label(date_frame, text="起始日期: ").pack(side="left")
        self.sale_start_date_var = tk.StringVar(value=(datetime.date.today().replace(day=1)).strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.sale_start_date_var, width=12).pack(side="left", padx=5)
        
        ttk.Label(date_frame, text="结束日期: ").pack(side="left")
        self.sale_end_date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.sale_end_date_var, width=12).pack(side="left", padx=5)
        
        ttk.Button(date_frame, text="查询", command=self.refresh_sale_list).pack(side="left", padx=5)
        
        # 销售列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview - 删除ID列
        columns = ("product_name", "quantity", "unit_price", "total_amount", "sale_date", "customer", "created_by")
        self.sale_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题 - 删除ID列标题
        self.sale_tree.heading("product_name", text="产品名称")
        self.sale_tree.heading("quantity", text="数量")
        self.sale_tree.heading("unit_price", text="单价")
        self.sale_tree.heading("total_amount", text="总金额")
        self.sale_tree.heading("sale_date", text="销售日期")
        self.sale_tree.heading("customer", text="客户")
        self.sale_tree.heading("created_by", text="创建人")
        
        # 设置列宽 - 删除ID列宽度设置
        self.sale_tree.column("product_name", width=150)
        self.sale_tree.column("quantity", width=80, anchor="center")
        self.sale_tree.column("unit_price", width=80, anchor="center")
        self.sale_tree.column("total_amount", width=100, anchor="center")
        self.sale_tree.column("sale_date", width=120)
        self.sale_tree.column("customer", width=120)
        self.sale_tree.column("created_by", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.sale_tree.yview)
        self.sale_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.sale_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 刷新销售列表
        self.refresh_sale_list()
    
    def refresh_sale_list(self):
        """刷新销售列表"""
        # 清空Treeview
        for item in self.sale_tree.get_children():
            self.sale_tree.delete(item)
        
        # 获取日期范围
        start_date = self.sale_start_date_var.get()
        end_date = self.sale_end_date_var.get()
        
        try:
            # 验证日期格式
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
            return
        
        # 连接数据库获取销售记录
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT s.id, pr.name, s.quantity, s.unit_price, s.total_amount, s.sale_date, s.customer, s.created_by 
               FROM sales s 
               JOIN products pr ON s.product_id = pr.id 
               WHERE s.sale_date BETWEEN ? AND ? 
               ORDER BY s.sale_date DESC""",
            (start_date, end_date)
        )
        sale_records = cursor.fetchall()
        conn.close()
        
        # 添加到Treeview - 将ID作为iid，不显示在列中
        total_amount = 0
        for record in sale_records:
            id, product_name, quantity, unit_price, total, sale_date, customer, created_by = record
            self.sale_tree.insert("", "end", iid=id,
                values=(product_name, quantity, unit_price, total, sale_date, customer, created_by))
            total_amount += total
        
        # 显示总计 - 将总计金额放在总金额列下方
        self.sale_tree.insert("", "end",
            values=("总计", "", "", total_amount, "", "", ""))
    
    def add_sale(self):
        """添加销售记录"""
        # 连接数据库获取有库存的产品列表及售价
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT pr.id, pr.name, pr.product_code, i.quantity, pr.selling_price FROM products pr 
               JOIN inventory i ON pr.id = i.product_id 
               WHERE i.quantity > 0 
               ORDER BY pr.name"""
        )
        products = cursor.fetchall()
        conn.close()
        
        if not products:
            messagebox.showinfo("提示", "当前没有可销售的产品！")
            return
        
        # 创建添加销售对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加销售记录", width_percent=0.7, height_percent=0.7)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 15
        
        # 存储产品售价和编码字典，用于快速查找
        product_prices = {product[1]: product[4] for product in products}
        product_codes = {product[1]: product[2] for product in products}
        
        # 初始单价变量，用于比较用户是否修改了单价
        original_price = 0
        
        # 产品选择
        product_frame = ttk.Frame(dialog.main_frame)
        product_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(product_frame, text="产品: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        product_var = tk.StringVar()
        product_combo = ttk.Combobox(product_frame, textvariable=product_var, state="normal", font=dialog.fonts['normal'])
        
        # 提取产品名称列表
        product_display_list = [f"{product[1]} (库存: {product[3]})" for product in products]
        product_names = [product[1] for product in products]
        product_combo['values'] = product_display_list
        
        if products:
            product_combo.current(0)
        
        product_combo.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 产品搜索功能
        def on_product_input(event):
            try:
                from pypinyin import lazy_pinyin
                
                input_text = product_var.get().lower()
                if not input_text:
                    product_combo['values'] = product_display_list
                    return
                
                # 模糊匹配并按相似度排序
                matched_products = []
                for i, product_name in enumerate(product_names):
                    # 原始名称匹配
                    if input_text in product_name.lower():
                        # 计算匹配度（包含位置越靠前，匹配度越高）
                        match_position = product_name.lower().find(input_text)
                        # 将匹配度和产品显示文本一起保存
                        matched_products.append((match_position, product_display_list[i]))
                    else:
                        # 拼音首字母匹配
                        try:
                            # 获取产品名称的拼音首字母
                            pinyin_initials = ''.join([s[0] for s in lazy_pinyin(product_name) if s])
                            if input_text in pinyin_initials.lower():
                                # 对于拼音首字母匹配，给一个较高的匹配位置值，表示优先级稍低
                                match_position = 100 + pinyin_initials.lower().find(input_text)
                                matched_products.append((match_position, product_display_list[i]))
                        except:
                            # 如果拼音转换失败，忽略此匹配
                            pass
                
                # 按匹配度排序（匹配位置越靠前，排序越靠前）
                matched_products.sort(key=lambda x: x[0])
                # 提取排序后的产品列表
                sorted_products = [product for _, product in matched_products]
                
                # 更新下拉菜单
                product_combo['values'] = sorted_products
                if sorted_products:
                    product_combo.event_generate('<Down>')  # 触发下拉菜单显示
            except Exception as e:
                # 如果发生任何错误，回退到原始列表
                product_combo['values'] = product_display_list
        
        # 绑定输入事件
        product_combo.bind('<KeyRelease>', on_product_input)
        
        # 数量
        quantity_frame = ttk.Frame(dialog.main_frame)
        quantity_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(quantity_frame, text="数量: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        quantity_var = ttk.Entry(quantity_frame, font=dialog.fonts['normal'])
        quantity_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 单价
        unit_price_frame = ttk.Frame(dialog.main_frame)
        unit_price_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(unit_price_frame, text="单价: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        unit_price_var = ttk.Entry(unit_price_frame, font=dialog.fonts['normal'])
        unit_price_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 产品选择事件处理函数
        def on_product_selected(event=None):
            nonlocal original_price
            selected_product_text = product_var.get()
            if selected_product_text:
                # 解析产品名称
                product_name = selected_product_text.split(" (")[0]
                # 获取并设置产品单价
                if product_name in product_prices:
                    selling_price = product_prices[product_name]
                    unit_price_var.delete(0, tk.END)
                    unit_price_var.insert(0, str(selling_price))
                    original_price = selling_price
        
        # 绑定产品选择事件
        product_combo.bind("<<ComboboxSelected>>", on_product_selected)
        
        # 初始加载第一个产品的单价（在unit_price_var定义后调用）
        if products:
            on_product_selected()
        
        # 销售日期
        date_frame = ttk.Frame(dialog.main_frame)
        date_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(date_frame, text="销售日期: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=date_var, font=dialog.fonts['normal']).pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 客户
        customer_frame = ttk.Frame(dialog.main_frame)
        customer_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(customer_frame, text="客户: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        customer_var = ttk.Entry(customer_frame, font=dialog.fonts['normal'])
        customer_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        

        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                # 获取选中的产品显示文本
                selected_product_text = product_var.get()
                
                # 解析产品名称
                product_name = selected_product_text.split(" (")[0]
                
                # 查找产品ID、可用数量和产品编码
                product_id = None
                available_quantity = 0
                product_code = None
                for product in products:
                    if product[1] == product_name:
                        product_id = product[0]
                        available_quantity = product[3]
                        product_code = product[2]  # 获取产品编码
                        break
                
                # 获取用户输入的单价并检查是否有修改
                user_input_price = float(unit_price_var.get().strip())
                
                # 如果用户修改了单价，提示用户
                if abs(user_input_price - original_price) > 0.01:  # 考虑浮点精度问题
                    result = messagebox.askyesno("确认修改", f"您修改了单价（原价: {original_price}，新价: {user_input_price}）\n是否确认使用新单价进行销售？")
                    if not result:
                        # 如果用户取消，恢复原始单价并退出
                        unit_price_var.delete(0, tk.END)
                        unit_price_var.insert(0, str(original_price))
                        return
                
                if not product_id:
                    messagebox.showerror("错误", "找不到选中的产品！")
                    return
                
                quantity = int(quantity_var.get().strip())
                unit_price = user_input_price
                sale_date = date_var.get().strip()
                customer = customer_var.get().strip()
                created_by = "admin"  # 这里应该从当前登录用户获取
                
                # 验证输入
                if quantity <= 0:
                    messagebox.showerror("错误", "数量必须大于0！")
                    return
                
                if unit_price < 0:
                    messagebox.showerror("错误", "单价不能为负数！")
                    return
                
                if not sale_date:
                    messagebox.showerror("错误", "销售日期不能为空！")
                    return
                
                # 验证日期格式
                try:
                    datetime.datetime.strptime(sale_date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                    return
                
                # 检查库存是否足够
                if quantity > available_quantity:
                    messagebox.showerror("错误", f"库存不足！当前库存：{available_quantity}")
                    return
                
                # 计算总金额
                total_amount = quantity * unit_price
                
                # 连接数据库添加销售记录
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                try:
                    # 检查是否存在相同产品、相同日期的销售记录
                    cursor.execute(
                        "SELECT id, quantity, total_amount FROM sales WHERE product_id = ? AND sale_date = ?",
                        (product_id, sale_date)
                    )
                    existing_record = cursor.fetchone()
                    
                    if existing_record:
                        # 存在相同记录，累加数量和总金额
                        record_id, existing_quantity, existing_total = existing_record
                        new_quantity = existing_quantity + quantity
                        new_total = existing_total + total_amount
                        
                        # 更新现有记录
                        cursor.execute(
                            "UPDATE sales SET quantity = ?, total_amount = ? WHERE id = ?",
                            (new_quantity, new_total, record_id)
                        )
                        
                        message = "销售记录已更新，数量已累加！"
                    else:
                        # 不存在相同记录，插入新记录
                        cursor.execute(
                            "INSERT INTO sales (product_id, quantity, unit_price, total_amount, sale_date, customer, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (product_id, quantity, unit_price, total_amount, sale_date, customer, created_by)
                        )
                        
                        message = "销售记录添加成功！"
                    
                    # 更新库存
                    cursor.execute(
                        "UPDATE inventory SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
                        (quantity, product_id)
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("成功", message)
                    dialog.destroy()
                    self.refresh_sale_list()
                    self.refresh_stock_list()
                    
                    # 销售成功后，自动切换到客户管理标签页
                    if hasattr(self, 'inventory_notebook'):
                        # 找到客户管理标签页的索引
                        for i, tab in enumerate(self.inventory_notebook.tabs()):
                            if self.inventory_notebook.tab(tab, "text") == "客户管理":
                                self.inventory_notebook.select(i)
                                
                                # 检查是否有客户名称
                                if customer:
                                    # 连接数据库检查客户是否已存在
                                    check_conn = sqlite3.connect(self.db_path)
                                    check_cursor = check_conn.cursor()
                                    check_cursor.execute("SELECT contact_person FROM customers WHERE contact_person = ?", (customer,))
                                    existing_customer = check_cursor.fetchone()
                                    check_conn.close()
                                      
                                    # 如果客户不存在，才启动添加客户功能
                                    if not existing_customer:
                                        self.root.after(100, lambda: self.add_customer(product_code=product_code, customer_name=customer, total_amount=total_amount))
                                    else:
                                        # 如果客户已存在，刷新客户列表以更新销售金额
                                        self.root.after(100, self.refresh_customer_list)
                                break
                    else:
                        # 如果找不到inventory_notebook属性，至少刷新客户列表以更新销售金额
                        if hasattr(self, 'refresh_customer_list'):
                            self.root.after(100, self.refresh_customer_list)
                    

                except Exception as e:
                    conn.close()
                    messagebox.showerror("错误", f"添加销售记录失败：{str(e)}")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字！")
            except Exception as e:
                messagebox.showerror("错误", f"添加销售记录失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10)
    
    def delete_sale_record(self):
        """删除销售记录"""
        # 获取选中的销售记录
        selected_item = self.sale_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条销售记录！")
            return
        
        # 获取销售ID（从item的iid中获取）
        sale_id = selected_item[0]
        
        # 如果是总计行（iid为空字符串），不删除
        if sale_id == "":
            messagebox.showinfo("提示", "不能删除总计行！")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", "确定要删除这条销售记录吗？\n删除后库存也会相应增加！"):
            return
        
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取销售记录的产品ID和数量
            cursor.execute(
                "SELECT product_id, quantity FROM sales WHERE id=?",
                (sale_id,)
            )
            sale_info = cursor.fetchone()
            
            if not sale_info:
                conn.close()
                messagebox.showerror("错误", "找不到指定的销售记录！")
                return
            
            product_id, quantity = sale_info
            
            # 删除销售记录
            cursor.execute(
                "DELETE FROM sales WHERE id=?",
                (sale_id,)
            )
            
            # 更新库存
            cursor.execute(
                "UPDATE inventory SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
                (quantity, product_id)
            )
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "销售记录删除成功！")
            self.refresh_sale_list()
            self.refresh_stock_list()
        except Exception as e:
            messagebox.showerror("错误", f"删除销售记录失败：{str(e)}")
    
    def init_stock_frame(self):
        """初始化库存查询页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.stock_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_stock_list).pack(side="left", padx=5)
        
        # 删除库存按钮
        ttk.Button(control_frame, text="删除库存", command=self.delete_stock).pack(side="left", padx=5)
        
        # 低库存提醒阈值设置
        threshold_frame = ttk.Frame(control_frame)
        threshold_frame.pack(side="right", padx=5)
        
        ttk.Label(threshold_frame, text="低库存提醒阈值: ").pack(side="left")
        self.low_stock_threshold_var = tk.StringVar(value="10")
        ttk.Entry(threshold_frame, textvariable=self.low_stock_threshold_var, width=5).pack(side="left", padx=5)
        
        # 库存列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview - 删除ID列
        columns = ("product_code", "product_name", "category", "unit", "quantity", "purchase_price", "selling_price", "updated_at")
        self.stock_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题 - 删除ID列标题
        self.stock_tree.heading("product_code", text="产品编码")
        self.stock_tree.heading("product_name", text="产品名称")
        self.stock_tree.heading("category", text="类别")
        self.stock_tree.heading("unit", text="单位")
        self.stock_tree.heading("quantity", text="库存数量")
        self.stock_tree.heading("purchase_price", text="进价")
        self.stock_tree.heading("selling_price", text="售价")
        self.stock_tree.heading("updated_at", text="更新时间")
        
        # 设置列宽 - 删除ID列宽度设置
        self.stock_tree.column("product_code", width=120)
        self.stock_tree.column("product_name", width=150)
        self.stock_tree.column("category", width=100)
        self.stock_tree.column("unit", width=80)
        self.stock_tree.column("quantity", width=100, anchor="center")
        self.stock_tree.column("purchase_price", width=80, anchor="center")
        self.stock_tree.column("selling_price", width=80, anchor="center")
        self.stock_tree.column("updated_at", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.stock_tree.yview)
        self.stock_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.stock_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 刷新库存列表
        self.refresh_stock_list()
    
    def refresh_stock_list(self):
        """刷新库存列表"""
        # 清空Treeview
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # 获取低库存阈值
        try:
            low_stock_threshold = int(self.low_stock_threshold_var.get().strip())
        except ValueError:
            low_stock_threshold = 10
            self.low_stock_threshold_var.set("10")
        
        # 连接数据库获取库存信息
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT pr.id, pr.product_code, pr.name, pr.category, pr.unit, i.quantity, pr.purchase_price, pr.selling_price, i.updated_at 
               FROM products pr 
               JOIN inventory i ON pr.id = i.product_id 
               ORDER BY pr.name"""
        )
        stock_info = cursor.fetchall()
        conn.close()
        
        # 检查低库存产品
        low_stock_products = []
        
        # 添加到Treeview - 将ID作为iid，不显示在列中
        total_purchase_value = 0
        total_selling_value = 0
        for stock in stock_info:
            id, product_code, product_name, category, unit, quantity, purchase_price, selling_price, updated_at = stock
            
            # 计算库存价值 - 进价和售价
            total_purchase_value += quantity * purchase_price
            total_selling_value += quantity * selling_price
            
            # 添加到Treeview
            item = self.stock_tree.insert("", "end", iid=id,
                values=(product_code, product_name, category, unit, quantity, purchase_price, selling_price, updated_at))
            
            # 如果库存低于阈值，标记为低库存
            if quantity <= low_stock_threshold:
                low_stock_products.append(product_name)
                # 设置行颜色为红色
                self.stock_tree.item(item, tags=("low_stock",))
        
        # 设置低库存行的样式
        self.stock_tree.tag_configure("low_stock", foreground="red")
        
        # 显示总计 - 同时显示进价和售价的累计
        self.stock_tree.insert("", "end",
            values=("", "总计", "", "", "", total_purchase_value, total_selling_value, ""))
        
        # 如果有低库存产品，显示提醒
        if low_stock_products:
                messagebox.showinfo("低库存提醒", f"以下产品库存不足：\n{', '.join(low_stock_products)}")

    def delete_stock(self):
        """删除库存"""
        # 获取选中的库存项目
        selected_item = self.stock_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个库存项目！")
            return
        
        # 获取产品ID (从item的iid中获取)
        product_id = selected_item[0]
        # 获取产品名称
        item_values = self.stock_tree.item(selected_item[0])["values"]
        product_name = item_values[1]
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除产品 '{product_name}' 的库存记录吗？\n删除后该产品将不再在库存列表中显示！"):
            return
        
        try:
            # 连接数据库删除库存
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除库存记录
            cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "库存记录删除成功！")
            self.refresh_stock_list()
        except Exception as e:
            messagebox.showerror("错误", f"删除库存记录失败：{str(e)}")
            
    def init_customer_frame(self):
        """初始化客户管理页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.customer_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 添加客户按钮
        ttk.Button(control_frame, text="添加客户", command=self.add_customer).pack(side="left", padx=5)
        
        # 修改客户按钮
        ttk.Button(control_frame, text="修改客户", command=self.edit_customer).pack(side="left", padx=5)
        
        # 删除客户按钮
        ttk.Button(control_frame, text="删除客户", command=self.delete_customer).pack(side="left", padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_customer_list).pack(side="left", padx=5)
        
        # 排序方式按钮
        self.sort_by_sales = True
        self.sort_button = ttk.Button(control_frame, text="按编码排序", command=self.toggle_sort)
        self.sort_button.pack(side="left", padx=5)
        
        # 客户列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview - 删除ID列，添加总销售金额列
        columns = ("customer_code", "contact_person", "phone", "email", "address", "total_sales", "description")
        self.customer_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题 - 删除ID列标题
        self.customer_tree.heading("customer_code", text="客户编码")
        self.customer_tree.heading("contact_person", text="联系人")
        self.customer_tree.heading("phone", text="电话")
        self.customer_tree.heading("email", text="邮箱")
        self.customer_tree.heading("address", text="地址")
        self.customer_tree.heading("total_sales", text="总销售金额")
        self.customer_tree.heading("description", text="描述")
        
        # 设置列宽 - 删除ID列宽度设置
        self.customer_tree.column("customer_code", width=120)
        self.customer_tree.column("contact_person", width=100)
        self.customer_tree.column("phone", width=120)
        self.customer_tree.column("email", width=150)
        self.customer_tree.column("total_sales", width=120, anchor="center")
        self.customer_tree.column("address", width=200)
        self.customer_tree.column("description", width=300)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.customer_tree.yview)
        self.customer_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.customer_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定双击事件，编辑客户
        self.customer_tree.bind("<Double-1>", lambda event: self.edit_customer())
        
        # 刷新客户列表
        self.refresh_customer_list()
    
    def refresh_customer_list(self):
        """刷新客户列表 - 增强版"""
        try:
            # 强制刷新前先隐藏Treeview，避免闪烁
            self.customer_tree.pack_forget()
            
            # 清空Treeview
            for item in self.customer_tree.get_children():
                self.customer_tree.delete(item)
            
            # 连接数据库获取客户列表，并计算总销售金额
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 根据排序状态选择不同的SQL查询
            if self.sort_by_sales:
                # 按总销售金额降序排序
                cursor.execute("""SELECT c.id, c.customer_code, c.name, c.contact_person, c.phone, c.email, 
                                  COALESCE(SUM(s.total_amount), 0) as total_sales, c.description 
                                  FROM customers c 
                                  LEFT JOIN sales s ON c.contact_person = s.customer 
                                  GROUP BY c.id, c.customer_code, c.name, c.contact_person, c.phone, c.email, c.description 
                                  ORDER BY total_sales DESC""")
            else:
                # 按客户编码排序
                cursor.execute("""SELECT c.id, c.customer_code, c.name, c.contact_person, c.phone, c.email, 
                                  COALESCE(SUM(s.total_amount), 0) as total_sales, c.description 
                                  FROM customers c 
                                  LEFT JOIN sales s ON c.contact_person = s.customer 
                                  GROUP BY c.id, c.customer_code, c.name, c.contact_person, c.phone, c.email, c.description 
                                  ORDER BY customer_code""")
            customers = cursor.fetchall()
            conn.close()
            
            # 打印调试信息，确认数据已从数据库获取
            print(f"刷新客户列表：共获取到{len(customers)}个客户")
            
            # 添加到Treeview - 将ID作为iid，不显示在列中
            for customer in customers:
                id, customer_code, name, contact_person, phone, email, total_sales, description = customer
                # 确保所有值都不为None，避免Treeview显示问题
                values = (
                    customer_code or "",
                    contact_person or "",
                    phone or "",
                    email or "",
                    "" or "",  # 地址字段，根据之前的查询修改
                    total_sales or 0,
                    description or "")
                self.customer_tree.insert("", "end", iid=id, values=values)
            
            # 重新显示Treeview
            self.customer_tree.pack(side="left", fill="both", expand=True)
            
            # 多重强制更新UI
            self.customer_tree.update_idletasks()
            self.customer_frame.update_idletasks()  # 刷新整个客户框架
            self.root.update_idletasks()            # 刷新整个应用
            
            # 添加短暂延迟后再次刷新，确保彻底更新
            self.root.after(50, self.customer_tree.update_idletasks)
            
        except Exception as e:
            # 添加更详细的错误日志，有助于排查问题
            print(f"刷新客户列表时出错: {str(e)}")
            
            # 显示错误信息给用户
            messagebox.showerror("错误", f"刷新客户列表失败：{str(e)}")
    
    def toggle_sort(self):
        """切换客户列表的排序方式"""
        self.sort_by_sales = not self.sort_by_sales
        if self.sort_by_sales:
            self.sort_button.config(text="按编码排序")
            print("切换客户列表排序方式：按总销售金额降序")
        else:
            self.sort_button.config(text="按销售排序")
            print("切换客户列表排序方式：按客户编码升序")
        self.refresh_customer_list()
    
    def validate_phone(self, phone):
        """验证手机号格式是否正确"""
        # 中国手机号规范：11位数字，以1开头
        import re
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))
        
    def add_customer(self, product_code=None, customer_name=None, total_amount=None):
        """添加客户信息"""
        # 创建添加客户对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加客户" if total_amount is None else "客户信息确认", width_percent=0.7, height_percent=0.7)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 15
        
        # 客户编码
        code_frame = ttk.Frame(dialog.main_frame)
        code_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(code_frame, text="客户编码: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        code_var = ttk.Entry(code_frame, font=dialog.fonts['normal'])
        # 自动生成客户编号，格式为XTZZKH年月日时分
        from datetime import datetime
        current_time = datetime.now()
        auto_code = f"XTZZKH{current_time.strftime('%Y%m%d%H%M')}"
        code_var.insert(0, auto_code)
        code_var.config(state="readonly")  # 设置为只读，不允许用户修改
        code_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 联系人
        contact_frame = ttk.Frame(dialog.main_frame)
        contact_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(contact_frame, text="联系人: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        contact_var = ttk.Entry(contact_frame, font=dialog.fonts['normal'])
        # 如果提供了客户名称，自动填充为联系人
        if customer_name:
            contact_var.insert(0, customer_name)
        contact_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 电话
        phone_frame = ttk.Frame(dialog.main_frame)
        phone_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(phone_frame, text="电话: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        phone_var = ttk.Entry(phone_frame, font=dialog.fonts['normal'])
        phone_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 邮箱
        email_frame = ttk.Frame(dialog.main_frame)
        email_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(email_frame, text="邮箱: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        email_var = ttk.Entry(email_frame, font=dialog.fonts['normal'])
        email_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 地址
        address_frame = ttk.Frame(dialog.main_frame)
        address_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(address_frame, text="地址: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        address_var = ttk.Entry(address_frame, font=dialog.fonts['normal'])
        address_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(dialog.main_frame)
        desc_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(desc_frame, text="描述: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        desc_var = ttk.Entry(desc_frame, font=dialog.fonts['normal'])
        desc_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                customer_code = code_var.get().strip()
                contact_person = contact_var.get().strip()
                phone = phone_var.get().strip()
                email = email_var.get().strip()
                address = address_var.get().strip()
                description = desc_var.get().strip()
                
                # 验证输入
                if not customer_code:
                    messagebox.showerror("错误", "客户编码不能为空！")
                    return
                    
                # 验证手机号格式
                if phone and not self.validate_phone(phone):
                    messagebox.showerror("错误", "请输入正确的手机号码！手机号码应为11位数字，以1开头。")
                    return
                
                # 连接数据库添加客户
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                try:
                    if total_amount is not None:
                        # 检查客户是否已存在
                        cursor.execute("SELECT contact_person FROM customers WHERE contact_person = ?", (contact_person,))
                        existing_customer = cursor.fetchone()
                        
                        if existing_customer:
                            # 客户已存在，不做处理
                            conn.close()
                            # 刷新客户列表
                            self.refresh_customer_list()
                            dialog.destroy()
                        else:
                            # 客户不存在，添加客户
                            cursor.execute(
                                "INSERT INTO customers (customer_code, name, contact_person, phone, email, description) VALUES (?, ?, ?, ?, ?, ?)",
                                (customer_code, contact_person, contact_person, phone, email, description)
                            )
                            conn.commit()
                            conn.close()
                            
                            # 先刷新客户列表，确保数据已写入
                            self.refresh_customer_list()
                            # 添加短暂延迟确保刷新完成
                            self.root.update_idletasks()
                            
                            dialog.destroy()
                    else:
                        # 正常添加客户
                        cursor.execute(
                            "INSERT INTO customers (customer_code, name, contact_person, phone, email, description) VALUES (?, ?, ?, ?, ?, ?)",
                            (customer_code, contact_person, contact_person, phone, email, description)
                        )
                        conn.commit()
                        conn.close()
                        
                        # 先刷新客户列表，确保数据已写入
                        self.refresh_customer_list()
                        # 添加短暂延迟确保刷新完成
                        self.root.update_idletasks()
                        
                        messagebox.showinfo("成功", "客户添加成功！")
                        dialog.destroy()
                except sqlite3.IntegrityError:
                    conn.close()
                    
                    # 如果是处理销售金额的情况，客户编码已存在则直接关闭对话框
                    if total_amount is not None:
                        self.refresh_customer_list()
                        dialog.destroy()
                    else:
                        # 正常添加客户时，客户编码已存在提供更新选项
                        if messagebox.askyesno("提示", "客户编码已存在，是否更新该客户的信息？"):
                            try:
                                # 连接数据库更新客户信息
                                conn = sqlite3.connect(self.db_path)
                                cursor = conn.cursor()
                                # 修复：添加name字段的更新，移除不存在的address字段
                                cursor.execute(
                                    "UPDATE customers SET name=?, contact_person=?, phone=?, email=?, description=? WHERE customer_code=?",
                                    (contact_person, contact_person, phone, email, description, customer_code)
                                )
                                conn.commit()
                                conn.close()
                                
                                # 先刷新客户列表，确保数据已更新
                                self.refresh_customer_list()
                                # 添加短暂延迟确保刷新完成
                                self.root.update_idletasks()
                                
                                messagebox.showinfo("成功", "客户信息更新成功！")
                                dialog.destroy()
                            except Exception as e:
                                conn.close()
                                messagebox.showerror("错误", f"更新客户信息失败：{str(e)}")
                except Exception as e:
                    conn.close()
                    messagebox.showerror("错误", f"添加客户失败：{str(e)}")
            except Exception as e:
                messagebox.showerror("错误", f"添加客户失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10)
    
    def edit_customer(self):
        """修改客户"""
        # 获取选中的客户
        selected_item = self.customer_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个客户！")
            return
        
        # 获取客户ID（从item的iid中获取）
        customer_id = selected_item[0]
        
        # 连接数据库获取客户详情
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT customer_code, contact_person, phone, email, address, description FROM customers WHERE id=?",
            (customer_id,)
        )
        customer = cursor.fetchone()
        conn.close()
        
        if not customer:
            messagebox.showerror("错误", "找不到指定的客户！")
            return
        
        # 创建修改客户对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "修改客户", width_percent=0.7, height_percent=0.7)
        
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 15
        
        # 客户编码
        code_frame = ttk.Frame(dialog.main_frame)
        code_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(code_frame, text="客户编码: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        code_var = ttk.Entry(code_frame, font=dialog.fonts['normal'])
        code_var.insert(0, customer[0])
        code_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 联系人
        contact_frame = ttk.Frame(dialog.main_frame)
        contact_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(contact_frame, text="联系人: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        contact_var = ttk.Entry(contact_frame, font=dialog.fonts['normal'])
        contact_var.insert(0, customer[1] if customer[1] else "")
        contact_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 电话
        phone_frame = ttk.Frame(dialog.main_frame)
        phone_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(phone_frame, text="电话: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        phone_var = ttk.Entry(phone_frame, font=dialog.fonts['normal'])
        phone_var.insert(0, customer[2] if customer[2] else "")
        phone_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 邮箱
        email_frame = ttk.Frame(dialog.main_frame)
        email_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(email_frame, text="邮箱: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        email_var = ttk.Entry(email_frame, font=dialog.fonts['normal'])
        email_var.insert(0, customer[3] if customer[3] else "")
        email_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 地址
        address_frame = ttk.Frame(dialog.main_frame)
        address_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(address_frame, text="地址: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        address_var = ttk.Entry(address_frame, font=dialog.fonts['normal'])
        address_var.insert(0, customer[4] if customer[4] else "")
        address_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(dialog.main_frame)
        desc_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(desc_frame, text="描述: ", width=label_width, font=dialog.fonts['normal']).pack(side="left")
        desc_var = ttk.Entry(desc_frame, font=dialog.fonts['normal'])
        desc_var.insert(0, customer[5] if customer[5] else "")
        desc_var.pack(side="left", padx=5, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                customer_code = code_var.get().strip()
                contact_person = contact_var.get().strip()
                phone = phone_var.get().strip()
                email = email_var.get().strip()
                address = address_var.get().strip()
                description = desc_var.get().strip()
                
                # 验证输入
                if not customer_code:
                    messagebox.showerror("错误", "客户编码不能为空！")
                    return

                # 验证手机号格式
                if phone and not self.validate_phone(phone):
                    messagebox.showerror("错误", "请输入正确的手机号码！手机号码应为11位数字，以1开头。")
                    return

                # 连接数据库更新客户
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                try:
                    # 检查客户编码是否被其他客户使用
                    cursor.execute("SELECT id FROM customers WHERE customer_code=? AND id != ?", (customer_code, customer_id))
                    if cursor.fetchone():
                        conn.close()
                        messagebox.showerror("错误", "客户编码已被其他客户使用！")
                        return
                    
                    # 修复：添加name字段的更新，移除不存在的updated_at和address字段
                    cursor.execute(
                        "UPDATE customers SET customer_code=?, name=?, contact_person=?, phone=?, email=?, description=? WHERE id=?",
                        (customer_code, contact_person, contact_person, phone, email, description, customer_id)
                    )
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("成功", "客户修改成功！")
                    dialog.destroy()
                    self.refresh_customer_list()
                except Exception as e:
                    conn.close()
                    messagebox.showerror("错误", f"修改客户失败：{str(e)}")
            except Exception as e:
                messagebox.showerror("错误", f"修改客户失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=10)
    
    def delete_customer(self):
        """删除客户"""
        # 获取选中的客户
        selected_item = self.customer_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个客户！")
            return
        
        # 获取客户ID（从item的iid中获取）和客户编码
        customer_id = selected_item[0]
        item_values = self.customer_tree.item(selected_item[0])["values"]
        customer_code = item_values[0]  # 客户编码是索引0
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除客户 '{customer_code}' 吗？"):
            return
        
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除客户
            cursor.execute(
                "DELETE FROM customers WHERE id=?",
                (customer_id,)
            )
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "客户删除成功！")
            self.refresh_customer_list()
        except Exception as e:
            messagebox.showerror("错误", f"删除客户失败：{str(e)}")
    
    def init_profit_frame(self):
        """初始化利润报表页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.profit_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # 日期范围选择
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(side="left", padx=5)
        
        ttk.Label(date_frame, text="起始日期: ").pack(side="left")
        self.profit_start_date_var = tk.StringVar(value=(datetime.date.today().replace(day=1)).strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.profit_start_date_var, width=12).pack(side="left", padx=5)
        
        ttk.Label(date_frame, text="结束日期: ").pack(side="left")
        self.profit_end_date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.profit_end_date_var, width=12).pack(side="left", padx=5)
        
        ttk.Button(date_frame, text="查询利润", command=self.query_profit).pack(side="left", padx=5)
        
        # 产品利润明细
        detail_frame = ttk.LabelFrame(main_frame, text="产品利润明细")
        detail_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("product_name", "sale_quantity", "purchase_cost", "sale_revenue", "product_profit", "product_profit_rate")
        self.profit_tree = ttk.Treeview(detail_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.profit_tree.heading("product_name", text="产品名称")
        self.profit_tree.heading("sale_quantity", text="销售数量")
        self.profit_tree.heading("purchase_cost", text="进货成本")
        self.profit_tree.heading("sale_revenue", text="销售收入")
        self.profit_tree.heading("product_profit", text="产品利润")
        self.profit_tree.heading("product_profit_rate", text="产品利润率")
        
        # 设置列宽
        self.profit_tree.column("product_name", width=150)
        self.profit_tree.column("sale_quantity", width=100, anchor="center")
        self.profit_tree.column("purchase_cost", width=100, anchor="center")
        self.profit_tree.column("sale_revenue", width=100, anchor="center")
        self.profit_tree.column("product_profit", width=100, anchor="center")
        self.profit_tree.column("product_profit_rate", width=100, anchor="center")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(detail_frame, orient="vertical", command=self.profit_tree.yview)
        self.profit_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.profit_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 初始查询利润数据
        self.query_profit()
    
    def query_profit(self):
        """查询利润数据"""
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
        
        # 连接数据库查询利润数据
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 清空利润明细列表
            for item in self.profit_tree.get_children():
                self.profit_tree.delete(item)
            
            # 连接数据库查询利润数据 - 仅用于产品利润明细
            
            # 查询产品利润明细
            # 这里我们需要计算每个产品的销售数量、销售金额、进货成本和利润
            # 由于销售记录中可能没有直接关联进货成本，我们使用产品表中的进货价格作为参考
            cursor.execute("""
                SELECT pr.name, 
                       SUM(s.quantity) as sale_quantity,
                       SUM(s.quantity * pr.purchase_price) as purchase_cost,
                       SUM(s.total_amount) as sale_revenue,
                       (SUM(s.total_amount) - SUM(s.quantity * pr.purchase_price)) as product_profit
                FROM sales s
                JOIN products pr ON s.product_id = pr.id
                WHERE s.sale_date BETWEEN ? AND ?
                GROUP BY pr.id
                ORDER BY product_profit DESC
            """, (start_date, end_date))
            
            product_profits = cursor.fetchall()
            
            # 初始化累计变量
            total_purchase_cost = 0
            total_sale_revenue = 0
            total_product_profit = 0
            
            # 添加到Treeview并累计计算
            for product_profit in product_profits:
                product_name, sale_quantity, purchase_cost, sale_revenue, product_profit_value = product_profit
                product_profit_rate = (product_profit_value / sale_revenue * 100) if sale_revenue > 0 else 0
                
                # 累计计算
                total_purchase_cost += purchase_cost
                total_sale_revenue += sale_revenue
                total_product_profit += product_profit_value
                
                self.profit_tree.insert("", "end",
                    values=(product_name, 
                            sale_quantity, 
                            f"{purchase_cost:.2f}", 
                            f"{sale_revenue:.2f}", 
                            f"{product_profit_value:.2f}", 
                            f"{product_profit_rate:.2f}%"))
            
            # 添加总计行
            if product_profits:
                self.profit_tree.insert("", "end",
                    values=("总计", 
                            "", 
                            f"{total_purchase_cost:.2f}", 
                            f"{total_sale_revenue:.2f}", 
                            f"{total_product_profit:.2f}", 
                            ""))
            # 如果没有数据，显示空记录
            else:
                self.profit_tree.insert("", "end", values=("暂无数据", "", "", "", "", ""))
                
        except Exception as e:
            messagebox.showerror("错误", f"查询利润数据失败：{str(e)}")
        finally:
            conn.close()