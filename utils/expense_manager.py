import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

# 导入自适应对话框类
from salary_calculator import AdaptiveDialog

class ExpenseManager:
    def __init__(self, db_path, root, notebook, user_role):
        self.db_path = db_path
        self.root = root
        self.notebook = notebook
        self.user_role = user_role
        
        # 创建支出管理标签页
        self.expense_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.expense_frame, text="支出管理")
        
        # 如果不是管理员，隐藏支出管理标签页
        if self.user_role != 'admin':
            self.notebook.hide(self.expense_frame)
        else:
            self.init_expense_frame()

    def init_expense_frame(self):
        # 创建主框架
        main_frame = ttk.Frame(self.expense_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加支出按钮
        ttk.Button(control_frame, text="添加支出", command=self.add_expense).pack(side=tk.LEFT, padx=5)
        
        # 删除支出按钮
        ttk.Button(control_frame, text="删除支出", command=self.delete_expense_record).pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_expense_list).pack(side=tk.LEFT, padx=5)
        
        # 日期范围选择
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(date_frame, text="起始日期: ").pack(side=tk.LEFT)
        self.expense_start_date_var = tk.StringVar(value=(datetime.date.today().replace(day=1)).strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.expense_start_date_var, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(date_frame, text="结束日期: ").pack(side=tk.LEFT)
        self.expense_end_date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.expense_end_date_var, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(date_frame, text="查询", command=self.refresh_expense_list).pack(side=tk.LEFT, padx=5)
        
        # 支出列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("id", "date", "category", "amount", "description", "added_by")
        self.expense_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.expense_tree.heading("id", text="ID")
        self.expense_tree.heading("date", text="日期")
        self.expense_tree.heading("category", text="类别")
        self.expense_tree.heading("amount", text="金额")
        self.expense_tree.heading("description", text="描述")
        self.expense_tree.heading("added_by", text="添加人")
        
        # 设置列宽
        self.expense_tree.column("id", width=50)
        self.expense_tree.column("date", width=120)
        self.expense_tree.column("category", width=120)
        self.expense_tree.column("amount", width=100, anchor=tk.E)
        self.expense_tree.column("description", width=250)
        self.expense_tree.column("added_by", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.expense_tree.yview)
        self.expense_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.expense_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件，编辑支出记录
        self.expense_tree.bind("<Double-1>", lambda event: self.edit_expense())
        
        # 刷新支出列表
        self.refresh_expense_list()

    def refresh_expense_list(self):
        # 清空Treeview
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        
        # 获取日期范围
        start_date = self.expense_start_date_var.get()
        end_date = self.expense_end_date_var.get()
        
        try:
            # 验证日期格式
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
            return
        
        # 连接数据库获取支出记录
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, date, category, amount, description, added_by 
               FROM expenses 
               WHERE date BETWEEN ? AND ? 
               ORDER BY date DESC""",
            (start_date, end_date)
        )
        expense_records = cursor.fetchall()
        conn.close()
        
        # 添加到Treeview
        total_amount = 0
        for record in expense_records:
            id, date, category, amount, description, added_by = record
            self.expense_tree.insert("", tk.END,
                values=(id, date, category, amount, description, added_by))
            total_amount += amount
        
        # 显示总计
        self.expense_tree.insert("", tk.END,
            values=("", "总计", "", total_amount, "", ""))

    def add_expense(self):
        # 创建添加支出对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "添加支出", width_percent=0.6, height_percent=0.5)
        
        # 日期
        date_frame = ttk.Frame(dialog.main_frame)
        date_frame.pack(fill=tk.X, padx=10, pady=8)
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 15
        ttk.Label(date_frame, text="日期: ", width=label_width, font=dialog.fonts['normal']).pack(side=tk.LEFT)
        date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=date_var, font=dialog.fonts['normal']).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 类别
        category_frame = ttk.Frame(dialog.main_frame)
        category_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(category_frame, text="类别: ", width=label_width, font=dialog.fonts['normal']).pack(side=tk.LEFT)
        category_var = tk.StringVar(value="办公用品")
        category_combo = ttk.Combobox(category_frame, textvariable=category_var, 
            values=["办公用品", "水电费", "租金", "薪资福利", "差旅费", "业务招待费", "其他"], state="readonly", font=dialog.fonts['normal'])
        category_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 金额
        amount_frame = ttk.Frame(dialog.main_frame)
        amount_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(amount_frame, text="金额: ", width=label_width, font=dialog.fonts['normal']).pack(side=tk.LEFT)
        amount_var = tk.DoubleVar()
        ttk.Entry(amount_frame, textvariable=amount_var, font=dialog.fonts['normal']).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(dialog.main_frame)
        desc_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(desc_frame, text="描述: ", width=label_width, font=dialog.fonts['normal']).pack(side=tk.LEFT)
        desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=desc_var, font=dialog.fonts['normal']).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                date = date_var.get().strip()
                category = category_var.get()
                amount = amount_var.get()
                description = desc_var.get().strip()
                added_by = "admin"  # 这里应该从当前登录用户获取
                
                # 验证输入
                if not date:
                    messagebox.showerror("错误", "日期不能为空！")
                    return
                
                if amount <= 0:
                    messagebox.showerror("错误", "金额必须大于0！")
                    return
                
                # 验证日期格式
                try:
                    datetime.datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                    return
                
                # 保存到数据库
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO expenses (date, category, amount, description, added_by) VALUES (?, ?, ?, ?, ?)",
                    (date, category, amount, description, added_by)
                )
                conn.commit()
                conn.close()
                
                messagebox.showinfo("成功", "支出添加成功！")
                dialog.destroy()
                self.refresh_expense_list()
            except Exception as e:
                messagebox.showerror("错误", f"添加支出失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def edit_expense(self):
        # 获取选中的支出记录
        selected_item = self.expense_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条支出记录！")
            return
        
        # 获取记录值
        item_values = self.expense_tree.item(selected_item[0])["values"]
        expense_id = item_values[0]
        current_date = item_values[1]
        current_category = item_values[2]
        current_amount = item_values[3]
        current_description = item_values[4]
        
        # 检查是否是总计行
        if not expense_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 创建编辑支出对话框 - 使用自适应对话框类
        dialog = AdaptiveDialog(self.root, "编辑支出记录", width_percent=0.6, height_percent=0.5)
        
        # 日期
        date_frame = ttk.Frame(dialog.main_frame)
        date_frame.pack(fill=tk.X, padx=10, pady=8)
        # 为标签设置合适的宽度
        label_width = 12 if dialog.winfo_width() < 500 else 15
        ttk.Label(date_frame, text="日期: ", width=label_width, font=dialog.fonts['normal']).pack(side=tk.LEFT)
        date_var = tk.StringVar(value=current_date)
        ttk.Entry(date_frame, textvariable=date_var, font=dialog.fonts['normal']).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 类别
        category_frame = ttk.Frame(dialog.main_frame)
        category_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(category_frame, text="类别: ", width=label_width, font=dialog.fonts['normal']).pack(side=tk.LEFT)
        category_var = tk.StringVar(value=current_category)
        category_combo = ttk.Combobox(category_frame, textvariable=category_var, 
            values=["办公用品", "水电费", "租金", "薪资福利", "差旅费", "业务招待费", "其他"], state="readonly", font=dialog.fonts['normal'])
        category_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 金额
        amount_frame = ttk.Frame(dialog.main_frame)
        amount_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(amount_frame, text="金额: ", width=label_width, font=dialog.fonts['normal']).pack(side=tk.LEFT)
        amount_var = tk.DoubleVar(value=current_amount)
        ttk.Entry(amount_frame, textvariable=amount_var, font=dialog.fonts['normal']).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(dialog.main_frame)
        desc_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(desc_frame, text="描述: ", width=label_width, font=dialog.fonts['normal']).pack(side=tk.LEFT)
        desc_var = tk.StringVar(value=current_description)
        ttk.Entry(desc_frame, textvariable=desc_var, font=dialog.fonts['normal']).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog.main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=15)
        
        # 确认按钮
        def confirm():
            try:
                date = date_var.get().strip()
                category = category_var.get()
                amount = amount_var.get()
                description = desc_var.get().strip()
                
                # 验证输入
                if not date:
                    messagebox.showerror("错误", "日期不能为空！")
                    return
                
                if amount <= 0:
                    messagebox.showerror("错误", "金额必须大于0！")
                    return
                
                # 验证日期格式
                try:
                    datetime.datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("错误", "日期格式必须是 YYYY-MM-DD！")
                    return
                
                # 更新数据库
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE expenses 
                    SET date=?, category=?, amount=?, description=? 
                    WHERE id=?""",
                    (date, category, amount, description, expense_id)
                )
                conn.commit()
                conn.close()
                
                messagebox.showinfo("成功", "支出记录更新成功！")
                dialog.destroy()
                self.refresh_expense_list()
            except Exception as e:
                messagebox.showerror("错误", f"更新支出记录失败：{str(e)}")
        
        ttk.Button(button_frame, text="确认", command=confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def delete_expense_record(self):
        # 获取选中的支出记录
        selected_item = self.expense_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一条支出记录！")
            return
        
        # 获取记录ID
        item_values = self.expense_tree.item(selected_item[0])["values"]
        expense_id = item_values[0]
        
        # 检查是否是总计行
        if not expense_id:
            messagebox.showinfo("提示", "不能选择总计行！")
            return
        
        # 确认删除
        if messagebox.askyesno("确认", "确定要删除这条支出记录吗？"):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("成功", "支出记录已删除！")
                self.refresh_expense_list()
            except Exception as e:
                messagebox.showerror("错误", f"删除支出记录失败：{str(e)}")