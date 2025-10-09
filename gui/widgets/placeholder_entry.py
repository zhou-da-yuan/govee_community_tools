import tkinter as tk


class PlaceholderEntry(tk.Entry):
    def __init__(self, parent, placeholder="", color_placeholder="gray", color_normal="black", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.placeholder = placeholder
        self.color_placeholder = color_placeholder
        self.color_normal = color_normal
        self.is_placeholder = True

        # 直接使用 super().insert，避免触发重写的 insert
        super().insert(0, self.placeholder)
        self.config(fg=self.color_placeholder)

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, event):
        if self.is_placeholder:
            self.delete(0, "end")
            self.config(fg=self.color_normal)
            self.is_placeholder = False

    def _on_focus_out(self, event):
        if not self.get().strip():
            self.delete(0, "end")
            super().insert(0, self.placeholder)  # 用 super() 避免触发 insert 重写
            self.config(fg=self.color_placeholder)
            self.is_placeholder = True

    def get(self):
        value = super().get()
        return "" if self.is_placeholder or not value.strip() else value

    def clear(self):
        self.delete(0, "end")
        super().insert(0, self.placeholder)
        self.config(fg=self.color_placeholder)
        self.is_placeholder = True

    def set(self, text):
        self.delete(0, "end")
        if text:
            super().insert(0, text)
            self.config(fg=self.color_normal)
            self.is_placeholder = False
        else:
            super().insert(0, self.placeholder)
            self.config(fg=self.color_placeholder)
            self.is_placeholder = True

    def insert(self, index, string):
        """重写 insert，确保脱离 placeholder 状态"""
        if self.is_placeholder:
            self.delete(0, "end")
            self.config(fg=self.color_normal)
            self.is_placeholder = False
        super().insert(index, string)