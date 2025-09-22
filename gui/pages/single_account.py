# govee_community_tool/gui/pages/single_account.py

import tkinter as tk
from tkinter import ttk, messagebox
from gui.widgets.log_text import LogText
from core.auth import login
from core.operations import OPERATIONS
from core.operations import execute_operation
from core.session_manager import SessionManager
import threading
import time
import random


class SingleAccountPage(ttk.Frame):
    def __init__(self, parent, current_env, change_env_callback):
        super().__init__(parent)
        self.current_env = current_env
        self.change_env_callback = change_env_callback
        self.session_manager = SessionManager()
        self.op_key_var = tk.StringVar()  # 当前选中的操作 key
        self.dynamic_widgets = []  # 存储动态控件，用于清除
        self.setup_ui()
        self.load_operations()  # 加载所有可用操作

    def setup_ui(self):
        # 1. 账号输入区
        account_frame = ttk.LabelFrame(self, text="🔑 账号信息", padding=15)
        account_frame.pack(fill=tk.X, pady=10)

        tk.Label(account_frame, text="📧 邮箱:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.email_entry = tk.Entry(account_frame, width=30, font=("Consolas", 10))
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(account_frame, text="🔒 密码:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.password_entry = tk.Entry(account_frame, width=30, font=("Consolas", 10), show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        # 2. 操作选择区
        op_frame = ttk.LabelFrame(self, text="⚙️ 操作选择", padding=15)
        op_frame.pack(fill=tk.X, pady=10)

        tk.Label(op_frame, text="选择操作:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.op_combo = ttk.Combobox(op_frame, textvariable=self.op_key_var, state="readonly", width=25)
        self.op_combo.grid(row=0, column=1, padx=5, pady=5)
        self.op_combo.bind("<<ComboboxSelected>>", self.on_operation_selected)

        # 3. 动态参数区
        self.param_frame = ttk.LabelFrame(self, text="📌 参数设置", padding=15)
        self.param_frame.pack(fill=tk.X, pady=10)

        self.param_widgets = {}  # 存储参数控件

        # 4. 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="▶️ 执行操作", style="Accent.TButton",
                   command=self.start_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)

        # 5. 日志输出
        log_frame = ttk.LabelFrame(self, text="📝 运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_widget = LogText(log_frame, height=15)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def load_operations(self):
        """加载所有支持的操作（排除批量类）"""
        # 只保留适合单账号的操作
        allowed_ops = {
            k: v for k, v in OPERATIONS.items()
            if k in [
                "create_post",

            ]
        }
        self.op_map = {key: info["name"] for key, info in allowed_ops.items()}
        self.op_combo["values"] = list(self.op_map.values())
        if self.op_map:
            self.op_combo.current(0)
            self.on_operation_selected()

    def on_operation_selected(self, event=None):
        """操作切换时，动态生成参数输入框"""
        # 清除旧控件
        for widget in self.dynamic_widgets:
            widget.destroy()
        self.dynamic_widgets.clear()
        self.param_widgets.clear()

        selected_name = self.op_combo.get()
        op_key = self.get_key_by_name(selected_name)
        op_info = OPERATIONS[op_key]

        row = 0

        # 根据操作类型决定需要哪些参数
        if op_key == "create_post":
            tk.Label(self.param_frame, text="发帖数量:").grid(row=row, column=0, sticky=tk.W, pady=3)
            count_spin = tk.Spinbox(self.param_frame, from_=1, to=50, width=10)
            count_spin.grid(row=row, column=1, padx=5, pady=3)
            self.param_widgets["count"] = count_spin
            row += 1

            tk.Label(self.param_frame, text="内容:").grid(row=row, column=0, sticky=tk.W, pady=3)
            content_entry = tk.Entry(self.param_frame, width=30, font=("Consolas", 10))
            content_entry.insert(0, "This is an automatically published test content.")
            content_entry.grid(row=row, column=1, padx=5, pady=3)
            self.param_widgets["content"] = content_entry

        else:
            # 其他操作只需一个 ID 输入
            tk.Label(self.param_frame, text="目标ID:").grid(row=row, column=0, sticky=tk.W, pady=3)
            target_entry = tk.Entry(self.param_frame, width=30, font=("Consolas", 10))
            target_entry.grid(row=row, column=1, padx=5, pady=3)
            self.param_widgets["target_id"] = target_entry

    def get_key_by_name(self, name):
        """通过显示名称反查操作 key"""
        for k, v in self.op_map.items():
            if v == name:
                return k
        return None

    def log(self, message):
        self.log_widget.log(message)

    def clear_log(self):
        self.log_widget.delete(1.0, tk.END)

    def start_operation(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        selected_name = self.op_combo.get()
        op_key = self.get_key_by_name(selected_name)

        if not email or not password:
            messagebox.showerror("❌ 错误", "请填写邮箱和密码")
            return
        if not op_key:
            messagebox.showerror("❌ 错误", "未选择有效操作")
            return

        base_url = self.get_base_url()

        # 开启线程执行
        thread = threading.Thread(
            target=self.run_operation,
            args=(op_key, email, password, base_url),
            daemon=True
        )
        thread.start()

    def run_operation(self, op_key, email, password, base_url):
        self.log(f"🚀 开始执行: {OPERATIONS[op_key]['name']}")

        try:
            token = login(self.session_manager, email, password, base_url)
            self.log("✅ 登录成功")
        except Exception as e:
            self.log(f"❌ 登录失败: {str(e)}")
            return

        if op_key == "create_post":
            count = int(self.param_widgets["count"].get())
            content = self.param_widgets["content"].get().strip() or "这是一条自动发布的测试内容。"

            result = execute_operation(
                op_key, self.session_manager, token, base_url,
                count=count, content=content
            )

            # 逐条打印结果
            for i, r in enumerate(result["results"]):
                status = "✅" if r["success"] else "❌"
                self.log(f"{status} 第 {i + 1} 篇: {r['msg']}")

            # 最终总结
            if result["success"]:
                if result["all_success"]:
                    self.log(f"\n🎉 批量发帖完成！成功 {result['success_count']}/{result['total']} 篇。")
                else:
                    self.log(f"\n⚠️  批量发帖完成，但部分失败：成功 {result['success_count']}/{result['total']} 篇。")
            else:
                self.log(f"\n❌ 所有发帖均失败！")

        else:
            target_id = self.param_widgets["target_id"].get().strip()
            if not target_id:
                self.log("❌ 请输入目标ID")
                return

            result = execute_operation(
                op_key, self.session_manager, token, base_url,
                target_id=target_id
            )

            if result["success"]:
                self.log("✅ 操作成功")
            else:
                self.log(f"❌ 操作失败: {result['msg']}")

    def _execute_post_batch(self, token, base_url, count, content):
        """批量发帖逻辑"""
        success_count = 0
        for i in range(count):
            try:
                from core.operations import OPERATIONS
                op = OPERATIONS["create_post"]

                # ✅ 调用 payload 时传入 content 参数
                title_suffix = f"{int(time.time()) % 10000}-{i + 1}"
                payload = op["payload"](title_suffix, content)  # ✅ 支持传入 content

                session = self.session_manager.get_session()
                headers = {**session.headers, 'Authorization': f'Bearer {token}'}
                url = op["url"](base_url)

                res = session.post(url, headers=headers, json=payload)

                if res.status_code == 200 and res.json().get("status") == 200:
                    post_id = res.json().get("data", {}).get("postId", "未知")
                    self.log(f"✅ 第 {i + 1} 篇发布成功 | Post ID: {post_id}")
                    success_count += 1
                else:
                    msg = res.json().get("msg", "未知错误")
                    self.log(f"❌ 第 {i + 1} 篇失败: {msg}")
            except Exception as e:
                self.log(f"❌ 异常: {str(e)}")
                continue
            time.sleep(random.uniform(1.5, 3.5))
        self.log(f"\n🎉 发帖完成！成功 {success_count}/{count} 篇。\n")

    def get_base_url(self):
        from config.settings import ENV_CONFIG
        return ENV_CONFIG[self.current_env]

    def on_environment_changed(self, new_env):
        self.current_env = new_env
        self.log(f"🔄 环境已切换至: {new_env.upper()}")
