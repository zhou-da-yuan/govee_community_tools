# gui/widgets/help_viewer.py

import tkinter as tk
from tkinter import ttk
import os
import re


class HelpViewer:
    """帮助文档查看器（支持多级标题和嵌套列表）"""

    @staticmethod
    def show_help(parent, title="📘 使用帮助", md_file=None, width=800, height=600):
        """
        显示帮助弹窗

        :param parent: 父窗口
        :param title: 弹窗标题
        :param md_file: Markdown 文件路径
        :param width: 宽度
        :param height: 高度
        """
        if md_file is None:
            md_file = os.path.join(os.path.dirname(__file__), "../../resources/help.md")
            md_file = os.path.abspath(md_file)

        help_window = tk.Toplevel(parent)
        help_window.title(title)
        help_window.geometry(f"{width}x{height}")
        help_window.transient(parent)
        help_window.grab_set()
        help_window.resizable(True, True)

        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            bg="#f9f9f9",
            fg="#333",
            spacing1=2,
            spacing2=2,
            spacing3=2,
            padx=10,
            pady=5
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 样式定义
        text_widget.tag_configure("h1", font=("微软雅黑", 16, "bold"), foreground="darkblue", spacing1=12, spacing3=12)
        text_widget.tag_configure("h2", font=("微软雅黑", 14, "bold"), foreground="blue", spacing1=10, spacing3=10)
        text_widget.tag_configure("h3", font=("微软雅黑", 12, "bold"), spacing1=8, spacing3=8)
        text_widget.tag_configure("h4", font=("微软雅黑", 11, "bold"), foreground="gray", spacing1=6, spacing3=6)
        text_widget.tag_configure("bold", font=("微软雅黑", 10, "bold"))
        text_widget.tag_configure("italic", font=("微软雅黑", 10, "italic"))
        text_widget.tag_configure("code", font=("Consolas", 9), background="#f0f0f0", foreground="#d73a49")
        text_widget.tag_configure("blockquote", font=("微软雅黑", 10, "italic"), foreground="gray", lmargin1=20, lmargin2=20)
        text_widget.tag_configure("hr", spacing1=10, spacing3=10)

        # 列表样式：不同层级不同符号和缩进
        text_widget.tag_configure("ul1", lmargin1=20, lmargin2=40)  # •
        text_widget.tag_configure("ul2", lmargin1=40, lmargin2=60)  # ◦
        text_widget.tag_configure("ul3", lmargin1=60, lmargin2=80)  # ▪
        text_widget.tag_configure("ul4", lmargin1=80, lmargin2=100)  # ▫

        if not os.path.exists(md_file):
            text_widget.insert(tk.END, f"❌ 帮助文件未找到：\n{md_file}\n\n请检查路径是否正确。")
            text_widget.config(state=tk.DISABLED)
            ttk.Button(help_window, text="关闭", command=help_window.destroy).pack(pady=5)
            return

        try:
            with open(md_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            text_widget.insert(tk.END, f"❌ 加载失败：\n{str(e)}")
            text_widget.config(state=tk.DISABLED)
            ttk.Button(help_window, text="关闭", command=help_window.destroy).pack(pady=5)
            return

        # 列表符号映射
        list_bullets = ["•", "◦", "▪", "▫"]
        indent_step = 2  # 每两个空格为一级缩进

        for line in lines:
            raw_line = line
            line = line.rstrip()

            if not line.strip():
                text_widget.insert(tk.END, "\n")
                continue

            # 分隔线
            if re.match(r'^[-*]{3,}\s*$', line.strip()):
                text_widget.insert(tk.END, "─" * 50 + "\n", "hr")
                continue

            # 标题
            if line.startswith("# "):
                text_widget.insert(tk.END, line[2:] + "\n", "h1")
                continue
            elif line.startswith("## "):
                text_widget.insert(tk.END, line[3:] + "\n", "h2")
                continue
            elif line.startswith("### "):
                text_widget.insert(tk.END, line[4:] + "\n", "h3")
                continue
            elif line.startswith("#### "):
                text_widget.insert(tk.END, line[5:] + "\n", "h4")
                continue

            # 引用
            if line.startswith("> "):
                start_idx = text_widget.index(tk.INSERT)
                content = line[2:]
                _apply_formatting(text_widget, content)
                text_widget.insert(tk.END, "\n")
                end_idx = text_widget.index(tk.INSERT)
                text_widget.tag_add("blockquote", start_idx, end_idx)
                continue

            # 检测列表：基于缩进的空格数判断层级
            leading_spaces = len(raw_line) - len(raw_line.lstrip())
            indent_level = leading_spaces // indent_step
            if indent_level > 3:
                indent_level = 3  # 最多支持 4 层（0~3）

            if line.lstrip().startswith("- "):
                # 提取列表项内容
                content = line.lstrip()[2:].strip()
                bullet = list_bullets[indent_level]

                start_idx = text_widget.index(tk.INSERT)
                text_widget.insert(tk.END, bullet + " ")
                _apply_formatting(text_widget, content)
                text_widget.insert(tk.END, "\n")
                end_idx = text_widget.index(tk.INSERT)
                text_widget.tag_add(f"ul{indent_level + 1}", start_idx, end_idx)
                continue

            # 默认普通段落
            _apply_formatting(text_widget, line)
            text_widget.insert(tk.END, "\n")

        text_widget.config(state=tk.DISABLED)
        ttk.Button(help_window, text="关闭", command=help_window.destroy).pack(pady=5)


def _apply_formatting(text_widget, text):
    """
    支持 **加粗**、*斜体*、`代码` 的内联格式化
    """
    parts = re.split(r'(`.*?`)', text)
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            text_widget.insert(tk.END, part[1:-1], "code")
        else:
            sub_parts = re.split(r'(\*\*.*?\*\*)', part)
            for sp in sub_parts:
                if sp.startswith("**") and sp.endswith("**"):
                    text_widget.insert(tk.END, sp[2:-2], "bold")
                else:
                    sub2 = re.split(r'(\*.*?\*)', sp)
                    for ssp in sub2:
                        if ssp.startswith("*") and ssp.endswith("*") and len(ssp) > 2:
                            text_widget.insert(tk.END, ssp[1:-1], "italic")
                        else:
                            text_widget.insert(tk.END, ssp)