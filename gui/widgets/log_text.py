# govee_community_tool/gui/widgets/log_text.py

import tkinter.scrolledtext as scrolledtext


class LogText(scrolledtext.ScrolledText):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="black", fg="lightgreen", font=("Consolas", 9))

    def log(self, message: str):
        self.insert("end", message + "\n")
        self.see("end")