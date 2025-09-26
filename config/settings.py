# govee_community_tool/config/settings.py

ENV_CONFIG = {
    'dev': 'https://dev-app2.govee.com',
    'pda': 'https://pda-app2.govee.com'
}

DEFAULT_ENV = 'dev'

BASE_HEADERS = {
    'appVersion': '7.2.00',
    'clientType': '0',
    'country': 'US',
    'envId': '1',
    'iotVersion': '1',
    'clientId': '5e972a68a408cada',
    'Content-Type': 'application/json',
}

# 👇 新增：默认操作延迟（秒）
DEFAULT_DELAY = {
    'min': 2,
    'max': 5
}

# ✅ 新增：管理员接口域名（与普通用户不同）
ADMIN_ENV_CONFIG = {
    "prod": "https://adminapi.govee.com",
    "dev": "https://dev-adminapi.govee.com",
    "test": "https://test-adminapi.govee.com"
}

# ✅ 新增：积分相关接口配置
POINTS_CONFIG = {
    "grant": {  # 积分发放
        "url": "/admin/v1/su-points/hand-on",
        "max_per_request": 5000
    },
    "deduct": {  # 积分扣除
        "url": "/admin/v1/points/deduction",
        "max_per_request": 500
    }
}