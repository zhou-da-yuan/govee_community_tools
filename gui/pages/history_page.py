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

        # 表格
        self.tree = ttk.Treeview(self, columns=("time", "op", "email", "target", "result", "env", "details"), show="headings", height=25)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # 列定义
        cols = [
            ("time", "时间", 100),
            ("op", "操作", 120),
            ("email", "账号", 180),
            ("target", "目标ID", 100),
            ("result", "结果", 80),
            ("env", "环境", 80),
            ("details", "详情", 150)
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

        for date, records in self.history_data.items():
            for rec in records:
                tag = "success" if rec["result"] == "success" else "failed"
                self.tree.insert("", tk.END, values=(
                    rec["time"],
                    rec["operation"],
                    rec["email"],
                    rec["target_id"],
                    "✅ 成功" if rec["result"]=="success" else "❌ 失败",
                    rec["env"].upper(),
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