# govee_community_tool/utils/history.py

import json
import os
from datetime import datetime
from threading import Lock
from config.settings import DEFAULT_ENV

# 历史记录存储路径
HISTORY_DIR = "data/history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# 线程锁
_history_lock = Lock()

def get_today_file():
    """获取今天的日志文件路径"""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(HISTORY_DIR, f"{today}.json")

def load_history():
    """加载今日历史记录"""
    file_path = get_today_file()
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_history(record):
    """保存单条记录"""
    file_path = get_today_file()
    with _history_lock:
        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "operation": record.get("operation"),
            "email": record.get("email"),
            "target_id": record.get("target_id"),
            "result": record.get("result"),  # success / failed
            "env": record.get("env", DEFAULT_ENV),
            "details": record.get("details", "")
        })
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

def clear_history():
    """清空今日记录"""
    file_path = get_today_file()
    if os.path.exists(file_path):
        os.remove(file_path)

def get_all_history():
    """获取所有历史文件（按日期）"""
    files = sorted(
        [f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")],
        reverse=True
    )
    all_data = {}
    for f in files:
        path = os.path.join(HISTORY_DIR, f)
        try:
            with open(path, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                date = f.split('.')[0]
                all_data[date] = data
        except:
            continue
    return all_data