# govee_community_tool/config/settings.py
import os
import sys
from pathlib import Path
import shutil

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

DEFAULT_DELAY = {
    'min': 2,
    'max': 5
}


def is_frozen():
    return getattr(sys, 'frozen', False)


# 确定 BASE_DIR：程序运行根目录
if is_frozen():
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent

# 数据目录：始终是程序目录下的 data/accounts/
DATA_DIR = BASE_DIR / "data"
RESOURCE_DIR = DATA_DIR / "accounts"

# ✅ 账号文件路径：永远指向 data/accounts/
ENV_TO_FILE = {
    "dev": RESOURCE_DIR / "accounts_dev.json",
    "pda": RESOURCE_DIR / "accounts_pda.json",
}

# ✅ 资源源：打包时是 _MEIPASS/data/accounts，开发时是项目中的 data/accounts
if is_frozen():
    RESOURCE_SRC = Path(sys._MEIPASS) / "data" / "accounts"
else:
    RESOURCE_SRC = BASE_DIR / "data" / "accounts"

# 创建 data/ 目录
DATA_DIR.mkdir(exist_ok=True)


# --- 初始化：首次运行，复制默认账号配置 ---
def initialize_data_dir():
    """ 初始化 data/accounts/ 目录 """
    # 确保 data/ 目录存在
    DATA_DIR.mkdir(exist_ok=True)

    # 如果 data/accounts 已存在，直接跳过（开发 or 已初始化）
    if RESOURCE_DIR.exists():
        print(f"📁 账号目录已存在: {RESOURCE_DIR}")
        return

    # 只有在打包环境下，且目标目录不存在时，才尝试复制内置模板
    if is_frozen():
        if RESOURCE_SRC.exists():
            print(f"📦 首次运行，正在初始化账号配置到: {RESOURCE_DIR}")
            try:
                shutil.copytree(RESOURCE_SRC, RESOURCE_DIR)
                print("✅ 账号配置初始化完成")
            except Exception as e:
                print(f"❌ 初始化失败: {e}")
        else:
            print(f"❌ 内置账号模板不存在: {RESOURCE_SRC}")
            print("⚠️ 请检查打包是否包含 data/accounts/ 目录")
            RESOURCE_DIR.mkdir(exist_ok=True)
    else:
        # 开发环境：不自动创建，也不复制，由开发者手动管理
        print(f"💡 开发模式：账号目录不存在，建议手动创建或放入默认配置: {RESOURCE_DIR}")
        # 可选：自动创建空目录和空文件
        RESOURCE_DIR.mkdir(exist_ok=True)
        for env in ENV_TO_FILE.values():
            if not env.exists():
                with open(env, 'w', encoding='utf-8') as f:
                    import json
                    json.dump([], f, indent=2, ensure_ascii=False)
                print(f"📄 已创建空账号文件: {env}")


# 自动初始化
initialize_data_dir()
