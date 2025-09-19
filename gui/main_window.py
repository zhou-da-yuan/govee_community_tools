# govee_community_tool/gui/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox

from gui.pages.account_tool import AccountToolPage
from gui.pages.batch_page import BatchOperationsPage
from gui.pages.single_account import SingleAccountOperationsPage
# 操作记录
from gui.pages.history_page import OperationHistoryPage

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("🔹 Govee 社区自动化工具 v3.0")
        self.root.geometry("1000x650")
        self.root.minsize(800, 600)

        self.current_env = "dev"
        self.accounts = self.load_default_accounts()
        self.total_accounts = len(self.accounts)

        self.setup_styles()
        self.setup_menu()
        self.setup_layout()
        self.show_page(BatchOperationsPage)

    def load_default_accounts(self):
        from utils.file_loader import load_accounts
        default_path = "resources/accounts.json"
        return load_accounts(default_path) or [
            {"email": "mmmm27@somoj.com", "password": "151515jr"},
            {"email": "pppp551@somoj.com", "password": "77777777c"},
            {"email": "hhhh04@somoj.com", "password": "86868686r"},
            {"email": "zzzz425@somoj.com", "password": "14141414u"},
            {"email": "ttt88@somoj.com", "password": "595959wk"},
        ]

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 10, "bold"))
        style.configure("Menu.TButton", font=("Arial", 10), padding=6)

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        env_menu = tk.Menu(menubar, tearoff=0)
        env_menu.add_command(label="DEV 环境", command=lambda: self.switch_env("dev"))
        env_menu.add_command(label="PDA 环境", command=lambda: self.switch_env("pda"))
        menubar.add_cascade(label="🌍 环境切换", menu=env_menu)

    def setup_layout(self):
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧菜单
        left_frame = ttk.Frame(paned, width=200, relief="sunken")
        left_frame.pack_propagate(False)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="功能菜单", style="Header.TLabel", anchor="center").pack(fill=tk.X, pady=(10, 20))

        self.menu_buttons = {}
        pages = [
            ("📦 批量账号操作", BatchOperationsPage),
            ("👤 单账号操作", SingleAccountOperationsPage),
            ("🔧 账号工具", AccountToolPage),
            ("📜 操作历史", OperationHistoryPage),  # 新增操作记录
        ]

        for text, page_class in pages:
            btn = ttk.Button(left_frame, text=text, style="Menu.TButton",
                             command=lambda pc=page_class: self.show_page(pc))
            btn.pack(fill=tk.X, padx=10, pady=5)
            self.menu_buttons[page_class] = btn

        self.env_label = ttk.Label(left_frame, text=f"📍 当前环境: {self.current_env.upper()}", foreground="blue")
        self.env_label.pack(side="bottom", pady=10)

        # 右侧内容
        self.content_frame = ttk.Frame(paned)
        paned.add(self.content_frame, weight=4)

        self.current_page = None

    # 修改 show_page 方法的调用参数（适配不同页面）
    def show_page(self, PageClass):
        if self.current_page is not None:
            self.current_page.destroy()

        # 根据页面类型传参
        if PageClass == BatchOperationsPage:
            self.current_page = PageClass(
                self.content_frame,
                self.accounts,
                self.total_accounts,
                self.current_env,
                self.on_environment_changed
            )
        elif PageClass == AccountToolPage:
            self.current_page = PageClass(
                self.content_frame,
                self.accounts,
                self.total_accounts,
                self.current_env,
                self.on_environment_changed
            )
        elif PageClass == SingleAccountOperationsPage:
            self.current_page = PageClass(
                self.content_frame,
                self.current_env,
                self.on_environment_changed
            )
        else:
            self.current_page = PageClass(self.content_frame)

        self.current_page.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def switch_env(self, env):
        if env == self.current_env:
            messagebox.showinfo("提示", f"已在 {env.upper()} 环境")
            return
        self.current_env = env
        self.env_label.config(text=f"📍 当前环境: {env.upper()}")
        if self.current_page and hasattr(self.current_page, "on_environment_changed"):
            self.current_page.on_environment_changed(env)
        messagebox.showinfo("切换成功", f"已切换到 {env.upper()} 环境")

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.env_label.config(text=f"📍 当前环境: {new_env.upper()}")