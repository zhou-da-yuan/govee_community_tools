# gui/widgets/aid_popup.py

import tkinter as tk
from tkinter import ttk, messagebox


class AidPopup:
    def __init__(self, parent, aid: str):
        """
        显示包含 AID 的弹窗。
        :param parent: 父级窗口
        :param aid: 要显示的 AID 字符串
        """
        self.parent = parent
        self.aid = aid
        self.style = ttk.Style()

        # 创建弹窗
        self.popup = tk.Toplevel(self.parent)
        self.popup.title("🎯 获取到的 AID")
        self.popup.geometry("400x180")
        self.popup.resizable(False, False)
        self.popup.transient(self.parent)
        self.popup.grab_set()

        # 设置整体背景色（Toplevel 背景）
        self.popup.configure(bg="#f0f0f0")

        # 居中
        self.center_window()

        # 标题标签（使用 tk.Label 支持颜色）
        tk.Label(
            self.popup,
            text="您的 AID 如下：",
            font=("微软雅黑", 10),
            bg="#f0f0f0",
            fg="black"
        ).pack(pady=(15, 5))

        # 使用普通 tk.Entry 以便自由设置颜色（不使用 ttk.Entry）
        self.aid_entry_var = tk.StringVar(value=aid)
        self.aid_entry = tk.Entry(
            self.popup,
            textvariable=self.aid_entry_var,
            width=40,
            font=("Consolas", 10),
            bg="white",
            fg="black",
            state="readonly",
            relief="solid",
            highlightbackground="#ccc"
        )
        self.aid_entry.pack(padx=20, pady=10)

        # 按钮区域
        btn_frame = tk.Frame(self.popup, bg="#f0f0f0")  # 使用 tk.Frame
        btn_frame.pack(pady=10)

        # 使用 tk.Button（支持直接设置颜色）
        tk.Button(
            btn_frame,
            text="📋 复制并关闭",
            bg="#4CAF50",
            fg="white",
            font=("微软雅黑", 9),
            borderwidth=0,
            padx=10,
            pady=3,
            command=self.copy_and_close
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="❌ 关闭",
            bg="#f44336",
            fg="white",
            font=("微软雅黑", 9),
            borderwidth=0,
            padx=10,
            pady=3,
            command=self.popup.destroy
        ).pack(side=tk.LEFT, padx=5)

    def center_window(self):
        self.popup.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (self.popup.winfo_width() // 2)
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (self.popup.winfo_height() // 2)
        self.popup.geometry(f"+{x}+{y}")

    def copy_and_close(self):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.aid)
        if hasattr(self.parent, 'log'):
            self.parent.log("📋 AID 已复制到剪贴板")
        self.popup.destroy()