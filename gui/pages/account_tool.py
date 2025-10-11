# govee_community_tool/gui/pages/account_tool.py
import random
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from core.account_generator import AccountGenerator
from core.email_verifier import EmailVerifier
from gui.widgets.log_text import LogText
from core.auth import login
from core.session_manager import SessionManager
from utils.file_loader import load_accounts
import threading
import os
import json

from utils.logger import SimpleLogger
from config.settings import ENV_CONFIG, ENV_TO_FILE
from gui.widgets.tooltip import add_tooltip


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

        # === 修改：info_frame 包含 刷新按钮 + 账号数 ===
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # 账号数标签
        ttk.Label(
            info_frame,
            textvariable=self.account_count_var,
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)

        refresh_btn = ttk.Button(
            info_frame,
            text="🔄 刷新",
            width=10,
            command=self.reload_current_file
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        add_tooltip(refresh_btn, "从文件重新加载当前环境的账号列表")

        # 延迟设置
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

        # 按钮区域
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        # 按钮顺序优化（移除了“重载当前文件”）
        ttk.Button(btn_frame, text="📁 加载账号文件", command=self.load_accounts_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 验证全部账号", style="Accent.TButton",
                   command=self.validate_all_accounts).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🆕 生成随机账号", style="Success.TButton",
                   command=self.generate_accounts_gui).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📥 获取邮箱验证码", style="Warning.TButton",
                   command=self.fetch_verification_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 导出有效账号", command=self.export_valid_accounts).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 查看已保存账号", command=self.open_accounts_folder).pack(side=tk.LEFT, padx=5)

        # 日志
        log_frame = ttk.LabelFrame(self, text="📋 账号验证日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_widget = LogText(log_frame, height=20)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        self.valid_accounts = []

        # === 新增：账号表格区域 ===
        table_frame = ttk.LabelFrame(self, text="📊 账号列表", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 创建带滚动条的 Treeview
        columns = ("email", "password", "env")
        self.account_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8
        )

        # 设置列标题和宽度
        self.account_tree.heading("email", text="📧 邮箱")
        self.account_tree.heading("password", text="🔑 密码")
        self.account_tree.heading("env", text="🌐 环境")

        self.account_tree.column("email", width=250, anchor="w")
        self.account_tree.column("password", width=180, anchor="w")
        self.account_tree.column("env", width=100, anchor="center")

        # 添加垂直滚动条
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.account_tree.pack(fill=tk.BOTH, expand=True)

        # 可选：双击复制邮箱
        self.account_tree.bind("<Double-1>", self.on_double_click_account)

        # 初始化为空
        self.refresh_account_table()

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
                self.refresh_account_table()  # ✅ 刷新表格
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
        """弹出输入框，获取生成数量"""
        dialog = tk.Toplevel(self)
        dialog.title("生成随机账号")
        dialog.geometry("300x180")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        dialog.configure(bg="#f9f9f9")

        # 标题
        ttk.Label(dialog, text="请输入要生成的账号数量", font=("微软雅黑", 11, "bold")).pack(pady=(15, 5))

        # 范围提示
        ttk.Label(
            dialog,
            text="范围：1-100",
            foreground="gray",
            font=("微软雅黑", 9)
        ).pack()

        # 输入框
        input_frame = ttk.Frame(dialog)
        input_frame.pack(pady=15, padx=20, fill=tk.X)

        ttk.Label(input_frame, text="数量:", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        count_var = tk.StringVar(value="5")
        entry = ttk.Entry(input_frame, textvariable=count_var, font=("微软雅黑", 10), width=10)
        entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        entry.focus()

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        # 使用 grid 布局避免文字被截断
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        def on_confirm():
            try:
                count = int(count_var.get().strip())
                if count < 1 or count > 100:
                    raise ValueError
                dialog.destroy()
                if messagebox.askyesno("确认", f"即将生成 {count} 个账号，确认继续？"):
                    self.run_generate_in_thread(count)
            except:
                messagebox.showwarning("⚠️ 输入错误", "请输入 1 到 100 之间的整数！")
                entry.focus()

        # 使用 grid + 足够宽度
        ttk.Button(button_frame, text="确定", width=12, style="Success.TButton", command=on_confirm).grid(row=0,
                                                                                                          column=0,
                                                                                                          padx=5,
                                                                                                          sticky="w")

        ttk.Button(button_frame, text="取消", width=12, command=dialog.destroy).grid(row=0, column=1, padx=5,
                                                                                     sticky="e")

    def run_generate_in_thread(self, count: int):
        """启动线程生成账号"""
        thread = threading.Thread(
            target=self.run_generate,
            args=(count,),
            daemon=True
        )
        thread.start()

    def run_generate(self, count: int):
        base_url = self.get_base_url()
        logger = SimpleLogger(self.log_widget.log)

        generator = AccountGenerator(base_url, logger)
        try:
            generated = generator.generate_accounts(count)
            if not generated:
                self.log("❌ 未生成任何账号。")
                return

            # 添加到全局列表
            self.accounts.extend(generated)
            self.valid_accounts.extend(generated)
            self.total_accounts = len(self.accounts)

            # 📁 自动保存到对应环境文件
            file_path = ENV_TO_FILE.get(self.current_env)
            if not file_path:
                self.log(f"⚠️ 未知环境：{self.current_env}，跳过保存。")
                return

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 读取原文件内容（避免覆盖）
            existing_accounts = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_accounts = json.load(f)
                        if not isinstance(existing_accounts, list):
                            existing_accounts = []
                except Exception as e:
                    self.log(f"⚠️ 读取历史账号失败（将新建）：{str(e)}")

            # 合并并去重（按 email 去重）
            email_set = {acc['email'] for acc in existing_accounts}
            new_unique = [acc for acc in generated if acc['email'] not in email_set]
            updated_accounts = existing_accounts + new_unique

            # 写回文件
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_accounts, f, indent=2, ensure_ascii=False)
                self.log(f"💾 已将 {len(new_unique)} 个新账号保存至: {file_path}")
                if len(new_unique) < len(generated):
                    self.log(f"ℹ️  共 {len(generated) - len(new_unique)} 个重复邮箱被跳过。")
            except Exception as e:
                self.log(f"❌ 保存文件失败: {str(e)}")

            # ✅ 刷新表格
            self.refresh_account_table()

            # 更新 UI
            self.account_count_var.set(f"📦 当前账号数: {self.total_accounts}")
            self.log(f"\n🎉 成功生成 {len(generated)} 个账号，当前共 {self.total_accounts} 个账号。\n")

        except Exception as e:
            self.log(f"❌ 生成过程中发生错误: {str(e)}")

    def fetch_verification_code(self):
        """优化版弹窗：获取邮箱验证码"""
        dialog = tk.Toplevel(self)
        dialog.title("获取邮箱验证码")
        dialog.geometry("400x280")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # 设置背景色（可选）
        dialog.configure(bg="#f9f9f9")

        # 标题
        title_label = ttk.Label(dialog, text="请输入邮箱和密码以获取验证码", font=("微软雅黑", 11, "bold"))
        title_label.pack(pady=(15, 10))

        # 警告提示（红色）
        warning_label = ttk.Label(
            dialog,
            text="⚠️ 仅在该工具创建的账号可以获取验证码",
            foreground="red",
            font=("微软雅黑", 9, "italic"),
            wraplength=350
        )
        warning_label.pack(pady=(0, 15))

        # 邮箱输入框
        email_frame = ttk.Frame(dialog)
        email_frame.pack(pady=5, padx=20, fill=tk.X)

        ttk.Label(email_frame, text="📧 邮箱:", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        email_var = tk.StringVar()
        email_entry = ttk.Entry(email_frame, textvariable=email_var, width=30, font=("微软雅黑", 10))
        email_entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        # 密码输入框
        password_frame = ttk.Frame(dialog)
        password_frame.pack(pady=5, padx=20, fill=tk.X)

        ttk.Label(password_frame, text="🔐 密码:", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        password_var = tk.StringVar()
        password_entry = ttk.Entry(password_frame, textvariable=password_var, width=30, font=("微软雅黑", 10), show="*")
        password_entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def on_confirm():
            email = email_var.get().strip()
            password = password_var.get().strip()
            if not email or not password:
                messagebox.showwarning("❌ 输入错误", "邮箱和密码不能为空！")
                return
            dialog.destroy()
            threading.Thread(target=self.run_fetch_code, args=(email, password), daemon=True).start()

        ttk.Button(button_frame, text="取消", width=10, style="TButton", command=dialog.destroy).pack(side=tk.RIGHT,
                                                                                                      padx=10)
        ttk.Button(button_frame, text="验证", width=10, style="Success.TButton", command=on_confirm).pack(side=tk.RIGHT)

        # 焦点设置
        email_entry.focus()

    def run_fetch_code(self, email: str, password: str):
        """后台线程：调用 core 模块获取验证码"""
        self.log(f"🔄 正在为 {email} 获取验证码...")

        try:
            from core.email_verifier import EmailVerifier
        except ImportError:
            self.log("❌ 未找到 EmailVerifier 模块，请检查 core/email_verifier.py 是否存在。")
            return

        verifier = EmailVerifier(log=self.log)  # 使用日志回调
        code = verifier.get_verification_code(email, password, code_length=4)

        if code:
            self.log(f"🔑 提取到 {email} 的 4 位验证码: {code}")
        else:
            self.log(f"❌ 未能从 {email} 获取到验证码，请确认邮箱有新邮件或账号正确。")

    def reload_current_file(self):
        file_path = ENV_TO_FILE.get(self.current_env)
        if not file_path or not os.path.exists(file_path):
            return

        accounts = load_accounts(file_path)
        if accounts:
            self.accounts = accounts
            self.total_accounts = len(accounts)
            self.valid_accounts = []
            self.refresh_account_table()  # ✅ 刷新表格
            self.log(f"🔄 已从 {file_path} 重新加载 {self.total_accounts} 个账号。")
        else:
            self.log(f"❌ 文件为空或格式错误：{file_path}")

    def open_accounts_folder(self):
        """打开保存账号的目录（兼容打包环境）"""
        file_path = ENV_TO_FILE.get(self.current_env)
        if not file_path:
            messagebox.showwarning("⚠️ 未知环境", f"未配置 {self.current_env} 的账号文件路径")
            return

        dir_path = os.path.dirname(file_path)  # 已经是正确路径

        # ✅ 确保目录存在，不存在则创建
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                self.log(f"📁 已创建目录：{dir_path}")
            except Exception as e:
                messagebox.showerror("❌ 创建失败", f"无法创建目录：{str(e)}")
                return

        # 跨平台打开目录
        try:
            if os.name == 'nt':  # Windows
                os.startfile(dir_path)
            elif os.name == 'posix':
                if sys.platform == "darwin":  # macOS
                    os.system(f'open "{dir_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{dir_path}"')
            self.log(f"📁 已打开账号保存目录：{os.path.basename(dir_path)}")
        except Exception as e:
            messagebox.showerror("❌ 打开失败", f"无法打开目录：{str(e)}")

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.log(f"🔄 环境已切换至: {new_env.upper()}")
        self.reload_current_file()  # 自动刷新账号和表格

    def refresh_account_table(self):
        """清空并重新填充账号表格"""
        # 清空现有数据
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        # 插入新数据
        for acc in self.accounts:
            self.account_tree.insert(
                "",
                tk.END,
                values=(acc['email'], acc['password'], self.current_env.upper())
            )

        # 更新状态标签
        self.account_count_var.set(f"📦 当前账号数: {len(self.accounts)}")

    def on_double_click_account(self, event):
        selection = self.account_tree.selection()
        if not selection:
            return
        item = self.account_tree.item(selection[0])
        email = item["values"][0]
        try:
            # 使用主窗口操作剪贴板
            self.winfo_toplevel().clipboard_clear()
            self.winfo_toplevel().clipboard_append(email)
            self.winfo_toplevel().update()
            self.log(f"📋 已复制邮箱到剪贴板: {email}")
        except Exception as e:
            self.log(f"❌ 无法复制到剪贴板: {str(e)}")
