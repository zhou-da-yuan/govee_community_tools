# govee_community_tool/utils/file_loader.py

import json
import os
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