# govee_community_tool/core/session_manager.py

import requests
from config.settings import BASE_HEADERS


class SessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self.session.verify = False  # 忽略 SSL 警告（测试用）

    def get_session(self):
        return self.session

    def close(self):
        self.session.close()