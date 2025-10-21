# govee_community_tool/gui/pages/history_page.py

import tkinter as tk
from tkinter import ttk, messagebox
from utils.history import get_all_history, clear_history
from datetime import datetime


class OperationHistoryPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.history_data = {}
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        # 标题 + 按钮
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=10)

        ttk.Label(header, text="📅 操作历史记录", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(header, text="🗑️ 清空今日", command=self.clear_today).pack(side=tk.RIGHT)
        # 新增：清空所有记录按钮
        ttk.Button(header, text="🗑️ 清空全部", command=self.clear_all_history).pack(side=tk.RIGHT)

        # 表格
        self.tree = ttk.Treeview(self, columns=("time", "op", "email", "target", "result", "env", "details"),
                                 show="headings", height=25)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # 列定义
        cols = [
            ("time", "日期时间", 120),
            ("op", "操作", 80),
            ("email", "账号", 120),
            ("target", "目标ID", 60),
            ("result", "结果", 40),
            ("env", "环境", 40),
            ("details", "详情", 220)
        ]
        for col, text, width in cols:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width)

        # 滚动条
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

    def load_history(self):
        self.history_data = get_all_history()
        self.tree.delete(*self.tree.get_children())

        # 收集所有记录用于排序
        all_records = []
        for date, records in self.history_data.items():
            for rec in records:
                all_records.append(rec)

        # 按时间逆序排序：最新的在最上面
        all_records.sort(key=lambda x: x["timestamp"], reverse=True)

        # 插入到表格
        for rec in all_records:
            tag = "success" if rec["result"] == "success" else "failed"
            self.tree.insert("", tk.END, values=(
                rec["timestamp"].split('.')[0].replace('T', ' '),  # 格式化为 "2025-09-26 14:30:25"
                rec["operation"],
                rec["email"],
                rec["target_id"],
                "✅ 成功" if rec["result"] == "success" else "❌ 失败",
                (str(rec.get("env") or "")).upper(),  # 防止为记录到环境报错
                rec["details"]
            ), tags=(tag,))

        # 颜色
        self.tree.tag_configure("success", foreground="green")
        self.tree.tag_configure("failed", foreground="red")

    def clear_today(self):
        if messagebox.askyesno("确认", "是否清空【今日】操作历史？"):
            clear_history()
            self.load_history()
            messagebox.showinfo("✅ 已清空", "今日历史记录已清除。")

    def clear_all_history(self):
        if messagebox.askyesno("确认", "是否清空【所有】操作历史？"):
            from utils.history import clear_all_history
            clear_all_history()
            self.load_history()
            messagebox.showinfo("✅ 已清空", "所有历史记录已清除。")
