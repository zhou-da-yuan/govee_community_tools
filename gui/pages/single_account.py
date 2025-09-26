# govee_community_tool/gui/pages/single_account.py

import tkinter as tk
from tkinter import ttk, messagebox

from gui.widgets.aid_popup import AidPopup
from gui.widgets.log_text import LogText
from core.auth import login
from core.operations import OPERATIONS, get_user_aid
from core.operations import execute_operation
from core.session_manager import SessionManager
from core_admin.admin_operations import ADMIN_OPERATIONS, execute_admin_operation
import threading
import time
import random
from core.session_state import session_state


class SingleAccountPage(ttk.Frame):
    def __init__(self, parent, current_env, change_env_callback):
        super().__init__(parent)
        self.current_env = current_env
        self.change_env_callback = change_env_callback
        self.session_manager = SessionManager()
        self.op_key_var = tk.StringVar()
        self.operations = {}          # 所有支持的操作 {key: info}
        self.op_map = {}              # key -> 显示名
        self.reverse_ops_map = {}     # 显示名 -> key
        self.param_widgets = {}
        self.setup_ui()
        self.load_operations()  # 加载所有单账号支持的操作
        self.update_operation_dropdown()

    def setup_ui(self):
        # 1. 账号输入区
        account_frame = ttk.LabelFrame(self, text="🔑 账号信息", padding=15)
        account_frame.pack(fill=tk.X, pady=10)

        tk.Label(account_frame, text="📧 邮箱:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.email_entry = tk.Entry(account_frame, width=30, font=("Consolas", 10))
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        if session_state.email:
            self.email_entry.insert(0, session_state.email)

        tk.Label(account_frame, text="🔒 密码:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.password_entry = tk.Entry(account_frame, width=30, font=("Consolas", 10), show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        if session_state.password:
            self.password_entry.insert(0, session_state.password)

        # 2. 操作选择区
        op_frame = ttk.LabelFrame(self, text="⚙️ 操作选择", padding=15)
        op_frame.pack(fill=tk.X, pady=10)

        tk.Label(op_frame, text="选择操作:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.op_combo = ttk.Combobox(op_frame, state="readonly", width=25)
        self.op_combo.grid(row=0, column=1, padx=5, pady=5)
        self.op_combo.bind("<<ComboboxSelected>>", self.on_operation_selected)

        # 3. 动态参数区
        self.param_frame = ttk.LabelFrame(self, text="📌 参数设置", padding=15)
        self.param_frame.pack(fill=tk.X, pady=10)

        # 4. 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="▶️ 执行操作", style="Accent.TButton",
                   command=self.start_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 获取 AID", command=self.get_aid).pack(side=tk.LEFT, padx=5)

        # 5. 日志输出
        log_frame = ttk.LabelFrame(self, text="📝 运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.log_widget = LogText(log_frame, height=15)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def load_operations(self):
        """加载所有支持单账号的操作（用户 + 管理员），并标记类型"""
        operations = {}

        # 普通用户操作
        for key, op in OPERATIONS.items():
            if op.get("support_single", False):
                operations[key] = {
                    "name": op["name"],
                    "description": op.get("description", ""),
                    "params": op["params"],
                    "type": "user"
                }

        # 管理员操作
        for key, op in ADMIN_OPERATIONS.items():
            if op.get("support_single", False):
                operations[key] = {
                    "name": op["name"],
                    "description": op["description"],
                    "params": op["params"],
                    "type": "admin"
                }

        self.operations = operations
        self.op_map = {k: v["name"] for k, v in self.operations.items()}
        self.reverse_ops_map = {v["name"]: k for k, v in self.operations.items()}

    def update_operation_dropdown(self):
        names = sorted([info["name"] for info in self.operations.values()])
        self.op_combo['values'] = names
        if names:
            self.op_combo.set(names[0])
            self.on_operation_selected()

    def on_operation_selected(self, event=None):
        """根据选择的操作动态生成参数输入框"""
        selected_name = self.op_combo.get()
        op_key = self.reverse_ops_map.get(selected_name)
        op = self.operations.get(op_key)
        if not op:
            return

        # 清除旧控件
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        self.param_widgets.clear()

        params = op.get("params", [])
        label_map = {
            "aid": "用户 AID",
            "points": "积分数量",
            "sn": "设备 SN",
            "count": "发帖数量",
            "content": "帖子内容",
            "target_id": "目标ID"
        }

        row = 0
        for param in params:
            label_text = label_map.get(param, param.title())
            tk.Label(self.param_frame, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry = tk.Entry(self.param_frame, width=30)
            entry.grid(row=row, column=1, padx=5, pady=5)
            self.param_widgets[param] = entry
            row += 1

    def log(self, message):
        self.log_widget.log(message)

    def clear_log(self):
        self.log_widget.delete(1.0, tk.END)

    def start_operation(self):
        """统一入口，根据操作类型分发"""
        selected_name = self.op_combo.get()
        op_key = self.reverse_ops_map.get(selected_name)
        if not op_key:
            messagebox.showerror("❌ 错误", "未选择有效操作")
            return

        op = self.operations[op_key]

        # 保存邮箱密码到会话
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        session_state.email = email
        session_state.password = password

        base_url = self.get_base_url()

        # 分发执行
        if op["type"] == "admin":
            thread = threading.Thread(
                target=self.run_admin_operation,
                args=(op_key, email, password, base_url),
                daemon=True
            )
        else:
            thread = threading.Thread(
                target=self.run_user_operation,
                args=(op_key, email, password, base_url),
                daemon=True
            )
        thread.start()

    def run_user_operation(self, op_key, email, password, base_url):
        """执行普通用户操作"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            messagebox.showerror("❌ 错误", "请填写邮箱和密码")
            return
        if not op_key:
            messagebox.showerror("❌ 错误", "未选择有效操作")
            return

        self.log(f"🚀 开始执行用户操作: {self.operations[op_key]['name']}")

        try:
            token = login(self.session_manager, email, password, base_url)
            self.log("✅ 登录成功")
        except Exception as e:
            self.log(f"❌ 登录失败: {str(e)}")
            return

        # 特殊处理：批量发帖
        if op_key == "create_post":
            try:
                count = max(1, min(50, int(self.param_widgets["count"].get())))
            except:
                count = 1
            content = self.param_widgets["content"].get().strip() or "This is an automatically published test content."

            result = execute_operation(op_key, self.session_manager, token, base_url,
                                       count=count, content=content)

            for i, r in enumerate(result["results"]):
                status = "✅" if r["success"] else "❌"
                self.log(f"{status} 第 {i + 1} 篇: {r['msg']}")

            msg = "🎉 全部成功！" if result["all_success"] else "⚠️ 部分失败："
            self.log(f"\n{msg}成功 {result['success_count']}/{result['total']} 篇。")

        else:
            target_id = self.param_widgets.get("target_id", {}).get("get", lambda: "")().strip()
            if not target_id:
                self.log("❌ 请输入目标ID")
                return

            result = execute_operation(op_key, self.session_manager, token, base_url, target_id=target_id)
            if result["success"]:
                self.log("✅ 操作成功")
            else:
                self.log(f"❌ 操作失败: {result['msg']}")

    def run_admin_operation(self, op_key, email, password, base_url):
        """执行管理员操作（无需用户 token，可自动获取 AID）"""
        op_name = self.operations[op_key]["name"]
        self.log(f"🚀 开始执行管理员操作: {op_name}")

        # 获取 AID：优先使用输入框，否则尝试自动获取
        aid_entry = self.param_widgets.get("aid")
        if not aid_entry:
            self.log("❌ 错误：该操作需要 AID 参数")
            return

        aid = aid_entry.get().strip()

        # 如果未输入 AID，但提供了邮箱密码，则自动获取
        if not aid and email and password:
            self.log("🔍 AID 未输入，尝试自动获取...")
            try:
                user_token_result = self.session_manager.login_user(email, password, base_url)
                if not user_token_result["success"]:
                    self.log("❌ 自动获取 AID 失败：登录失败")
                    return
                user_token = user_token_result["token"]
                aid_result = get_user_aid(self.session_manager, user_token, base_url)
                if aid_result["success"]:
                    aid = aid_result["aid"]
                    self.log(f"✅ 自动获取 AID 成功: {aid}")
                else:
                    self.log(f"❌ 自动获取 AID 失败: {aid_result['msg']}")
                    return
            except Exception as e:
                self.log(f"❌ 自动获取 AID 异常: {str(e)}")
                return
        elif not aid:
            self.log("❌ 请输入 AID 或提供邮箱密码以自动获取")
            return

        # 获取积分
        try:
            points = int(self.param_widgets["points"].get())
        except ValueError:
            self.log("❌ 积分数必须是正整数")
            return

        # 执行管理员操作
        admin_result = execute_admin_operation(
            op_key=op_key,
            env=self.current_env,
            aid=aid,
            points=points,
            admin_username="dayuan_zhou",
            admin_password="Govee1234"
        )

        for r in admin_result["results"]:
            self.log(r["msg"])

        status = "🎉" if admin_result["all_success"] else "⚠️"
        self.log(f"\n{status} 管理员操作完成！成功 {admin_result['success_count']} 次。")

    def get_aid(self):
        """手动获取 AID 并弹窗"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not email or not password:
            messagebox.showerror("❌ 错误", "请先输入邮箱和密码")
            return

        base_url = self.get_base_url()
        try:
            result = self.session_manager.login_user(email, password, base_url)
            if not result["success"]:
                messagebox.showerror("❌ 登录失败", result["msg"])
                return
            token = result["token"]
            aid_result = get_user_aid(self.session_manager, token, base_url)
            if aid_result["success"]:
                aid = aid_result["aid"]
                self.log(f"🎯 获取 AID 成功: {aid}")
                AidPopup(self, aid)
            else:
                self.log(f"❌ 获取失败: {aid_result['msg']}")
                messagebox.showerror("❌ 获取失败", aid_result["msg"])
        except Exception as e:
            self.log(f"❌ 异常: {str(e)}")
            messagebox.showerror("❌ 错误", str(e))

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]