# gui/widgets/tooltip.py
import tkinter as tk
from tkinter import ttk


def add_tooltip(widget, text: str):
    """
    为任意 Tkinter widget 添加鼠标悬停提示（Tooltip）

    :param widget: 要添加提示的控件（如 Button, Entry 等）
    :param text: 提示文本
    """
    if widget is None:
        return  # 安全防护：防止传入 None

    def on_enter(event):
        # 创建提示窗口
        x, y, _, _ = widget.bbox("insert") if hasattr(widget, "bbox") else (0, 0)
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25

        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)  # 去除窗口边框
        tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            tooltip,
            text=text,
            background="#ffffe0",
            foreground="black",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9, "normal"),
            padding=(5, 2)
        )
        label.pack()
        widget.tooltip = tooltip  # 保存引用

    def on_leave(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)