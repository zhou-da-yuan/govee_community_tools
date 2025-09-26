# govee_community_tool/gui/widgets/log_text.py

import tkinter.scrolledtext as scrolledtext
import threading
import queue
from datetime import datetime


class LogText(scrolledtext.ScrolledText):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="black", fg="lightgreen", font=("Consolas", 9), insertbackground="white")
        self.tag_config("debug", foreground="cyan")
        self.tag_config("info", foreground="lightgreen")
        self.tag_config("error", foreground="red")

        # 标记控件是否已销毁
        self._is_destroyed = False

        # 线程安全队列（用于接收日志）
        self.log_queue = queue.Queue()

        # 启动轮询
        self._poll_queue()

        # 绑定销毁事件
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        self._is_destroyed = True

    def _poll_queue(self):
        """主线程定期检查队列"""
        try:
            while True:
                record = self.log_queue.get_nowait()
                self._write_to_gui(*record)
        except queue.Empty:
            pass
        finally:
            if not self._is_destroyed:
                try:
                    self.after(50, self._poll_queue)
                except Exception:
                    pass  # Tkinter 销毁后 ignore

    def _write_to_gui(self, message: str, tag=None):
        """只写入 GUI（主线程执行）"""
        if self._is_destroyed:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        try:
            self.insert("end", log_entry + "\n", tag)
            self.see("end")
        except Exception:
            self._is_destroyed = True

    def _log(self, message: str, tag=None):
        """线程安全入口"""
        if threading.current_thread() is threading.main_thread():
            self._write_to_gui(message, tag)
        else:
            self.log_queue.put((message, tag))

    def debug(self, msg, *args):
        self._log(f"DEBUG: {msg % args if args and '%' in msg else msg.format(*args) if args else msg}", "debug")

    def info(self, msg, *args):
        self._log(f"INFO: {msg % args if args and '%' in msg else msg.format(*args) if args else msg}", "info")

    def error(self, msg, *args):
        self._log(f"ERROR: {msg % args if args and '%' in msg else msg.format(*args) if args else msg}", "error")

    def log(self, msg, *args):
        self._log(msg % args if args and '%' in msg else msg.format(*args) if args else str(msg))

    def destroy(self):
        self._is_destroyed = True
        super().destroy()