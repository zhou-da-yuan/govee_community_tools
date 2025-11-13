# govee_community_tool/gui/pages/batch_page.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gui.widgets.log_text import LogText
from gui.widgets.placeholder_entry import PlaceholderEntry
from gui.widgets.tooltip import add_tooltip
from utils.file_loader import load_accounts
from core.auth import login
from core.operations import execute_operation
from core.session_manager import SessionManager
import threading
import random
import time
import os

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

        # === 修改：info_frame 包含 账号数 + 刷新按钮 ===
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # 账号数标签
        ttk.Label(
            info_frame,
            textvariable=self.account_count_var,
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)

        # 刷新按钮
        refresh_btn = ttk.Button(
            info_frame,
            text="🔄 刷新",
            width=10,
            command=self.reload_current_file
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        add_tooltip(refresh_btn, "从文件重新加载当前环境的账号列表")

        # --- 操作类型 ---
        op_frame = ttk.LabelFrame(self, text="选择操作类型", padding=10)
        op_frame.pack(fill=tk.X, pady=10)

        self.choice_var = tk.StringVar(value="complaint_topic")

        ops = list(self.op_map.items())  # [(key, name), ...]
        max_per_row = 5
        col_width = 14  # ✅ 固定宽度（字符），适应 8 个中文
        h_padding = 25  # 横向间距（像素）

        container = ttk.Frame(op_frame)
        container.pack(fill=tk.X, anchor="w")

        for i in range(0, len(ops), max_per_row):
            row_frame = ttk.Frame(container)
            row_frame.pack(fill=tk.X, pady=2, anchor="w")

            # 创建一个 grid 容器
            grid_frame = ttk.Frame(row_frame)
            grid_frame.grid(row=0, column=0, sticky="w")
            grid_frame.columnconfigure(list(range(max_per_row)), weight=0)  # 禁止拉伸

            for j in range(max_per_row):
                if i + j < len(ops):
                    key, name = ops[i + j]
                    rb = tk.Radiobutton(
                        grid_frame,
                        text=name,
                        variable=self.choice_var,
                        value=key,
                        font=("Arial", 9),
                        command=self.on_operation_change,
                        indicatoron=True,
                        selectcolor="lightblue",
                        width=col_width  # ✅ 强制宽度（字符）
                    )
                    rb.grid(row=0, column=j, sticky="w", padx=(0, h_padding), pady=2)
                    rb.bind("<Button-1>", lambda e, r=rb: r.invoke())
                else:
                    # 空白占位，保持列宽一致
                    empty_label = tk.Label(grid_frame, width=col_width, font=("Arial", 9))
                    empty_label.grid(row=0, column=j, sticky="w", padx=(0, h_padding), pady=2)

        # ===== 参数设置 =====
        input_frame = ttk.LabelFrame(self, text="参数设置", padding=10)
        input_frame.pack(fill=tk.X, pady=10)

        # --- 子 Frame 1: 目标ID + 评论内容 ---
        target_frame = ttk.Frame(input_frame)
        target_frame.pack(fill=tk.X, pady=2)

        tk.Label(target_frame, text="目标ID:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.target_id_entry = PlaceholderEntry(
            target_frame,
            placeholder="话题ID/视频ID/帖子ID/播放列表ID",
            width=30,
            font=("Consolas", 10)
        )
        self.target_id_entry.pack(side=tk.LEFT, padx=(0, 15))

        # 评论内容（初始隐藏）
        self.comment_label = tk.Label(target_frame, text="评论内容:", font=("Arial", 9))
        self.comment_content_entry = tk.Entry(target_frame, width=40, font=("Consolas", 10))
        self.comment_content_entry.insert(0, "This is the default comment content for testing")

        # 初始隐藏
        self.comment_label.pack_forget()
        self.comment_content_entry.pack_forget()

        # --- 子 Frame 2: 使用账号数 + 起始位置 ---
        account_frame = ttk.Frame(input_frame)
        account_frame.pack(fill=tk.X, pady=2)

        tk.Label(account_frame, text="使用账号数:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.num_accounts_entry = tk.Entry(account_frame, width=8, font=("Consolas", 10))
        self.num_accounts_entry.insert(0, str(min(5, self.total_accounts)))
        self.num_accounts_entry.pack(side=tk.LEFT, padx=(0, 40))

        tk.Label(account_frame, text="起始账号位置:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.start_index_entry = tk.Entry(account_frame, width=8, font=("Consolas", 10))
        self.start_index_entry.insert(0, "1")
        self.start_index_entry.pack(side=tk.LEFT, padx=(0, 0))

        # --- 子 Frame 3: 延迟设置 ---
        delay_frame1 = ttk.Frame(input_frame)
        delay_frame1.pack(fill=tk.X, pady=2)
        tk.Label(delay_frame1, text="延迟 (最小秒):", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.min_delay_entry = tk.Entry(delay_frame1, width=6, font=("Consolas", 10))
        self.min_delay_entry.insert(0, "2")
        self.min_delay_entry.pack(side=tk.LEFT, padx=(0, 15))

        delay_frame2 = ttk.Frame(input_frame)
        delay_frame2.pack(fill=tk.X, pady=2)
        tk.Label(delay_frame2, text="延迟 (最大秒):", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.max_delay_entry = tk.Entry(delay_frame2, width=6, font=("Consolas", 10))
        self.max_delay_entry.insert(0, "5")
        self.max_delay_entry.pack(side=tk.LEFT, padx=(0, 15))

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
            self.comment_label.pack(side=tk.LEFT, padx=(0, 5))
            self.comment_content_entry.pack(side=tk.LEFT)
        else:
            self.comment_label.pack_forget()
            self.comment_content_entry.pack_forget()

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

            # 👉 新增：起始位置处理
        start_input = self.start_index_entry.get().strip()
        try:
            start_index = int(start_input)
            if start_index < 1:
                raise ValueError
        except Exception:
            messagebox.showwarning("⚠️ 警告", "起始位置必须是 ≥1 的整数！")
            return

        if start_index > self.total_accounts:
            messagebox.showwarning("⚠️ 警告", f"起始位置 {start_index} 超出总账号数 {self.total_accounts}！")
            return

        end_index = start_index - 1 + num_accounts
        selected_accounts = self.accounts[start_index - 1: min(end_index, self.total_accounts)]

        if len(selected_accounts) == 0:
            messagebox.showwarning("⚠️ 警告", "没有可操作的账号，请检查起始位置和账号数量！")
            return

        op_name = self.op_map[choice]
        self.logger.info(
            f"🚀 开始执行: {op_name} | ID: {target_id} | 账号数: {len(selected_accounts)} | 起始位置: #{start_index}")
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
            args=(choice, op_name, target_id, selected_accounts, min_delay, max_delay, self.current_env),
            kwargs=extra_kwargs,  # 传入 content
            daemon=True
        )
        thread.start()

    def run_operation(self, op_key, op_name, target_id, accounts, min_delay, max_delay, current_env, **kwargs):
        success_count = 0
        base_url = self.get_base_url()
        total = len(accounts)

        for idx, acc in enumerate(accounts, 1):
            self.logger.info(f"--- [{idx}/{total}] 账号: {acc['email']} ---")
            try:
                token = login(self.session_manager, acc['email'], acc['password'], base_url)
                self.logger.info("✅ 登录成功")
                if execute_operation(op_key, self.session_manager, token, base_url, target_id=target_id,
                                     env=current_env, **kwargs):
                    success_count += 1
                    self.logger.info(f"✅ {op_name} 成功")
                else:
                    self.logger.error(f"❌ {op_name} 失败")

                # 👉 只有不是最后一个账号时才等待
                if idx < total:
                    delay = random.uniform(min_delay, max_delay)
                    self.logger.info(f"⏸️  等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                else:
                    self.logger.info("🔚 最后一个账号，跳过延迟。")

            except Exception as e:
                self.logger.error(f"🚫 错误: {str(e)}")
                # 即使出错，如果是最后一个也不用等
                if idx < total:
                    delay = random.uniform(min_delay, max_delay)
                    self.logger.info(f"⏸️  异常后等待 {delay:.1f} 秒...")
                    time.sleep(delay)

        self.logger.info(f"\n🎉 完成！共 {total} 个账号，成功 {success_count} 次。\n")

    def reload_current_file(self):
        """从当前环境对应的文件重新加载账号"""
        from config.settings import ENV_TO_FILE
        file_path = ENV_TO_FILE.get(self.current_env)
        if not file_path or not os.path.exists(file_path):
            self.logger.warning(f"⚠️ 未找到当前环境的账号文件: {file_path}")
            return

        accounts = load_accounts(file_path)
        if accounts:
            self.accounts = accounts
            self.total_accounts = len(accounts)
            self.account_count_var.set(f"📦 当前账号数: {self.total_accounts}")
            self.logger.info(f"🔄 已从 {os.path.basename(file_path)} 重新加载 {self.total_accounts} 个账号。")
        else:
            self.logger.error(f"❌ 文件为空或格式错误：{file_path}")

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.logger.info(f"🔄 环境已切换至: {new_env.upper()}")

    def refresh_accounts(self, new_accounts, total_count):
        """外部调用：刷新账号列表和 UI 显示"""
        self.accounts = new_accounts.copy()
        self.total_accounts = total_count
        # ✅ 刷新 UI 上的账号数
        self.account_count_var.set(f"📦 当前账号数: {self.total_accounts}")
        self.log(f"🔄 已刷新账号列表，共 {self.total_accounts} 个账号（来自 {self.current_env} 环境）")
