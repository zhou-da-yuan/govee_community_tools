# utils/logger.py

import os
from datetime import datetime

LOG_FILE = "logs/app.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


class SimpleLogger:
    """统一日志接口，支持 GUI 和文件"""

    def __init__(self, log_func):
        self.log_func = log_func
        self.file = open(LOG_FILE, "a", encoding="utf-8")
        import atexit
        atexit.register(self._close)

    def _log(self, level, msg, *args):
        formatted = msg % args if args and '%' in msg else msg.format(*args) if args else msg
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{formatted}"

        # 写入文件
        self.file.write(log_entry + "\n")
        self.file.flush()

        # 调用 GUI 显示
        self.log_func(log_entry)

    def info(self, msg, *args):
        self._log("INFO", msg, *args)

    def error(self, msg, *args):
        self._log("ERROR", msg, *args)

    def debug(self, msg, *args):
        self._log("DEBUG", msg, *args)

    def _close(self):
        if not self.file.closed:
            self.file.close()