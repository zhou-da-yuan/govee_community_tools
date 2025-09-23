# govee_community_tool/gui/widgets/log_text.py

import tkinter.scrolledtext as scrolledtext


class LogText(scrolledtext.ScrolledText):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="black", fg="lightgreen", font=("Consolas", 9))
        self.tag_config("debug", foreground="cyan")
        self.tag_config("info", foreground="lightgreen")
        self.tag_config("error", foreground="red")

    def _format(self, msg, *args):
        """安全格式化：支持 % 和 {}"""
        if args and isinstance(msg, str):
            try:
                if '%' in msg:
                    return msg % args
                elif '{}' in msg:
                    return msg.format(*args)
            except Exception as e:
                return str(msg) + " " + " ".join(map(str, args))
        return str(msg)

    def _log(self, message: str, tag=None):
        self.insert("end", message + "\n", tag)
        self.see("end")

    def debug(self, msg, *args):
        formatted = self._format(msg, *args)
        self._log(f"{formatted}", "debug")

    def info(self, msg, *args):
        formatted = self._format(msg, *args)
        self._log(f"{formatted}", "info")

    def error(self, msg, *args):
        formatted = self._format(msg, *args)
        self._log(f"{formatted}", "error")

    def log(self, message):  # 兼容旧接口
        self._log(str(message))

    def __call__(self, *args, **kwargs):
        # 🚨 拦截所有 () 调用
        raise TypeError(
            f"❌ 不能调用 LogText 组件！你写了类似 log_widget(...) 的代码。\n"
            f"传入的参数: args={args}, kwargs={kwargs}\n"
            f"提示：请使用 .info() 或 .log() 方法，而不是直接调用组件。"
        )
