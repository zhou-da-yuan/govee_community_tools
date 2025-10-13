# govee_community_tool/gui/main_window.py
import os
import tkinter as tk
from tkinter import ttk, messagebox

from gui.pages.account_tool import AccountToolPage
from gui.pages.batch_page import BatchOperationsPage
from gui.pages.single_account import SingleAccountPage
from gui.pages.history_page import OperationHistoryPage
from config.__version__ import __version__, __author__, __email__
from gui.widgets.help_viewer import HelpViewer


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
        # 根据当前环境选择文件
        filename = f"accounts_{self.current_env}.json"
        file_path = os.path.join("resources", filename)

        # 使用 resource_path 处理打包后路径
        from utils import file_loader
        full_path = file_loader.resource_path(file_path)

        accounts = load_accounts(full_path)
        if accounts:
            return accounts
        else:
            # fallback 默认账号（按环境提供不同默认值）
            if self.current_env == "dev":
                return [
                    {"email": "mmmm27@somoj.com", "password": "151515jr"},
                    {"email": "pppp551@somoj.com", "password": "77777777c"},
                    {"email": "hhhh04@somoj.com", "password": "86868686r"},
                    {"email": "zzzz425@somoj.com", "password": "14141414u"},
                    {"email": "ttt88@somoj.com", "password": "595959wk"},
                ]
            elif self.current_env == "pda":
                return [
                    {"email": "test1@pda.com", "password": "123456"},
                    {"email": "test2@pda.com", "password": "123456"},
                ]
            return []

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

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📘 帮助", menu=help_menu)
        help_menu.add_command(label="使用帮助", command=self.show_help)
        # help_menu.add_separator()
        # help_menu.add_command(label="关于", command=self.show_about)

    def setup_layout(self):
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧菜单
        left_frame = ttk.Frame(paned, width=150, relief="sunken")
        left_frame.pack_propagate(False)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="功能菜单", style="Header.TLabel", anchor="center").pack(fill=tk.X, pady=(10, 20))

        self.menu_buttons = {}
        pages = [
            ("📦 批量账号操作", BatchOperationsPage),
            ("👤 账号操作", SingleAccountPage),
            ("🔧 账号工具", AccountToolPage),
            ("📜 操作历史", OperationHistoryPage),
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
        elif PageClass == SingleAccountPage:
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

        # 保存旧环境
        old_env = self.current_env
        self.current_env = env

        # 更新环境标签
        self.env_label.config(text=f"📍 当前环境: {env.upper()}")

        # 🔁 重新加载该环境的默认账号
        self.accounts = self.load_default_accounts()
        self.total_accounts = len(self.accounts)

        # 🔄 如果当前页面支持环境切换，通知它
        if self.current_page and hasattr(self.current_page, "on_environment_changed"):
            self.current_page.on_environment_changed(env)

        # 🔄 如果当前页面是 AccountToolPage 或 BatchOperationsPage，需要刷新账号和 UI
        if hasattr(self.current_page, 'refresh_accounts'):
            self.current_page.refresh_accounts(self.accounts, self.total_accounts)

        messagebox.showinfo("切换成功", f"已切换到 {env.upper()} 环境\n并加载 {self.total_accounts} 个账号。")

    def show_help(self):
        HelpViewer.show_help(self.root)

    def show_about(self):
        """关于"""
        messagebox.showinfo(
            "关于",
            f"Govee 社区工具 v{__version__}\n\n"
            "功能：自动化发帖、点赞、投诉等操作\n"
            f"作者：{__author__}\n"
            f"邮箱：{__email__}\n"
            # "GitHub: github.com/yourname/govee-tool"
        )

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.env_label.config(text=f"📍 当前环境: {new_env.upper()}")
