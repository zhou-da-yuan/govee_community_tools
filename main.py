# govee_community_tool/main.py

import tkinter as tk
from gui.main_window import MainWindow
import requests

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()