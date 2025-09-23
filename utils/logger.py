# utils/logger.py

class SimpleLogger:
    """统一日志接口"""
    def __init__(self, log_func):
        self.log_func = log_func

    def info(self, msg, *args):
        formatted = msg % args if args else msg
        self.log_func(f"{formatted}")

    def error(self, msg, *args):
        formatted = msg % args if args else msg
        self.log_func(f"{formatted}")

    def debug(self, msg, *args):
        formatted = msg % args if args else msg
        self.log_func(f"{formatted}")