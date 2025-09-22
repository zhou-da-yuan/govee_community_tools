# govee_community_tool/main.py

import tkinter as tk
from utils import file_loader
from gui.main_window import MainWindow
import requests
import os

# 导入版本信息
try:
    from config.__version__ import __version__, __author__, __email__
except ImportError:
    __version__ = "未知"
    __author__ = "未知"
    __email__ = "未知"


def ensure_resources():
    resources_dir = os.path.join(os.path.dirname(__file__), "resources")
    help_file = file_loader.resource_path("resources/help.md")
    if not os.path.exists(help_file):
        os.makedirs(resources_dir, exist_ok=True)
        with open(help_file, "w", encoding="utf-8") as f:
            f.write("# 默认帮助文档\n\n请编辑此文件以更新帮助内容。")


if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    ensure_resources()
    root = tk.Tk()
    app = MainWindow(root)

    # 可选：在窗口标题显示版本
    root.title(f"Govee 社区工具 v{__version__}")

    root.mainloop()