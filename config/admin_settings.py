# govee_community_tool/config/admin_settings.py

# 管理员后台域名（根据环境切换）
ADMIN_BackendENV_CONFIG = {
    "dev": "dev-backend.lanjingerp.com",
    "pda": "pda-backend.lanjingerp.com"
}

ADMIN_AdminApiENV_CONFIG = {
    "dev": "dev-adminapi.govee.com",
    "pda": "pda-adminapi.govee.com"
}

# 登录路径
ADMIN_LOGIN_PATH = "/user/rest/v2/login"

# 积分接口配置
POINTS_CONFIG = {
    "grant_points": {
        "url_path": "/admin/v1/su-points/hand-on",
        "max_per_request": 5000
    },
    "deduct_points": {
        "url_path": "/admin/v1/points/deduction",
        "max_per_request": 500
    }
}