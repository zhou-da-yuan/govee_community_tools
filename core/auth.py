# govee_community_tool/core/auth.py

import time
from core.session_manager import SessionManager


def login(session_manager: SessionManager, email: str, password: str, base_url: str) -> str:
    session = session_manager.get_session()
    url = f"{base_url}/account/rest/account/v1/login"
    payload = {
        "client": "5e972a68a408cada",
        "email": email,
        "password": password,
        "key": "",
        "view": 0,
        "transaction": str(int(time.time() * 1000))
    }
    response = session.post(url, json=payload)
    result = response.json()
    if result.get("status") == 200:

        # 添加操作记录
        session.headers.update({"X-User-Email": email})

        return result['client']['token']
    raise Exception(f"登录失败: {result}")