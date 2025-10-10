# govee_community_tool/core_admin/admin_operations.py

import requests
import json
from typing import Dict, Any
from config.admin_settings import ADMIN_AdminApiENV_CONFIG, POINTS_CONFIG
from .admin_session import AdminSession
from utils.history import save_history  # ✅ 导入历史记录模块

# --- 全局会话 ---
_admin_session = AdminSession()

# --- 管理员操作定义 ---
ADMIN_OPERATIONS = {
    "grant_points": {
        "name": "🎁 积分发放(活动奖励)",
        "description": "向指定用户发放积分",
        "params": ["aid", "points"],
        "placeholders": {
            "aid": "输入了账号信息则无需输入AID",
        },
        "support_single": True,
        "method": "POST",
        "url_path": lambda: POINTS_CONFIG["grant_points"]["url_path"],
        "payload": lambda aid, points: {
            "title": "积分发放",
            "type": "13",
            "integralList": [
                {
                    "userList": [str(aid)],
                    "integral": int(points)
                }
            ],
            "isSend": 1
        }
    },
    "deduct_points": {
        "name": "🚫 积分扣除",
        "description": "扣除指定用户积分",
        "params": ["aid", "points"],
        "placeholders": {
            "aid": "输入了账号信息则无需输入AID",
        },
        "support_single": True,
        "method": "POST",
        "url_path": lambda: POINTS_CONFIG["deduct_points"]["url_path"],
        "payload": lambda aid, points: {
            "userIds": [str(aid)],
            "points": str(points),
            "remarks": "积分扣除",
            "reason": "1",
            "content": "Suspected to be a spam.",
            "causeId": 1
        }
    },
    "export_report": {
        "name": "📊 导出报表",
        "description": "导出管理员报表",
        "params": ["date_range"],
        "support_single": False,
    }
}


# --- 工具函数 ---
def _get_admin_token(env: str, username: str, password: str) -> tuple:
    """
    获取管理员 token 和邮箱
    返回: (token: str, email: str)
    """
    if _admin_session.is_valid():
        return _admin_session.get_token(), _admin_session.get_email()

    from .admin_auth import admin_login
    result = admin_login(env, username, password)
    if result["success"]:
        token = result["token"]
        email = result.get("user_info", {}).get("email") or username or "unknown"

        # ✅ 保存 token 和 email
        _admin_session.set_token(token, email=email)
        return token, email
    else:
        raise Exception(f"登录失败: {result['msg']}")


# --- 核心执行函数 ---
def execute_admin_operation(
        op_key: str,
        env: str,
        aid: str,
        points: int,
        admin_username: str,
        admin_password: str
) -> Dict[str, Any]:
    """
    统一执行管理员操作（支持自动分批 + 操作记录）
    """
    if op_key not in ADMIN_OPERATIONS:
        result = {"success": False, "results": [{"success": False, "msg": "不支持的操作"}]}
        # 🔽 记录非法操作尝试
        save_history({
            "operation": "未知操作",
            "email": admin_username,
            "target_id": aid,
            "result": "failed",
            "env": env,
            "details": {"error": "不支持的操作"}
        })
        return result

    op = ADMIN_OPERATIONS[op_key]
    op_name = op["name"]

    try:
        token, email = _get_admin_token(env, admin_username, admin_password)
    except Exception as e:
        result = {"success": False, "results": [{"success": False, "msg": str(e)}]}
        save_history({
            "operation": op_name,
            "email": admin_username,
            "target_id": aid,
            "result": "failed",
            "env": env,
            "details": {"error": str(e)}
        })
        return result

    base_url = f"https://{ADMIN_AdminApiENV_CONFIG[env]}"
    api_url = base_url + op["url_path"]()
    max_per = POINTS_CONFIG[op_key]["max_per_request"]

    success_count = 0
    results = []

    remaining = points
    while remaining > 0:
        current = min(remaining, max_per)
        payload = op["payload"](aid, current)
        headers = {
            'Authorization': f'Bearer {token}',
            'originFrom': 'erp',
            'Content-Type': 'application/json'
        }

        try:
            res = requests.post(api_url, headers=headers, json=payload, timeout=10, verify=False)
            # 解析响应
            try:
                response_data = res.json()
            except json.JSONDecodeError:
                response_data = {"raw": res.text, "status_code": res.status_code}

            # 📝 记录本次操作历史（✅ 每次请求都审计）
            save_history({
                "operation": op_name,
                "email": email,
                "target_id": aid,
                "result": "success" if (
                        res.status_code == 200 and response_data.get("status") in [200, 0]) else "failed",
                "env": env,
                "details": response_data
            })

            if res.status_code == 200:
                if response_data.get("status") in [200, 0]:
                    msg = f"✅ 成功 {op_name} {current} 积分"
                    results.append({"success": True, "msg": msg})
                    success_count += 1
                else:
                    msg = response_data.get("message", "未知错误")
                    error_msg = f"❌ {op_name}失败: {msg}"
                    results.append({"success": False, "msg": error_msg})
            else:
                error_msg = f"❌ HTTP {res.status_code}"
                results.append({"success": False, "msg": error_msg})

        except Exception as e:
            error_msg = f"❌ 请求异常: {str(e)}"
            results.append({"success": False, "msg": error_msg})
            # 🔽 记录异常
            save_history({
                "operation": op_name,
                "email": email,
                "target_id": aid,
                "result": "failed",
                "env": env,
                "details": {"error": error_msg}
            })

        remaining -= current

    return {
        "success": success_count > 0,
        "all_success": len(results) == success_count,
        "success_count": success_count,
        "results": results
    }
