# govee_community_tool/core/session_manager.py

import requests
import time
from typing import Dict, Optional
from config.settings import BASE_HEADERS
from core.auth import login as auth_login


class SessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self.session.verify = False  # 测试环境忽略 SSL

        # 缓存每个用户的登录信息 { email: { 'token': str, 'aid': str, 'base_url': str, 'expires_at': float } }
        self._user_sessions: Dict[str, dict] = {}

    def get_session(self) -> requests.Session:
        """获取底层会话对象"""
        return self.session

    def login_user(self, email: str, password: str, base_url: str, client_id: str = None) -> dict:
        """
        登录用户，缓存 token 和过期时间
        :return: { 'success': bool, 'token': str or None, 'msg': str }
        """
        cached = self._user_sessions.get(email)

        # 如果已登录且 token 未过期，直接返回
        if cached and cached['base_url'] == base_url and cached['expires_at'] > time.time():
            return {
                "success": True,
                "token": cached["token"],
                "msg": "✅ 使用缓存的登录态"
            }

        # 否则重新登录
        try:
            token = auth_login(self, password=password, email=email, base_url=base_url, client_id=client_id)
            if token:
                # 假设 token 有效期为 2 小时（7200 秒），实际可根据响应头调整
                expires_at = time.time() + 7200

                self._user_sessions[email] = {
                    "token": token,
                    "base_url": base_url,
                    "expires_at": expires_at
                }
                return {
                    "success": True,
                    "token": token,
                    "msg": "🎉 登录成功并缓存"
                }
            else:
                return {
                    "success": False,
                    "token": None,
                    "msg": "❌ 登录失败：认证接口未返回 token"
                }
        except Exception as e:
            return {
                "success": False,
                "token": None,
                "msg": f"❌ 登录异常: {str(e)}"
            }

    def get_token(self, email: str) -> Optional[str]:
        """获取指定用户的 token（如果未过期）"""
        cached = self._user_sessions.get(email)
        if cached and cached['expires_at'] > time.time():
            return cached['token']
        return None

    def is_logged_in(self, email: str, base_url: str) -> bool:
        """检查用户是否已在该 base_url 下登录且 token 有效"""
        cached = self._user_sessions.get(email)
        return (
                cached is not None and
                cached['base_url'] == base_url and
                cached['expires_at'] > time.time()
        )

    def clear_session(self, email: str = None):
        """清除某个用户或所有用户的缓存"""
        if email:
            self._user_sessions.pop(email, None)
        else:
            self._user_sessions.clear()

    def close(self):
        self.session.close()
