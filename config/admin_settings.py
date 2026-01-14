# govee_community_tool/config/admin_settings.py

# 管理员后台域名（根据环境切换）
ADMIN_BackendENV_CONFIG = {
    "dev": "dev-backend.lanjingerp.com",
    "pda": "dev-backend.lanjingerp.com"
}

ADMIN_AdminApiENV_CONFIG = {
    "dev": "dev-adminapi.govee.com",
    "pda": "pda-adminapi.govee.com"
}

# 管理员账号密码（按环境配置）
ADMIN_CREDENTIALS = {
    "dev": {
        "username": "dayuan_zhou",
        "password": "Govee12345"
    },
    "pda": {
        "username": "dayuan_zhou",
        "password": "Govee12345"
    }
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
