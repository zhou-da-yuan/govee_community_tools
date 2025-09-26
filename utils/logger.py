# govee_community_tool/utils/logger.py

import os
from datetime import datetime

LOG_FILE = "logs/app.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


class SimpleLogger:
    """统一日志接口：写文件 + 转发到 GUI"""

    def __init__(self, log_func=None):
        """
        :param log_func: 接收 (message: str, tag: str) 的函数（通常是 LogText._log）
        """
        self.log_func = log_func
        self.file = open(LOG_FILE, "a", encoding="utf-8")
        import atexit
        atexit.register(self._close)

    def _clean(self, msg: str) -> str:
        """清理特殊字符：\xa0, \u200b 等"""
        return msg.replace('\xa0', ' ').replace('\u200b', '').strip()

    def _log(self, level: str, msg: str, *args, tag=None):
        # 格式化
        if args:
            if '%' in msg:
                formatted = msg % args
            else:
                formatted = msg.format(*args)
        else:
            formatted = str(msg)

        # 清理
        cleaned = self._clean(formatted)

        # 带时间戳的日志
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {cleaned}"

        # 写入文件
        try:
            self.file.write(log_entry + "\n")
            self.file.flush()
        except (ValueError, OSError):
            pass

        # 转发到 GUI
        if self.log_func:
            self.log_func(cleaned, tag)

    def info(self, msg, *args):
        self._log("INFO", msg, *args, tag="info")

    def error(self, msg, *args):
        self._log("ERROR", msg, *args, tag="error")

    def debug(self, msg, *args):
        self._log("DEBUG", msg, *args, tag="debug")

    def log(self, msg, *args):
        self._log("", msg, *args, tag=None)

    def _close(self):
        if not self.file.closed:
            self.file.close()