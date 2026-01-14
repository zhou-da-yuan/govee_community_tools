# govee_community_tool/core/operations.py
import logging
import json
import time
import random
from typing import Dict, List, Any
from core.session_manager import SessionManager
from utils.history import save_history

# 所有操作定义
OPERATIONS = {
    "complaint_topic": {
        "name": "投诉话题",
        "url": lambda base: f"{base}/bff-app/v1/community/circle/topic/complaint",
        "method": "post",
        "params": [{"name": "target_id", "label": "话题ID"}],
        "payload": lambda **kw: {
            "communalId": int(kw["target_id"]),
            "causeId": 1,
            "communalType": 12,
            "content": ""
        }
    },
    "complaint_video": {
        "name": "投诉视频",
        "url": lambda base: f"{base}/appco/v1/complaints",
        "method": "post",
        "params": [{"name": "target_id", "label": "视频ID"}],
        "payload": lambda **kw: {
            "content": "",
            "causeId": 1,
            "type": 2,
            "id": int(kw["target_id"])
        }
    },
    "collect_diy_video": {
        "name": "收藏DIY视频",
        "url": lambda base: f"{base}/app/v1/diy-videos/collections",
        "method": "post",
        "params": [{"name": "target_id", "label": "视频ID"}],
        "payload": lambda **kw: {"videoId": int(kw["target_id"])}
    },
    "like_diy_video": {
        "name": "点赞DIY视频",
        "url": lambda base: f"{base}/bi/rest/v2/evals/likes",
        "method": "post",
        "params": [{"name": "target_id", "label": "视频ID"}],
        "payload": lambda **kw: {"videoId": int(kw["target_id"]), "state": 1}
    },
    "like_post": {
        "name": "点赞帖子",
        "url": lambda base: f"{base}/bi/rest/v1/postings/spot",
        "method": "get",
        "params": [{"name": "target_id", "label": "帖子ID"}],
        "params_func": lambda **kw: {
            'client': '5e972a68a408cada',
            'type': 1,
            'postId': kw["target_id"]
        }
    },
    "collect_post": {
        "name": "收藏帖子",
        "url": lambda base: f"{base}/appco/v1/posting/collections",
        "method": "post",
        "params": [{"name": "target_id", "label": "帖子ID"}],
        "payload": lambda **kw: {"postingId": str(kw["target_id"]), "state": 1}
    },
    "complaint_post": {
        "name": "投诉帖子",
        "url": lambda base: f"{base}/appco/v1/complaints",
        "method": "post",
        "params": [{"name": "target_id", "label": "帖子ID"}],
        "payload": lambda **kw: {
            "content": "",
            "causeId": 1,
            "type": 1,
            "id": int(kw["target_id"])
        }
    },
    "collect_playlist": {
        "name": "收藏播放列表",
        "url": lambda base: f"{base}/bff-app/v1/pixel-screen/share-list/collect",
        "method": "post",
        "params": [{"name": "target_id", "label": "播放列表ID"}],
        "payload": lambda **kw: {"id": int(kw["target_id"]), "state": 1}
    },
    "like_playlist": {
        "name": "点赞播放列表",
        "url": lambda base: f"{base}/bff-app/v1/pixel-screen/share-list/like",
        "method": "post",
        "params": [{"name": "target_id", "label": "播放列表ID"}],
        "payload": lambda **kw: {"id": int(kw["target_id"]), "state": 1}
    },
    "complaint_playlist": {
        "name": "投诉播放列表",
        "url": lambda base: f"{base}/bff-app/v1/pixel-screen/share-list/share/complaint",
        "method": "post",
        "params": [{"name": "target_id", "label": "播放列表ID"}],
        "payload": lambda **kw: {
            "causeId": 1,
            "communalId": int(kw["target_id"]),
            "communalType": 5,
            "content": ""
        }
    },
    "like_light_effect": {
        "name": "点赞图片灯效",
        "url": lambda base: f"{base}/appco/v1/light-square/picture-effect/likes",
        "method": "post",
        "params": [{"name": "target_id", "label": "灯效ID"}],
        "payload": lambda **kw: {
            "effectId": int(kw["target_id"]),
            "state": 1,
            "sku": ""
        }
    },
    "create_post": {
        "name": "发布帖子",
        "url": lambda base: f"{base}/bff-app/v1/community/posting/details",
        "method": "post",
        "support_batch": False,
        "support_single": True,
        "params": [
            {"name": "count", "label": "发布数量"},
            {"name": "content", "label": "发布内容"},
            {"name": "circle_id", "label": "圈子ID"},
            {"name": "topic_id", "label": "话题ID"}
        ],
        "defaults": {
            "content": "This is an automatically published test content.",
            "count": "1"
        },
        "placeholders": {
            "content": "请输入要发布的内容...",
            "count": "输入发布数量(默认1)",
            "circle_id": "圈子ID（可选）",
            "topic_id": "话题ID（可选）"
        },
        "payload": lambda **kw: build_create_post_payload(**kw)
    },
    "comment_post": {
        "name": "发布帖子评论",
        "url": lambda base: f"{base}/bff-app/v1/community/posting/detail/answers",
        "method": "post",
        "support_batch": False,
        "support_single": True,
        "params": [
            {"name": "target_id", "label": "目标帖子ID"},
            {"name": "content", "label": "评论内容"},
            {"name": "count", "label": "评论数量"}
        ],
        "defaults": {
            "content": "This is the default comment content for testing",
            "count": "1"
        },
        "placeholders": {
            "content": "请输入评论内容...",
            "count": "输入评论数量(默认1)",
            "target_id": "请输入目标帖子ID"
        },
        "payload": lambda **kw: {
            "originalContent": kw["content"],
            "content": kw["content"],
            "urls": [],
            "color": "",
            "hasImg": False,
            "hasVideo": False,
            "isAtUser": 0,
            "postId": str(kw["target_id"]),
            "firstCommentOriginal": kw["content"],
            "atUser": []
        }
    },
    "follow_user": {
        "name": "新增Followers",
        "url": lambda base: f"{base}/appco/v1/users/subscription",
        "method": "post",
        "params": [{"name": "target_id", "label": "用户ID"}],
        "payload": lambda **kw: {
            "userId": str(kw["target_id"]),
            "action": 1  # 1 表示关注
        }
    },
    "create_devices_group": {
        "name": "新增房间",
        "url": lambda base: f"{base}/bff-app/v1/devices/groups",
        "method": "post",
        "support_single": True,
        "params": [{"name": "count", "label": "创建数量"},
                   {"name": "groupName","label":"房间名称"}
                   ],
        "payload": lambda **kw: {"groupName": str(kw["groupName"]), "key": "", "view": 0}
    }
    # 需要两个参数，暂时先不做
    # "collect_music_create": {
    #     "name": "收藏音乐创作",
    #     "url": lambda base: f"{base}/bff-app/v1/music-create/collects",
    #     "method": "post",
    #     "payload": lambda lid: {"musicShareId": str(lid), "state": 1}
    # },
    # "get_aid": {
    #     "name": "获取 AID",
    #     "url": lambda base: f"{base}/bi/rest/v1/user-informations",
    #     "method": "get"
    # },

}


