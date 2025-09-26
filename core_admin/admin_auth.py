# govee_community_tool/core_admin/admin_auth.py

import http.client
import json
from urllib.parse import urlparse


from config.admin_settings import ADMIN_BackendENV_CONFIG, ADMIN_LOGIN_PATH


def admin_login(env: str, username: str, password: str) -> dict:
    """
    管理员登录，获取 token 和用户信息（含 email）
    :param env: 环境 (prod/dev/test)
    :param username: 登录名
    :param password: 密码
    :return: {success: bool, token: str, user_info: {email, username}, msg: str}
    """
    base_domain = ADMIN_BackendENV_CONFIG.get(env)
    if not base_domain:
        return {"success": False, "msg": f"不支持的环境: {env}"}

    conn = http.client.HTTPSConnection(base_domain)
    payload = json.dumps({
        "loginName": username,
        "password": password
    })
    headers = {
        'Pragma': 'no-cache',
        'Content-Type': 'application/json'
    }

    try:
        conn.request("POST", ADMIN_LOGIN_PATH, payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        result = json.loads(data)

        if res.status == 200 and result.get("message") == "登录成功":
            token = result["token"]

            # ✅ 尝试从返回结果中提取用户信息
            user_info = result.get("data", {}) or {}
            email = user_info.get("email") or user_info.get("loginName") or username

            return {
                "success": True,
                "token": token,
                "user_info": {
                    "email": email,
                    "username": username
                },
                "msg": "登录成功"
            }
        else:
            msg = result.get("msg", result.get("message", "登录失败"))
            return {"success": False, "msg": msg}
    except Exception as e:
        return {"success": False, "msg": f"连接异常: {str(e)}"}
    finally:
        conn.close()