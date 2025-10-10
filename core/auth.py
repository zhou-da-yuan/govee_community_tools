# govee_community_tool/core/auth.py

import time


def login(session_manager, email: str, password: str, base_url: str, client_id: str = None) -> str:
    session = session_manager.get_session()
    url = f"{base_url}/account/rest/account/v1/login"
    payload = {
        "client": client_id or "5e972a68a408cada",  # 使用用户输入或默认值
        "email": email,
        "password": password,
        "key": "",
        "view": 0,
        "transaction": str(int(time.time() * 1000))
    }
    response = session.post(url, json=payload)
    result = response.json()
    if result.get("status") == 200:
        session.headers.update({"X-User-Email": email})
        return result['client']['token']
    raise Exception(f"登录失败: {result}")
