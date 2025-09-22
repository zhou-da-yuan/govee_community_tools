# govee_community_tool/utils/file_loader.py

import json
import os
import sys
from typing import List, Dict, Optional


def load_accounts(filepath: str) -> Optional[List[Dict[str, str]]]:
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            return None
        for item in data:
            if not isinstance(item, dict) or 'email' not in item or 'password' not in item:
                return None
        return data
    except Exception as e:
        print(f"⚠️ 加载账号失败: {e}")
        return None

# utils.py 或 main.py 中
def resource_path(relative_path):
    """ 获取资源的正确路径，兼容 PyInstaller 打包 """
    try:
        # PyInstaller 创建临时文件夹，并把路径存入 _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)