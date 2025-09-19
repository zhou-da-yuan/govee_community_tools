# govee_community_tool/core/operations.py

from core.session_manager import SessionManager


OPERATIONS = {
    "complaint_topic": {
        "name": "投诉话题",
        "url": lambda base: f"{base}/bff-app/v1/community/circle/topic/complaint",
        "method": "post",
        "payload": lambda tid: {"communalId": int(tid), "causeId": 1, "communalType": 12, "content": ""}
    },
    "complaint_video": {
        "name": "投诉视频",
        "url": lambda base: f"{base}/appco/v1/complaints",
        "method": "post",
        "payload": lambda vid: {"content": "", "causeId": 1, "type": 2, "id": int(vid)}
    },
    "like_diy_video": {
        "name": "点赞DIY视频",
        "url": lambda base: f"{base}/app/v1/diy-videos/collections",
        "method": "post",
        "payload": lambda vid: {"videoId": int(vid)}
    },
    "like_post": {
        "name": "给帖子点赞",
        "url": lambda base: f"{base}/bi/rest/v1/postings/spot",
        "method": "get",
        "params": lambda pid: {'client': '5e972a68a408cada', 'type': 1, 'postId': pid}
    },
    "collect_playlist": {
        "name": "收藏播放列表",
        "url": lambda base: f"{base}/bff-app/v1/pixel-screen/share-list/collect",
        "method": "post",
        "payload": lambda lid: {"id": int(lid), "state": 1}
    },
    "complaint_playlist": {
        "name": "投诉播放列表",
        "url": lambda base: f"{base}/bff-app/v1/pixel-screen/share-list/share/complaint",
        "method": "post",
        "payload": lambda lid: {"causeId": 1, "communalId": int(lid), "communalType": 5, "content": ""}
    },
    "complaint_post": {
        "name": "投诉帖子",
        "url": lambda base: f"{base}/appco/v1/complaints",
        "method": "post",
        "payload": lambda pid: {"content": "", "causeId": 1, "type": 1, "id": int(pid)}
    }
}


def execute_operation(op_key: str, session_manager: SessionManager, token: str, target_id: str, base_url: str) -> bool:
    op = OPERATIONS[op_key]
    session = session_manager.get_session()
    headers = {**session.headers, 'Authorization': f'Bearer {token}'}
    url = op["url"](base_url)

    try:
        if op["method"] == "get":
            params = op["params"](target_id)
            res = session.get(url, headers=headers, params=params)
        else:
            payload = op["payload"](target_id)
            res = session.post(url, headers=headers, json=payload)

        return res.status_code == 200 and res.json().get("status") == 200
    except Exception as e:
        print(f"❌ 执行操作失败: {e}")
        return False