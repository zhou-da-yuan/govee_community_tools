# govee_community_tool/gui/pages/account_tool.py
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from core.account_generator import AccountGenerator
from gui.widgets.log_text import LogText
from core.auth import login
from core.session_manager import SessionManager
from utils.file_loader import load_accounts
import threading
import os
import json

from utils.logger import SimpleLogger


class AccountToolPage(ttk.Frame):
    def __init__(self, parent, initial_accounts, total_count, current_env, change_env_callback):
        super().__init__(parent)
        self.accounts = initial_accounts.copy()
        self.total_accounts = total_count
        self.current_env = current_env
        self.change_env_callback = change_env_callback
        self.session_manager = SessionManager()

        self.setup_ui()

    def setup_ui(self):
        # 使用 StringVar 来绑定动态文本
        self.account_count_var = tk.StringVar(value=f"📦 当前账号数: {self.total_accounts}")

        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info_frame, textvariable=self.account_count_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        # 添加延迟设置
        delay_frame = ttk.Frame(self)
        delay_frame.pack(pady=5)

        tk.Label(delay_frame, text="验证延迟 (最小秒):").pack(side=tk.LEFT)
        self.min_validate_delay = tk.Entry(delay_frame, width=8)
        self.min_validate_delay.insert(0, "1")
        self.min_validate_delay.pack(side=tk.LEFT, padx=5)

        tk.Label(delay_frame, text="最大秒):").pack(side=tk.LEFT)
        self.max_validate_delay = tk.Entry(delay_frame, width=8)
        self.max_validate_delay.insert(0, "3")
        self.max_validate_delay.pack(side=tk.LEFT, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        # 在 delay_frame 后添加 generate_frame
        generate_frame = ttk.Frame(self)
        generate_frame.pack(pady=5)

        tk.Label(generate_frame, text="生成数量:").pack(side=tk.LEFT)
        self.generate_count = tk.Entry(generate_frame, width=8)
        self.generate_count.insert(0, "5")
        self.generate_count.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="📁 加载账号文件", command=self.load_accounts_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 验证全部账号", style="Accent.TButton",
                   command=self.validate_all_accounts).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🆕 生成账号", style="Success.TButton",
                   command=self.generate_accounts_gui).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 导出有效账号", command=self.export_valid_accounts).pack(side=tk.LEFT, padx=5)

        # 日志
        log_frame = ttk.LabelFrame(self, text="📋 账号验证日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_widget = LogText(log_frame, height=20)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        self.valid_accounts = []

    def log(self, message):
        self.log_widget.log(message)

    def load_accounts_file(self):
        path = filedialog.askopenfilename(title="选择账号文件", filetypes=[("JSON files", "*.json")])
        if path:
            accounts = load_accounts(path)
            if accounts:
                self.accounts = accounts
                self.total_accounts = len(accounts)
                self.valid_accounts = []
                # ✅ 更新 UI 显示
                self.account_count_var.set(f"📦 当前账号数: {self.total_accounts}")
                self.log(f"✅ 成功加载 {self.total_accounts} 个账号：{os.path.basename(path)}")
            else:
                messagebox.showerror("❌ 加载失败", "账号文件格式错误或为空！")

    def refresh_accounts(self, new_accounts, total_count):
        """外部调用：刷新账号列表和 UI 显示"""
        self.accounts = new_accounts.copy()
        self.total_accounts = total_count
        self.valid_accounts = []
        # ✅ 刷新 UI 上的账号数
        self.account_count_var.set(f"📦 当前账号数: {self.total_accounts}")
        self.log(f"🔄 已刷新账号列表，共 {self.total_accounts} 个账号（来自 {self.current_env} 环境）")

    def validate_all_accounts(self):
        if not self.accounts:
            messagebox.showwarning("⚠️ 警告", "请先加载账号！")
            return

        try:
            min_delay = float(self.min_validate_delay.get().strip())
            max_delay = float(self.max_validate_delay.get().strip())
            if min_delay < 0 or max_delay < 0 or min_delay > max_delay:
                raise ValueError
        except:
            messagebox.showwarning("⚠️ 警告", "验证延迟格式错误！")
            return

        self.log(f"🔍 开始验证 {self.total_accounts} 个账号...")
        self.valid_accounts = []
        base_url = self.get_base_url()

        thread = threading.Thread(
            target=self.run_validation,
            args=(base_url, min_delay, max_delay),
            daemon=True
        )
        thread.start()

    def run_validation(self, base_url, min_delay, max_delay):
        success_count = 0
        for idx, acc in enumerate(self.accounts, 1):
            email = acc['email']
            try:
                session = self.session_manager.get_session()
                session.headers.update({'Authorization': ''})
                token = login(self.session_manager, acc['email'], acc['password'], base_url)
                self.log(f"[{idx}/{self.total_accounts}] ✅ {email} 登录成功")
                self.valid_accounts.append(acc)
                success_count += 1
            except Exception as e:
                self.log(f"[{idx}/{self.total_accounts}] ❌ {email} 失败: {str(e)}")

            # 👇 添加延迟
            if idx < self.total_accounts:  # 最后一个不延迟
                delay = random.uniform(min_delay, max_delay)
                self.log(f"⏸️  等待 {delay:.1f} 秒...")
                time.sleep(delay)

        self.log(f"\n🎉 验证完成！共 {self.total_accounts} 个账号，有效 {success_count} 个。\n")

    def export_valid_accounts(self):
        if not self.valid_accounts:
            messagebox.showinfo("ℹ️ 提示", "暂无有效账号可导出。")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存有效账号",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.valid_accounts, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("✅ 成功", f"已导出 {len(self.valid_accounts)} 个有效账号到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("❌ 错误", f"保存失败: {str(e)}")

    def generate_accounts_gui(self):
        try:
            count = int(self.generate_count.get().strip())
            if count <= 0 or count > 100:
                messagebox.showwarning("⚠️ 输入错误", "请输入 1-100 之间的数字")
                return
        except:
            messagebox.showwarning("⚠️ 输入错误", "请输入有效数字")
            return

        if messagebox.askyesno("确认", f"即将生成 {count} 个账号，确认继续？"):
            thread = threading.Thread(
                target=self.run_generate,
                args=(count,),
                daemon=True
            )
            thread.start()

    def run_generate(self, count: int):
        base_url = self.get_base_url()
        # ✅ 包装成统一接口
        logger = SimpleLogger(self.log_widget.log)  # 传入 LogText.log 方法

        generator = AccountGenerator(base_url, log_widget=logger)  # 注意是 log=logger
        try:
            generated = generator.generate_accounts(count)
            self.accounts.extend(generated)
            self.valid_accounts.extend(generated)  # 生成即有效
            self.total_accounts = len(self.accounts)
            self.log(f"\n🎉 成功生成 {len(generated)} 个账号，当前共 {self.total_accounts} 个账号。\n")
        except Exception as e:
            self.log(f"❌ 生成过程中发生错误: {str(e)}")

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.log(f"🔄 环境已切换至: {new_env.upper()}")
