# govee_community_tool/gui/widgets/log_text.py

import tkinter.scrolledtext as scrolledtext
import threading
import queue
import os
from datetime import datetime

LOG_FILE = "logs/app.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


class LogText(scrolledtext.ScrolledText):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="black", fg="lightgreen", font=("Consolas", 9))
        self.tag_config("debug", foreground="cyan")
        self.tag_config("info", foreground="lightgreen")
        self.tag_config("error", foreground="red")

        # ✅ 确保 _is_destroyed 初始就存在
        self._is_destroyed = False

        # 线程安全队列
        self.log_queue = queue.Queue()

        # 打开日志文件
        self.log_file = open(LOG_FILE, "a", encoding="utf-8")

        # 启动轮询
        self._poll_queue()

        # 绑定销毁事件
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        """当控件被销毁时标记状态"""
        self._is_destroyed = True

    def _poll_queue(self):
        """主线程定期检查队列"""
        try:
            while True:
                # 非阻塞获取
                record = self.log_queue.get_nowait()
                self._write_to_gui_and_file(*record)
        except queue.Empty:
            pass
        finally:
            # ✅ 只有组件未被销毁才继续轮询
            if not self._is_destroyed:
                try:
                    self.after(50, self._poll_queue)
                except Exception:
                    # 防止 after 在销毁后抛异常（Tkinter 内部错误）
                    pass

    def _write_to_gui_and_file(self, message: str, tag=None):
        """真正写入 GUI 和文件（只在主线程执行）"""
        # ✅ 安全检查：防止在销毁后操作
        if self._is_destroyed:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # 写入文件
        try:
            self.log_file.write(log_entry + "\n")
            self.log_file.flush()
        except (ValueError, OSError):
            # 文件已关闭或不可写（如程序退出）
            pass

        # 写入 GUI
        try:
            self.insert("end", log_entry + "\n", tag)
            self.see("end")
        except Exception:
            # Tkinter 控件已销毁
            self._is_destroyed = True

    def _format(self, msg, *args):
        """安全格式化"""
        if args and isinstance(msg, str):
            try:
                if '%' in msg:
                    return msg % args
                elif '{}' in msg:
                    return msg.format(*args)
            except Exception:
                return str(msg) + " " + " ".join(map(str, args))
        return str(msg)

    def _log(self, message: str, tag=None):
        """线程安全的日志入口"""
        if threading.current_thread() is threading.main_thread():
            self._write_to_gui_and_file(message, tag)
        else:
            # 子线程：放入队列
            self.log_queue.put((message, tag))

    def debug(self, msg, *args):
        formatted = self._format(msg, *args)
        self._log(f"DEBUG: {formatted}", "debug")

    def info(self, msg, *args):
        formatted = self._format(msg, *args)
        self._log(f"INFO: {formatted}", "info")

    def error(self, msg, *args):
        formatted = self._format(msg, *args)
        self._log(f"ERROR: {formatted}", "error")

    def log(self, message):
        self._log(str(message))

    def __call__(self, *args, **kwargs):
        raise TypeError(
            f"❌ 不能调用 LogText 组件！\n"
            f"传入的参数: args={args}, kwargs={kwargs}\n"
            f"提示：请使用 .info() 或 .log() 方法。"
        )

    def destroy(self):
        """安全销毁控件"""
        # 防止重复关闭
        if hasattr(self, 'log_file') and not self.log_file.closed:
            self.log_file.close()
        self._is_destroyed = True
        super().destroy()