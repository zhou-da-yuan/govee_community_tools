# govee_community_tool/gui/pages/single_account.py

import tkinter as tk
from tkinter import ttk, messagebox

from gui.widgets.aid_popup import AidPopup
from gui.widgets.log_text import LogText
from core.auth import login
from core.operations import OPERATIONS, get_user_aid
from core.operations import execute_operation
from core_admin.admin_operations import ADMIN_OPERATIONS, execute_admin_operation
from core.session_manager import SessionManager
from core.session_state import session_state

from utils.logger import SimpleLogger
from gui.widgets.placeholder_entry import PlaceholderEntry

import threading
import time
import random


class SingleAccountPage(ttk.Frame):
    def __init__(self, parent, current_env, change_env_callback):
        super().__init__(parent)
        self.current_env = current_env
        self.change_env_callback = change_env_callback
        self.session_manager = SessionManager()
        self.op_key_var = tk.StringVar()
        self.operations = {}
        self.op_map = {}
        self.reverse_ops_map = {}
        self.param_widgets = {}

        self.setup_ui()
        self.load_operations()
        self.update_operation_dropdown()

        # ✅ 创建 logger（必须在 setup_ui 之后）
        self.logger = SimpleLogger(log_func=self.log_widget._log)

    def setup_ui(self):
        account_frame = ttk.LabelFrame(self, text="🔑 账号信息", padding=15)
        account_frame.pack(fill=tk.X, pady=10)

        # 邮箱输入
        tk.Label(account_frame, text="📧 邮箱:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.email_entry = tk.Entry(account_frame, width=30, font=("Consolas", 10))
        self.email_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        if session_state.email:
            self.email_entry.insert(0, session_state.email)

        # 新增 ClientId 输入
        # 修改为使用 PlaceholderEntry 并添加占位符
        tk.Label(account_frame, text="🏷 Client ID:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        self.client_id_entry = PlaceholderEntry(
            account_frame,
            placeholder="输入该账号登录过的设备的clientId",  # 添加灰色提示文字
            width=30,
            font=("Consolas", 10)
        )
        self.client_id_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        if session_state.clientId:
            self.client_id_entry.set(session_state.clientId)  # 使用 set 方法设置初始值

        # 密码输入（调整为第二列起始）
        tk.Label(account_frame, text="🔒 密码:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.password_entry = tk.Entry(account_frame, width=30, font=("Consolas", 10), show="*")
        self.password_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        if session_state.password:
            self.password_entry.insert(0, session_state.password)

        op_frame = ttk.LabelFrame(self, text="⚙️ 操作选择", padding=15)
        op_frame.pack(fill=tk.X, pady=10)

        tk.Label(op_frame, text="选择操作:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.op_combo = ttk.Combobox(op_frame, state="readonly", width=25)
        self.op_combo.grid(row=0, column=1, padx=5, pady=5)
        self.op_combo.bind("<<ComboboxSelected>>", self.on_operation_selected)

        self.param_frame = ttk.LabelFrame(self, text="📌 参数设置", padding=15)
        self.param_frame.pack(fill=tk.X, pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="▶️ 执行操作", style="Accent.TButton",
                   command=self.start_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 获取账号 AID", command=self.get_aid).pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(self, text="📝 运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.log_widget = LogText(log_frame, height=15)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    # 👉 使用 logger 封装 log
    def log(self, message, level="info"):
        getattr(self.logger, level)(message)

    def clear_log(self):
        self.log_widget.delete(1.0, tk.END)

    def load_operations(self):
        operations = {}
        for key, op in OPERATIONS.items():
            if op.get("support_single", False):
                # 处理 params 为 list[dict] 的新格式
                processed_params = []
                for p in op.get("params", []):
                    if isinstance(p, str):
                        # 兼容旧格式（可选）
                        processed_params.append({"name": p, "label": p.title()})
                    else:
                        processed_params.append(p)

                operations[key] = {
                    "name": op["name"],
                    "description": op.get("description", ""),
                    "params": processed_params,  # 现在是带 label 的 dict 列表
                    "type": "user",
                    "defaults": op.get("defaults", {}),
                    "placeholders": op.get("placeholders", {})
                }
        # 同样处理 ADMIN_OPERATIONS（略，结构相同）
        for key, op in ADMIN_OPERATIONS.items():
            if op.get("support_single", False):
                processed_params = []
                for p in op.get("params", []):
                    if isinstance(p, str):
                        processed_params.append({"name": p, "label": p.title()})
                    else:
                        processed_params.append(p)
                operations[key] = {
                    "name": op["name"],
                    "description": op.get("description", ""),
                    "params": processed_params,
                    "type": "admin",
                    "defaults": op.get("defaults", {}),
                    "placeholders": op.get("placeholders", {})
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
        selected_name = self.op_combo.get()
        op_key = self.reverse_ops_map.get(selected_name)
        op = self.operations.get(op_key)
        if not op:
            return

        # 清除旧控件
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        self.param_widgets.clear()

        params = op.get("params", [])  # 现在是 [{"name": ..., "label": ...}, ...]

        defaults = op.get("defaults", {})
        placeholders = op.get("placeholders", {})

        # 双列布局
        for idx, param_info in enumerate(params):
            param_name = param_info["name"]
            label_text = param_info["label"]  # 👈 直接使用定义好的 label

            row = idx // 2
            col_offset = (idx % 2) * 2

            tk.Label(self.param_frame, text=label_text).grid(
                row=row, column=col_offset, padx=5, pady=5, sticky="e"
            )

            entry = PlaceholderEntry(
                self.param_frame,
                placeholder=placeholders.get(param_name, ""),
                width=28,
                font=("Consolas", 10)
            )
            entry.grid(row=row, column=col_offset + 1, padx=5, pady=5, sticky="w")

            if param_name in defaults:
                entry.set(defaults[param_name])

            self.param_widgets[param_name] = entry

    def start_operation(self):
        selected_name = self.op_combo.get()
        op_key = self.reverse_ops_map.get(selected_name)
        if not op_key:
            self.logger.error("❌ 错误：未选择有效操作")
            messagebox.showerror("❌ 错误", "未选择有效操作")
            return

        op = self.operations[op_key]

        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        client_id = self.client_id_entry.get().strip()
        session_state.clientId = client_id
        session_state.email = email
        session_state.password = password

        base_url = self.get_base_url()

        # ✅ 自动收集所有参数
        kwargs = {}
        for param_name, entry_widget in self.param_widgets.items():
            value = entry_widget.get().strip()
            if value:  # 只传非空值（或根据需求改为 always 传）
                kwargs[param_name] = value

        if op["type"] == "admin":
            thread = threading.Thread(
                target=self.run_admin_operation,
                args=(op_key, email, password, base_url, self.current_env),
                kwargs=kwargs,  # 👈 传入参数
                daemon=True
            )
        else:
            thread = threading.Thread(
                target=self.run_user_operation,
                args=(op_key, email, password, base_url, client_id, self.current_env),
                kwargs=kwargs,  # 👈 传入参数
                daemon=True
            )
        thread.start()

    def run_user_operation(self, op_key, email, password, base_url, client_id, current_env, **kwargs):
        if not email or not password:
            self.logger.error("❌ 请填写邮箱和密码")
            return

        self.logger.info(f"🚀 开始执行用户操作: {self.operations[op_key]['name']}")

        try:
            token = login(self.session_manager, email, password, base_url, client_id)
            self.logger.info("✅ 登录成功")
        except Exception as e:
            self.logger.error(f"❌ 登录失败: {str(e)}")
            return

        # ✅ 直接传递所有参数给 execute_operation
        try:
            result = execute_operation(
                op_key=op_key,
                session_manager=self.session_manager,
                token=token,
                base_url=base_url,
                env=current_env,
                **kwargs  # 👈 全部参数透传
            )

            # 统一日志处理（兼容 dict 和 bool）
            if isinstance(result, dict) and "results" in result:
                for i, r in enumerate(result["results"]):
                    status = "✅" if r["success"] else "❌"
                    self.logger.info(f"{status} 第 {i + 1} 次: {r['msg']}")
                msg = "🎉 全部成功！" if result["all_success"] else "⚠️ 部分失败："
                self.logger.info(f"\n{msg}成功 {result['success_count']}/{result['total']} 次。")
            elif result is True:
                self.logger.info("✅ 操作成功")
            else:
                self.logger.error("❌ 操作失败")

        except Exception as e:
            self.logger.error(f"❌ 操作异常: {str(e)}")

    def run_admin_operation(self, op_key, email, password, base_url, current_env, **kwargs):
        op_name = self.operations[op_key]["name"]
        self.logger.info(f"🚀 开始执行管理员操作: {op_name}")

        # 尝试从 kwargs 获取 aid，若无则尝试自动获取
        aid = kwargs.get("aid", "").strip()
        if not aid and email and password:
            self.logger.info("🔍 AID 未输入，尝试自动获取...")
            try:
                user_token_result = self.session_manager.login_user(email, password, base_url)
                if user_token_result["success"]:
                    user_token = user_token_result["token"]
                    aid_result = get_user_aid(self.session_manager, user_token, base_url)
                    if aid_result["success"]:
                        aid = aid_result["aid"]
                        self.logger.info(f"✅ 自动获取 AID 成功: {aid}")
                    else:
                        self.logger.error(f"❌ 自动获取 AID 失败: {aid_result['msg']}")
                        return
                else:
                    self.logger.error("❌ 自动获取 AID 失败：登录失败")
                    return
            except Exception as e:
                self.logger.error(f"❌ 自动获取 AID 异常: {str(e)}")
                return
        elif not aid:
            self.logger.error("❌ 请输入 AID 或提供邮箱密码以自动获取")
            return

        # 从 kwargs 获取 points
        points_str = kwargs.get("points", "").strip()
        try:
            points = int(points_str)
            if points <= 0:
                raise ValueError
        except (ValueError, TypeError):
            self.logger.error("❌ 积分数必须是正整数")
            return

        # 执行操作（只传必要参数）
        admin_result = execute_admin_operation(
            op_key=op_key,
            env=current_env,
            aid=aid,
            points=points,
        )

        for r in admin_result["results"]:
            self.logger.info(r["msg"])

        status = "🎉" if admin_result["all_success"] else "⚠️"
        self.logger.info(f"\n{status} 管理员操作完成！成功 {admin_result['success_count']} 次。")

    def get_aid(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        client_id = self.client_id_entry.get().strip()  # 获取 ClientId

        if not email or not password:
            self.logger.error("❌ 请先输入邮箱和密码")
            messagebox.showerror("❌ 错误", "请先输入邮箱和密码")
            return

        base_url = self.get_base_url()
        try:
            result = self.session_manager.login_user(email, password, base_url, client_id)
            if not result["success"]:
                self.logger.error(f"❌ 登录失败: {result['msg']}")
                messagebox.showerror("❌ 登录失败", result["msg"])
                return
            token = result["token"]
            aid_result = get_user_aid(self.session_manager, token, base_url)
            if aid_result["success"]:
                aid = aid_result["aid"]
                self.logger.info(f"🎯 获取 AID 成功: {aid}")
                AidPopup(self, aid)
            else:
                self.logger.error(f"❌ 获取失败: {aid_result['msg']}")
                messagebox.showerror("❌ 获取失败", aid_result["msg"])
        except Exception as e:
            self.logger.error(f"❌ 异常: {str(e)}")
            messagebox.showerror("❌ 错误", str(e))

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.logger.info(f"🔄 环境已切换至: {new_env.upper()}")
