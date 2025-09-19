# govee_community_tool/gui/pages/single_account.py

import tkinter as tk
from tkinter import ttk, messagebox
from gui.widgets.log_text import LogText
from core.auth import login
from core.operations import execute_operation
from core.session_manager import SessionManager
import threading
import time


class SingleAccountOperationsPage(ttk.Frame):
    def __init__(self, parent, current_env, change_env_callback):
        super().__init__(parent)
        self.current_env = current_env
        self.change_env_callback = change_env_callback
        self.session_manager = SessionManager()
        self.op_map = {k: v["name"] for k, v in self.get_operations().items()}
        self.setup_ui()

    def get_operations(self):
        from core.operations import OPERATIONS
        return OPERATIONS

    def setup_ui(self):
        # 账号输入区
        account_frame = ttk.LabelFrame(self, text="👤 单账号信息", padding=15)
        account_frame.pack(fill=tk.X, pady=10)

        tk.Label(account_frame, text="邮箱:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.email_entry = tk.Entry(account_frame, width=40, font=("Consolas", 10))
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(account_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.password_entry = tk.Entry(account_frame, width=40, font=("Consolas", 10), show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        # 操作选择
        op_frame = ttk.LabelFrame(self, text="⚙️ 选择操作", padding=10)
        op_frame.pack(fill=tk.X, pady=10)

        self.choice_var = tk.StringVar(value="complaint_topic")
        row, col = 0, 0
        for key, name in self.op_map.items():
            tk.Radiobutton(op_frame, text=name, variable=self.choice_var, value=key).grid(
                row=row, column=col, sticky=tk.W, padx=15, pady=5)
            col += 1
            if col > 2:
                col = 0
                row += 1

        # 参数输入
        param_frame = ttk.LabelFrame(self, text="🎯 参数设置", padding=15)
        param_frame.pack(fill=tk.X, pady=10)

        tk.Label(param_frame, text="目标ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.target_id_entry = tk.Entry(param_frame, width=30, font=("Consolas", 10))
        self.target_id_entry.grid(row=0, column=1, padx=5, pady=5)

        # 按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="▶️ 执行操作", style="Accent.TButton",
                   command=self.start_operation).pack(side=tk.LEFT, padx=5)

        # 日志
        log_frame = ttk.LabelFrame(self, text="📝 运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_widget = LogText(log_frame, height=18)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        self.log("✅ 请填写账号信息并选择操作类型。")

    def log(self, message):
        self.log_widget.log(message)

    def start_operation(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        target_id = self.target_id_entry.get().strip()
        op_key = self.choice_var.get()

        if not email or not password:
            messagebox.showwarning("⚠️ 警告", "请输入邮箱和密码！")
            return
        if not target_id:
            messagebox.showwarning("⚠️ 警告", "请输入目标ID！")
            return

        op_name = self.op_map[op_key]
        self.log(f"🚀 开始执行: {op_name} | 账号: {email} | ID: {target_id}")

        thread = threading.Thread(
            target=self.run_operation,
            args=(email, password, op_key, op_name, target_id),
            daemon=True
        )
        thread.start()

    def run_operation(self, email, password, op_key, op_name, target_id):
        base_url = self.get_base_url()

        try:
            token = login(self.session_manager, email, password, base_url)
            self.log("✅ 登录成功")
            time.sleep(1)

            if execute_operation(op_key, self.session_manager, token, target_id, base_url):
                self.log(f"✅ 【{op_name}】执行成功！")
            else:
                self.log(f"❌ 【{op_name}】执行失败！")
        except Exception as e:
            self.log(f"🚫 错误: {str(e)}")

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.log(f"🔄 环境已切换至: {new_env.upper()}")