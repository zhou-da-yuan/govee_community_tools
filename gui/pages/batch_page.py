# govee_community_tool/gui/pages/batch_page.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gui.widgets.log_text import LogText
from utils.file_loader import load_accounts
from core.auth import login
from core.operations import execute_operation
from core.session_manager import SessionManager
import threading
import random
import time
import os


class BatchOperationsPage(ttk.Frame):
    def __init__(self, parent, initial_accounts, total_count, current_env, change_env_callback):
        super().__init__(parent)
        self.accounts = initial_accounts.copy()
        self.total_accounts = total_count
        self.current_env = current_env
        self.change_env_callback = change_env_callback
        self.session_manager = SessionManager()

        self.op_map = {k: v["name"] for k, v in self.get_operations().items()}
        self.setup_ui()

    def get_operations(self):
        from core.operations import OPERATIONS
        return OPERATIONS

    def setup_ui(self):
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info_frame, text=f"📦 账号总数: {self.total_accounts}", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        op_frame = ttk.LabelFrame(self, text="选择操作类型", padding=10)
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

        input_frame = ttk.LabelFrame(self, text="参数设置", padding=15)
        input_frame.pack(fill=tk.X, pady=10)

        tk.Label(input_frame, text="目标ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.target_id_entry = tk.Entry(input_frame, width=30, font=("Consolas", 10))
        self.target_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="使用账号数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.num_accounts_entry = tk.Entry(input_frame, width=30, font=("Consolas", 10))
        self.num_accounts_entry.insert(0, str(min(5, self.total_accounts)))
        self.num_accounts_entry.grid(row=1, column=1, padx=5, pady=5)

        # 添加延迟设置
        tk.Label(input_frame, text="延迟 (最小秒):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.min_delay_entry = tk.Entry(input_frame, width=10, font=("Consolas", 10))
        self.min_delay_entry.insert(0, "2")
        self.min_delay_entry.grid(row=2, column=1, sticky=tk.W, padx=5)

        tk.Label(input_frame, text="延迟 (最大秒):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.max_delay_entry = tk.Entry(input_frame, width=10, font=("Consolas", 10))
        self.max_delay_entry.insert(0, "5")
        self.max_delay_entry.grid(row=3, column=1, sticky=tk.W, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="📁 选择账号文件", command=self.select_account_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="▶️ 开始运行", style="Accent.TButton",
                   command=self.start_operation).pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(self, text="运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_widget = LogText(log_frame, height=15)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        self.log(f"✅ 已加载 {self.total_accounts} 个账号。当前环境: {self.current_env.upper()}")

    def log(self, message):
        self.log_widget.log(message)

    def select_account_file(self):
        path = filedialog.askopenfilename(title="选择账号文件", filetypes=[("JSON files", "*.json")])
        if path:
            accounts = load_accounts(path)
            if accounts:
                self.accounts = accounts
                self.total_accounts = len(accounts)
                self.log(f"✅ 成功加载 {self.total_accounts} 个账号：{os.path.basename(path)}")
            else:
                messagebox.showerror("❌ 加载失败", "账号文件格式错误或为空！")

    def start_operation(self):
        choice = self.choice_var.get()
        target_id = self.target_id_entry.get().strip()
        num_input = self.num_accounts_entry.get().strip()

        # 获取延迟
        try:
            min_delay = float(self.min_delay_entry.get().strip())
            max_delay = float(self.max_delay_entry.get().strip())
            if min_delay < 0 or max_delay < 0 or min_delay > max_delay:
                raise ValueError
        except:
            messagebox.showwarning("⚠️ 警告", "延迟必须为非负数，且最小 ≤ 最大！")
            return

        if not target_id:
            messagebox.showwarning("⚠️ 警告", "请输入目标ID！")
            return
        try:
            num_accounts = min(int(num_input), self.total_accounts)
            if num_accounts <= 0:
                raise ValueError
        except:
            messagebox.showwarning("⚠️ 警告", "账号数量必须是正整数！")
            return

        selected_accounts = self.accounts[:num_accounts]
        op_name = self.op_map[choice]
        self.log(f"🚀 开始执行: {op_name} | ID: {target_id} | 账号数: {num_accounts}")
        self.log(f"⏱️  操作延迟: {min_delay:.1f} ~ {max_delay:.1f} 秒")

        thread = threading.Thread(
            target=self.run_operation,
            args=(choice, op_name, target_id, selected_accounts, min_delay, max_delay),
            daemon=True
        )
        thread.start()

    def run_operation(self, op_key, op_name, target_id, accounts, min_delay, max_delay):
        success_count = 0
        base_url = self.get_base_url()

        for idx, acc in enumerate(accounts, 1):
            self.log(f"--- [{idx}/{len(accounts)}] 账号: {acc['email']} ---")
            try:
                token = login(self.session_manager, acc['email'], acc['password'], base_url)
                self.log("✅ 登录成功")
                if execute_operation(op_key, self.session_manager, token, target_id, base_url):
                    success_count += 1
                    self.log(f"✅ {op_name} 成功")
                else:
                    self.log(f"❌ {op_name} 失败")
                # 👇 使用传入的延迟
                delay = random.uniform(min_delay, max_delay)
                self.log(f"⏸️  等待 {delay:.1f} 秒...")
                time.sleep(delay)
            except Exception as e:
                self.log(f"🚫 错误: {str(e)}")
                continue

        self.log(f"\n🎉 完成！共 {len(accounts)} 个账号，成功 {success_count} 次。\n")

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.log(f"🔄 环境已切换至: {new_env.upper()}")