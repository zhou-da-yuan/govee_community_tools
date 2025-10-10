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
