# govee_community_tool/core_admin/admin_session.py

import threading
from datetime import datetime, timedelta


class AdminSession:
    def __init__(self):
        self.token = None
        self.email = None  # ✅ 新增字段
        self.expires_at = None
        self.lock = threading.Lock()

    def is_valid(self):
        return self.token and self.expires_at and datetime.now() < self.expires_at

    def set_token(self, token: str, email: str = None, expires_in: int = 7200):
        with self.lock:
            self.token = token
            self.email = email
            self.expires_at = datetime.now() + timedelta(seconds=expires_in)

    def get_token(self) -> str:
        return self.token if self.is_valid() else None

    def get_email(self) -> str:
        return self.email or "unknown"  # ✅ 提供 fallback

    def clear(self):
        with self.lock:
            self.token = None
            self.email = None
            self.expires_at = None
