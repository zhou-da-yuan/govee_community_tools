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

# 👉 导入 SimpleLogger
from utils.logger import SimpleLogger


class BatchOperationsPage(ttk.Frame):
    def __init__(self, parent, initial_accounts, total_count, current_env, change_env_callback):
        super().__init__(parent)
        self.accounts = initial_accounts.copy()
        self.total_accounts = total_count
        self.current_env = current_env
        self.change_env_callback = change_env_callback
        self.session_manager = SessionManager()

        self.op_map = {k: v["name"] for k, v in self.get_operations().items()}
        self.op_map.pop("create_post")

        # 👉 创建 logger 实例（关键改动）
        self.logger = None  # 延迟绑定，在 setup_ui 后赋值

        self.setup_ui()

        # ✅ 初始化 logger 并连接 log_widget
        self.logger = SimpleLogger(log_func=self.log_widget._log)
        self.logger.info(f"✅ 已加载 {self.total_accounts} 个账号。当前环境: {self.current_env.upper()}")

    def get_operations(self):
        from core.operations import OPERATIONS
        return OPERATIONS

    def setup_ui(self):
        self.account_count_var = tk.StringVar(value=f"📦 当前账号数: {self.total_accounts}")

        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info_frame, textvariable=self.account_count_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        # --- 操作类型 ---
        op_frame = ttk.LabelFrame(self, text="选择操作类型", padding=10)
        op_frame.pack(fill=tk.X, pady=10)

        self.choice_var = tk.StringVar(value="complaint_topic")

        radio_frame = ttk.Frame(op_frame)
        radio_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        for i in range(6):
            radio_frame.columnconfigure(i, weight=1)

        row = 0
        for idx, (key, name) in enumerate(self.op_map.items()):
            rb = tk.Radiobutton(
                radio_frame,
                text=name,
                variable=self.choice_var,
                value=key,
                font=("Arial", 9),
                command=self.on_operation_change
            )
            rb.grid(row=row, column=idx, sticky="w", padx=5, pady=3)

        # ===== 参数设置 =====
        input_frame = ttk.LabelFrame(self, text="参数设置", padding=10)
        input_frame.pack(fill=tk.X, pady=10)

        # 配置列：支持四列布局
        input_frame.columnconfigure(0, weight=0)  # 标签1
        input_frame.columnconfigure(1, weight=1)  # 输入1
        input_frame.columnconfigure(2, weight=0)  # 标签2 (评论)
        input_frame.columnconfigure(3, weight=2)  # 输入2 (评论内容)

        # ===== 第一行：目标ID + 评论内容 =====
        tk.Label(input_frame, text="目标ID:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=3)
        self.target_id_entry = tk.Entry(input_frame, width=18, font=("Consolas", 10))
        self.target_id_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5), pady=3)

        self.comment_label = tk.Label(input_frame, text="评论内容:", font=("Arial", 9))
        self.comment_content_entry = tk.Entry(input_frame, width=40, font=("Consolas", 10))
        self.comment_content_entry.insert(0, "This is the default comment content for testing")

        # 初始隐藏
        self.comment_label.grid_remove()
        self.comment_content_entry.grid_remove()

        # ===== 第二行：使用账号数 =====
        tk.Label(input_frame, text="使用账号数:", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, padx=(0, 5),
                                                                          pady=3)
        self.num_accounts_entry = tk.Entry(input_frame, width=8, font=("Consolas", 10))
        self.num_accounts_entry.insert(0, str(min(5, self.total_accounts)))
        self.num_accounts_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 5), pady=3)

        # ===== 第三行：延迟 (最小秒) =====
        tk.Label(input_frame, text="延迟 (最小秒):", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, padx=(0, 5),
                                                                             pady=3)
        self.min_delay_entry = tk.Entry(input_frame, width=6, font=("Consolas", 10))
        self.min_delay_entry.insert(0, "2")
        self.min_delay_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 5), pady=3)

        # ===== 第四行：延迟 (最大秒) =====
        tk.Label(input_frame, text="延迟 (最大秒):", font=("Arial", 9)).grid(row=3, column=0, sticky=tk.W, padx=(0, 5),
                                                                             pady=3)
        self.max_delay_entry = tk.Entry(input_frame, width=6, font=("Consolas", 10))
        self.max_delay_entry.insert(0, "5")
        self.max_delay_entry.grid(row=3, column=1, sticky=tk.W, padx=(0, 5), pady=3)

        # ===== 按钮区域 =====
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="📁 选择账号文件", command=self.select_account_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="▶️ 开始运行", style="Accent.TButton", command=self.start_operation).pack(
            side=tk.LEFT, padx=5)

        # ===== 日志区域 =====
        log_frame = ttk.LabelFrame(self, text="运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_widget = LogText(log_frame, height=20)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def on_operation_change(self):
        """根据选择的操作显示/隐藏评论内容整组"""
        choice = self.choice_var.get()
        if choice == "comment_post":
            self.comment_label.grid(row=0, column=2, sticky=tk.W, padx=(15, 5), pady=3)  # 左对齐，适当间距
            self.comment_content_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 0), pady=3)  # 紧贴标签
        else:
            self.comment_label.grid_remove()
            self.comment_content_entry.grid_remove()

    # 👉 替代原 log 方法：使用 logger.info/debug/error
    def log(self, message, level="info"):
        getattr(self.logger, level)(message)

    def select_account_file(self):
        path = filedialog.askopenfilename(title="选择账号文件", filetypes=[("JSON files", "*.json")])
        if path:
            accounts = load_accounts(path)
            if accounts:
                self.accounts = accounts
                self.total_accounts = len(accounts)
                self.valid_accounts = []
                self.account_count_var.set(f"📦 当前账号数: {self.total_accounts}")
                self.logger.info(f"✅ 成功加载 {self.total_accounts} 个账号：{os.path.basename(path)}")
            else:
                self.logger.error("❌ 加载失败，账号文件格式错误或为空！")
                messagebox.showerror("❌ 加载失败", "账号文件格式错误或为空！")

    def refresh_accounts(self, new_accounts, total_count):
        self.accounts = new_accounts.copy()
        self.total_accounts = total_count
        self.valid_accounts = []
        self.account_count_var.set(f"📦 当前账号数: {self.total_accounts}")
        self.logger.info(f"🔄 已刷新账号列表，共 {self.total_accounts} 个账号（来自 {self.current_env} 环境）")

    def start_operation(self):
        choice = self.choice_var.get()
        target_id = self.target_id_entry.get().strip()
        num_input = self.num_accounts_entry.get().strip()

        try:
            min_delay = float(self.min_delay_entry.get().strip())
            max_delay = float(self.max_delay_entry.get().strip())
            if min_delay < 0 or max_delay < 0 or min_delay > max_delay:
                raise ValueError
        except Exception:
            messagebox.showwarning("⚠️ 警告", "延迟必须为非负数，且最小 ≤ 最大！")
            return

        if not target_id:
            messagebox.showwarning("⚠️ 警告", "请输入目标ID！")
            return

        try:
            num_accounts = min(int(num_input), self.total_accounts)
            if num_accounts <= 0:
                raise ValueError
        except Exception:
            messagebox.showwarning("⚠️ 警告", "账号数量必须是正整数！")
            return

        selected_accounts = self.accounts[:num_accounts]
        op_name = self.op_map[choice]
        self.logger.info(f"🚀 开始执行: {op_name} | ID: {target_id} | 账号数: {num_accounts}")
        self.logger.info(f"⏱️  操作延迟: {min_delay:.1f} ~ {max_delay:.1f} 秒")

        # 👉 获取评论内容（仅 comment_post 需要）
        extra_kwargs = {}
        if choice == "comment_post":
            content = self.comment_content_entry.get().strip()
            if not content:
                messagebox.showwarning("⚠️ 警告", "评论内容不能为空！")
                return
            extra_kwargs["content"] = content

        thread = threading.Thread(
            target=self.run_operation,
            args=(choice, op_name, target_id, selected_accounts, min_delay, max_delay),
            kwargs=extra_kwargs,  # 传入 content
            daemon=True
        )
        thread.start()

    def run_operation(self, op_key, op_name, target_id, accounts, min_delay, max_delay, **kwargs):
        success_count = 0
        base_url = self.get_base_url()

        for idx, acc in enumerate(accounts, 1):
            self.logger.info(f"--- [{idx}/{len(accounts)}] 账号: {acc['email']} ---")
            try:
                token = login(self.session_manager, acc['email'], acc['password'], base_url)
                self.logger.info("✅ 登录成功")
                # 👉 将 kwargs 传入 execute_operation
                if execute_operation(op_key, self.session_manager, token, base_url, target_id=target_id, **kwargs):
                    success_count += 1
                    self.logger.info(f"✅ {op_name} 成功")
                else:
                    self.logger.error(f"❌ {op_name} 失败")
                delay = random.uniform(min_delay, max_delay)
                self.logger.info(f"⏸️  等待 {delay:.1f} 秒...")
                time.sleep(delay)
            except Exception as e:
                self.logger.error(f"🚫 错误: {str(e)}")
                continue

        self.logger.info(f"\n🎉 完成！共 {len(accounts)} 个账号，成功 {success_count} 次。\n")

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.logger.info(f"🔄 环境已切换至: {new_env.upper()}")