def build_create_post_payload(**kw):
    """辅助函数：构建发布帖子的完整 payload"""
    title_suffix = f"{int(time.time()) % 10000}"
    content_text = kw.get("content", "Default auto post.")
    circle_id = int(kw.get("circle_id", -1)) if kw.get("circle_id") else -1
    topic_id = int(kw.get("topic_id", -1)) if kw.get("topic_id") else -1
    content_html = f"<p class=\"new-posting-content\">{content_text}</p>"
    content_v2_dict = {
        "content": content_text,
        "contentHTML": content_html,
        "uploadImage": []
    }
    content_v2_str = json.dumps(content_v2_dict, ensure_ascii=False)

    return {
        "postType": 1,
        "title": f"AutoPost-{title_suffix}",
        "h5Url": "",
        "labelId": None,
        "circleId": circle_id,  # 👈 使用传入的 circle_id
        "atUsers": [],
        "content": "",
        "contentV2": content_v2_str,
        "urls": [],
        "products": [],
        "draftId": -1,
        "topicId": topic_id,  # 👈 使用传入的 topic_id
        "topicName": "",
        "topicDes": "",
        "needVote": False,
        "voteContent": {}
    }


def execute_operation(
        op_key: str,
        session_manager: SessionManager,
        token: str,
        base_url: str,
        **kwargs
) -> bool | dict:
    op = OPERATIONS.get(op_key)
    if not op:
        logging.error(f"未知操作: {op_key}")
        return False

    session = session_manager.get_session()
    headers = {**session.headers, 'Authorization': f'Bearer {token}'}
    url = op["url"](base_url)
    op_name = op["name"]

    try:
        # 统一收集参数（包含 target_id, content, count 等）
        collected_params = kwargs.copy()

        # 特殊处理：如果操作支持批量（如 create_post），则循环执行
        if op.get("support_single", False):
            count = int(collected_params.get("count", 1))
            success_count = 0
            results = []

            for i in range(count):
                # 每次可生成唯一内容（可选）
                if "content" in collected_params:
                    content = collected_params["content"]
                    # 可加后缀避免重复，如 AutoPost-1234-1
                    # 但由 payload 函数决定是否使用

                # 调用 payload 函数（传入当前循环的上下文）
                payload = op["payload"](**collected_params)

                res = session.post(url, headers=headers, json=payload)
                success = res.status_code == 200 and res.json().get("status") == 200
                msg = "成功" if success else f"失败: {res.text[:100]}"

                result = {"success": success, "msg": msg}
                results.append(result)
                if success:
                    success_count += 1

                save_history({
                    "operation": op_name,
                    "email": headers.get("X-User-Email", "unknown"),
                    "target_id": "batch",
                    "result": "success" if success else "failed",
                    "env": kwargs.get("env"),
                    "details": msg
                })

                time.sleep(random.uniform(1.5, 3.5))

            return {
                "success": success_count > 0,
                "total": count,
                "success_count": success_count,
                "all_success": success_count == count,
                "results": results
            }

        else:
            # 单次操作
            if op["method"] == "get":
                # 使用 params_func 或默认从 target_id 构造
                if "params_func" in op:
                    params = op["params_func"](**collected_params)
                else:
                    # 默认：GET 操作通常只需要 target_id
                    params = {"postId": collected_params.get("target_id")}
                res = session.get(url, headers=headers, params=params)
            else:
                # POST 操作：调用 payload 函数
                payload = op["payload"](**collected_params)
                res = session.post(url, headers=headers, json=payload)

            success = res.status_code == 200 and res.json().get("status") == 200

            save_history({
                "operation": op_name,
                "email": headers.get("X-User-Email", "unknown"),
                "target_id": collected_params.get("target_id", "N/A"),
                "result": "success" if success else "failed",
                "env": kwargs.get("env"),
                "details": res.json() if success else res.text
            })

            return success

    except Exception as e:
        logging.error(f"操作执行失败 [{op_name}]: {str(e)}")
        save_history({
            "operation": op_name,
            "email": headers.get("X-User-Email", "unknown"),
            "target_id": kwargs.get("target_id", "N/A"),
            "result": "failed",
            "env": kwargs.get("env"),
            "details": str(e)
        })
        return False


def get_user_aid(session_manager: SessionManager, token: str, base_url: str) -> dict:
    """
    获取用户的 AID (identity)
    :param session_manager: 会话管理器
    :param token: 登录 token
    :param base_url: 环境 base_url
    :return: { "success": bool, "aid": str 或 None, "msg": str }
    """
    session = session_manager.get_session()
    url = f"{base_url}/bi/rest/v1/user-informations"
    headers = {**session.headers, 'Authorization': f'Bearer {token}'}

    try:
        response = session.get(url, headers=headers)
        if response.status_code == 200 and response.json().get("status") == 200:
            data = response.json()
            identity = data.get("data", {}).get("identity")
            if identity:
                return {
                    "success": True,
                    "aid": identity,
                    "msg": "获取成功"
                }
            else:
                return {
                    "success": False,
                    "aid": None,
                    "msg": "响应中未找到 identity 字段: " + str(data)
                }
        else:
            return {
                "success": False,
                "aid": None,
                "msg": f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "aid": None,
            "msg": f"请求异常: {str(e)}"
        }
