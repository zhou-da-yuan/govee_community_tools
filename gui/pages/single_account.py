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
        ttk.Button(btn_frame, text="🔍 获取 AID", command=self.get_aid).pack(side=tk.LEFT, padx=5)

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
                operations[key] = {
                    "name": op["name"],
                    "description": op.get("description", ""),
                    "params": op["params"],
                    "type": "user",
                    "defaults": op.get("defaults", {}),
                    "placeholders": op.get("placeholders", {})
                }
        for key, op in ADMIN_OPERATIONS.items():
            if op.get("support_single", False):
                operations[key] = {
                    "name": op["name"],
                    "description": op.get("description", ""),
                    "params": op["params"],
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

        params = op.get("params", [])
        label_map = {
            "aid": "用户 AID",
            "points": "积分数量",
            "sn": "设备 SN",
            "count": "发布数量",
            "content": "发布内容",
            "target_id": "目标帖子ID"
        }

        defaults = op.get("defaults", {})
        placeholders = op.get("placeholders", {})

        row = 0
        for param in params:
            label_text = label_map.get(param, param.title())
            tk.Label(self.param_frame, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="e")

            # 👉 创建 PlaceholderEntry
            entry = PlaceholderEntry(
                self.param_frame,
                placeholder=placeholders.get(param, ""),  # 使用占位符
                width=30,
                font=("Consolas", 10)
            )
            entry.grid(row=row, column=1, padx=5, pady=5)

            # 👉 设置默认值（真实内容）
            if param in defaults:
                entry.set(defaults[param])  # ⚠️ 关键：必须调用 .set()，不是 .insert()

            self.param_widgets[param] = entry
            row += 1

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
        client_id = self.client_id_entry.get().strip()  # 获取 ClientId
        session_state.clientId = client_id
        session_state.email = email
        session_state.password = password

        base_url = self.get_base_url()

        if op["type"] == "admin":
            thread = threading.Thread(
                target=self.run_admin_operation,
                args=(op_key, email, password, base_url, self.current_env),
                daemon=True
            )
        else:
            thread = threading.Thread(
                target=self.run_user_operation,
                args=(op_key, email, password, base_url, client_id, self.current_env),
                daemon=True
            )
        thread.start()

    def run_user_operation(self, op_key, email, password, base_url, client_id, current_env):
        if not email or not password:
            self.logger.error("❌ 请填写邮箱和密码")
            messagebox.showerror("❌ 错误", "请填写邮箱和密码")
            return
        if not op_key:
            self.logger.error("❌ 未选择有效操作")
            return

        self.logger.info(f"🚀 开始执行用户操作: {self.operations[op_key]['name']}")

        try:
            token = login(self.session_manager, email, password, base_url, client_id)
            self.logger.info("✅ 登录成功")
        except Exception as e:
            self.logger.error(f"❌ 登录失败: {str(e)}")
            return

        # === 特殊处理：发帖 ===
        if op_key == "create_post":
            try:
                count = max(1, min(50, int(self.param_widgets["count"].get())))
            except:
                count = 1
            content = self.param_widgets["content"].get().strip() or "This is an automatically published test content."

            result = execute_operation(op_key, self.session_manager, token, base_url,
                                       count=count, content=content, env=current_env)

            for i, r in enumerate(result["results"]):
                status = "✅" if r["success"] else "❌"
                self.logger.info(f"{status} 第 {i + 1} 篇: {r['msg']}")

            msg = "🎉 全部成功！" if result["all_success"] else "⚠️ 部分失败："
            self.logger.info(f"\n{msg}成功 {result['success_count']}/{result['total']} 篇。")

        # === 新增：处理评论帖子 ===
        elif op_key == "comment_post":
            try:
                count = max(1, min(100, int(self.param_widgets["count"].get())))  # 限制最多100条评论
            except:
                count = 1
            content = self.param_widgets["content"].get().strip()
            if not content:
                content = "This is the default comment content for testing"

            target_id = self.param_widgets["target_id"].get().strip()
            if not target_id:
                self.logger.error("❌ 请输入目标帖子ID")
                messagebox.showerror("❌ 错误", "请输入目标帖子ID")
                return

            self.logger.info(f"⏳ 开始发布 {count} 条评论到帖子 {target_id}...")

            success_count = 0
            results = []

            for i in range(count):
                try:
                    res = execute_operation(
                        op_key="comment_post",
                        session_manager=self.session_manager,
                        token=token,
                        base_url=base_url,
                        target_id=target_id,
                        content=content,
                        env=current_env
                    )

                    if res is True:
                        msg = f"评论 {i + 1}: 发布成功"
                        success = True
                        success_count += 1
                    else:
                        msg = f"评论 {i + 1}: 发布失败"
                        success = False

                except Exception as e:
                    msg = f"评论 {i + 1}: 异常 {str(e)}"
                    success = False
                    self.logger.error(f"评论异常: {str(e)}")

                results.append({"success": success, "msg": msg})
                self.logger.info("✅ 评论成功" + " " + msg if success else "❌ 评论失败" + " " + msg)
                time.sleep(random.uniform(1.5, 3.5))

            all_success = success_count == count
            status = "🎉" if all_success else "⚠️"
            self.logger.info(f"\n{status} 批量评论完成！成功 {success_count}/{count} 条。")

        # === 处理其他普通操作（如点赞、收藏等）===
        else:
            target_id = self.param_widgets.get("target_id", {}).get("get", lambda: "")().strip()
            if not target_id:
                self.logger.error("❌ 请输入目标ID")
                return

            result = execute_operation(op_key, self.session_manager, token, base_url, target_id=target_id)
            if result["success"]:
                self.logger.info("✅ 操作成功")
            else:
                self.logger.error(f"❌ 操作失败: {result['msg']}")

    def run_admin_operation(self, op_key, email, password, base_url):
        op_name = self.operations[op_key]["name"]
        self.logger.info(f"🚀 开始执行管理员操作: {op_name}")

        aid_entry = self.param_widgets.get("aid")
        if not aid_entry:
            self.logger.error("❌ 错误：该操作需要 AID 参数")
            return

        aid = aid_entry.get().strip()

        if not aid and email and password:
            self.logger.info("🔍 AID 未输入，尝试自动获取...")
            try:
                user_token_result = self.session_manager.login_user(email, password, base_url)
                if not user_token_result["success"]:
                    self.logger.error("❌ 自动获取 AID 失败：登录失败")
                    return
                user_token = user_token_result["token"]
                aid_result = get_user_aid(self.session_manager, user_token, base_url)
                if aid_result["success"]:
                    aid = aid_result["aid"]
                    self.logger.info(f"✅ 自动获取 AID 成功: {aid}")
                else:
                    self.logger.error(f"❌ 自动获取 AID 失败: {aid_result['msg']}")
                    return
            except Exception as e:
                self.logger.error(f"❌ 自动获取 AID 异常: {str(e)}")
                return
        elif not aid:
            self.logger.error("❌ 请输入 AID 或提供邮箱密码以自动获取")
            return

        try:
            points = int(self.param_widgets["points"].get())
        except ValueError:
            self.logger.error("❌ 积分数必须是正整数")
            return

        self.logger.info(f"⏳ 操作执行中，请等待...")
        admin_result = execute_admin_operation(
            op_key=op_key,
            env=self.current_env,
            aid=aid,
            points=points,
            admin_username="dayuan_zhou",
            admin_password="Govee1234"
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
