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
        "payload": lambda tid: {"communalId": int(tid), "causeId": 1, "communalType": 12, "content": ""}
    },
    "complaint_video": {
        "name": "投诉视频",
        "url": lambda base: f"{base}/appco/v1/complaints",
        "method": "post",
        "payload": lambda vid: {"content": "", "causeId": 1, "type": 2, "id": int(vid)}
    },
    "collect_diy_video": {
        "name": "收藏DIY视频",
        "url": lambda base: f"{base}/app/v1/diy-videos/collections",
        "method": "post",
        "payload": lambda vid: {"videoId": int(vid)}
    },
    "like_diy_video": {
        "name": "点赞DIY视频",
        "url": lambda base: f"{base}/bi/rest/v2/evals/likes",
        "method": "post",
        "payload": lambda vid: {"videoId": int(vid), "state": 1}
    },
    "like_post": {
        "name": "点赞帖子",
        "url": lambda base: f"{base}/bi/rest/v1/postings/spot",
        "method": "get",
        "params": lambda pid: {'client': '5e972a68a408cada', 'type': 1, 'postId': pid}
    },
    "collect_post": {
        "name": "收藏帖子",
        "url": lambda base: f"{base}/appco/v1/posting/collections",
        "method": "post",
        "payload": lambda pid: {"postingId": str(pid), "state": 1}
    },
    "complaint_post": {
        "name": "投诉帖子",
        "url": lambda base: f"{base}/appco/v1/complaints",
        "method": "post",
        "payload": lambda pid: {"content": "", "causeId": 1, "type": 1, "id": int(pid)}
    },
    "collect_playlist": {
        "name": "收藏播放列表",
        "url": lambda base: f"{base}/bff-app/v1/pixel-screen/share-list/collect",
        "method": "post",
        "payload": lambda lid: {"id": int(lid), "state": 1}
    },
    "like_playlist": {
        "name": "点赞播放列表",
        "url": lambda base: f"{base}/bff-app/v1/pixel-screen/share-list/like",
        "method": "post",
        "payload": lambda lid: {"id": int(lid), "state": 1}
    },
    "complaint_playlist": {
        "name": "投诉播放列表",
        "url": lambda base: f"{base}/bff-app/v1/pixel-screen/share-list/share/complaint",
        "method": "post",
        "payload": lambda lid: {"causeId": 1, "communalId": int(lid), "communalType": 5, "content": ""}
    },
    "like_light_effect": {
        "name": "点赞图片灯效",
        "url": lambda base: f"{base}/appco/v1/light-square/picture-effect/likes",
        "method": "post",
        "payload": lambda effect_id: {"effectId": int(effect_id), "state": 1, "sku": ""}
    },
    # 注意：create_post 不再需要 payload 函数，由 execute_operation 处理
    "create_post": {
        "name": "发布帖子",
        "url": lambda base: f"{base}/bff-app/v1/community/posting/details",
        "method": "post",
        "support_single": True,
        "params": ["count", "content", "circle_id", "topic_id"],  # 👈 新增两个参数
        "defaults": {
            "content": "This is an automatically published test content.",
        },
        "placeholders": {
            "content": "请输入要发布的内容...",
            "count": "输入发布数量(默认1)",
            "circle_id": "圈子ID（可选）",
            "topic_id": "话题ID（可选）"
        },
    },
    "comment_post": {
        "name": "发布帖子评论",
        "url": lambda base: f"{base}/bff-app/v1/community/posting/detail/answers",
        "method": "post",
        "support_single": True,
        "params": ["count", "content", "target_id"],
        "defaults": {
            "content": "This is the default comment content for testing",
        },
        "placeholders": {
            "content": "请输入评论内容...",
            "count": "输入评论数量(默认1)",
            "target_id": "请输入目标帖子ID"
        },
        "payload": lambda content, post_id: {
            "originalContent": content,
            "content": content,
            "urls": [],
            "color": "",
            "hasImg": False,
            "hasVideo": False,
            "isAtUser": 0,
            "postId": str(post_id),
            "firstCommentOriginal": content,
            "atUser": []
        }
    },
    # 需要两个参数，暂时先不做
    # "collect_music_create": {
    #     "name": "收藏音乐创作",
    #     "url": lambda base: f"{base}/bff-app/v1/music-create/collects",
    #     "method": "post",
    #     "payload": lambda lid: {"musicShareId": str(lid), "state": 1}
    # },
    "follow_user": {
        "name": "新增Followers",
        "url": lambda base: f"{base}/appco/v1/users/subscription",
        "method": "post",
        # 不再使用静态 payload，改为动态生成（需 myIdentity）
    },
    # "get_aid": {
    #     "name": "获取 AID",
    #     "url": lambda base: f"{base}/bi/rest/v1/user-informations",
    #     "method": "get"
    # },

}


def build_create_post_payload(title_suffix: str, content_text: str, circle_id: int = -1, topic_id: int = -1):
    """
    构建发帖 payload，支持指定圈子和话题
    """
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
        **kwargs  # 支持额外参数，如 count, content, target_id 等
) -> bool | dict[str, int | bool | list[
    dict[str, str | bool | Any] | dict[str, str | bool] | dict[str, str | bool] | dict[str, str | bool]]]:
    """
    统一执行操作入口
    支持：
        - 单次操作（target_id）
        - 批量操作（count, content）
    """
    op = OPERATIONS.get(op_key)
    if not op:
        logging.error(f"未知操作: {op_key}")
        return False

    session = session_manager.get_session()
    headers = {**session.headers, 'Authorization': f'Bearer {token}'}
    url = op["url"](base_url)
    op_name = op["name"]

    try:
        if op_key == "create_post":
            # 处理批量发帖
            count = kwargs.get("count", 1)
            content_text = kwargs.get("content", "This is an automatically published test content.。")

            # 👇 解析 circle_id 和 topic_id，转为 int；若无效则默认 -1
            try:
                circle_id = int(kwargs.get("circle_id", -1))
            except (TypeError, ValueError):
                circle_id = -1

            try:
                topic_id = int(kwargs.get("topic_id", -1))
            except (TypeError, ValueError):
                topic_id = -1

            success_count = 0
            results = []

            for i in range(count):
                title_suffix = f"{int(time.time()) % 10000}-{i + 1}"
                payload = build_create_post_payload(title_suffix, content_text, circle_id, topic_id)

                try:
                    res = session.post(url, headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("status") == 200:
                            post_id = data.get("data", {}).get("id", "未知")
                            result = {
                                "success": True,
                                "post_id": post_id,
                                "msg": f"发布成功 | Post ID: {post_id}"
                            }
                        else:
                            msg = data.get("message", "未知错误")
                            result = {
                                "success": False,
                                "post_id": "失败",
                                "msg": f"发布失败: {msg}"
                            }
                    else:
                        result = {
                            "success": False,
                            "post_id": "失败",
                            "msg": f"HTTP {res.status_code}"
                        }

                except Exception as e:
                    result = {
                        "success": False,
                        "post_id": "异常",
                        "msg": f"异常: {str(e)}"
                    }
                    logging.error(f"发帖异常 (第{i + 1}条): {str(e)}")

                # 无论成功失败都记录历史
                save_history({
                    "operation": op_name,
                    "email": session.headers.get("X-User-Email", "unknown"),
                    "target_id": result["post_id"],
                    "result": "success" if result["success"] else "failed",
                    "env": kwargs.get("env"),
                    "details": result["msg"]
                })

                results.append(result)
                time.sleep(random.uniform(1.5, 3.5))

                # 统计
            success_count = sum(1 for r in results if r["success"])
            all_success = success_count == count
            any_success = success_count > 0

            return {
                "success": any_success,  # 至少一条成功
                "total": count,
                "success_count": success_count,
                "all_success": all_success,
                "results": results
            }

        elif op_key == "comment_post":
            # 在 execute_operation 函数中，处理 comment_post 的逻辑已兼容
            target_id = kwargs.get("target_id")
            if not target_id:
                raise ValueError("缺少 target_id")
            content = kwargs.get("content", "This is the default comment content for testing")

            payload = op["payload"](content, target_id)
            res = session.post(url, headers=headers, json=payload)

            result = res.status_code == 200 and res.json().get("status") == 200

            # 记录历史
            save_history({
                "operation": op_name,
                "email": session.headers.get("X-User-Email", "unknown"),
                "target_id": target_id,
                "result": "success" if result else "failed",
                "env": kwargs.get("env"),
                "details": res.json()
            })

            return result

        elif op_key == "follow_user":
            target_identity = kwargs.get("target_id")
            if not target_identity:
                raise ValueError("缺少 target_id（被关注用户的 identity）")

            # 👉 先获取当前用户的 AID (myIdentity)
            aid_result = get_user_aid(session_manager, token, base_url)
            if not aid_result["success"]:
                logging.error(f"获取 myIdentity 失败: {aid_result['msg']}")
                save_history({
                    "operation": op_name,
                    "email": session.headers.get("X-User-Email", "unknown"),
                    "target_id": target_identity,
                    "result": "failed",
                    "env": kwargs.get("env"),
                    "details": f"获取 myIdentity 失败: {aid_result['msg']}"
                })
                return False

            my_identity = aid_result["aid"]

            # 构造 payload
            payload = {
                "identity": str(target_identity),
                "identityType": 2,
                "subscribe": 1,
                "myIdentity": str(my_identity)  # 👈 新增字段
            }

            res = session.post(url, headers=headers, json=payload)
            result = res.status_code == 200 and res.json().get("status") == 200

            save_history({
                "operation": op_name,
                "email": session.headers.get("X-User-Email", "unknown"),
                "target_id": target_identity,
                "result": "success" if result else "failed",
                "env": kwargs.get("env"),
                "details": res.json() if result else str(res.text)
            })

            return result

        else:
            # 处理其他单次操作
            target_id = kwargs.get("target_id")
            if not target_id:
                raise ValueError("缺少 target_id")

            if op["method"] == "get":
                params = op["params"](target_id)
                res = session.get(url, headers=headers, params=params)
            else:
                payload = op["payload"](target_id)
                res = session.post(url, headers=headers, json=payload)

            result = res.status_code == 200 and res.json().get("status") == 200

            # 记录历史
            save_history({
                "operation": op_name,
                "email": session.headers.get("X-User-Email", "unknown"),
                "target_id": target_id,
                "result": "success" if result else "failed",
                "env": kwargs.get("env"),
                "details": res.json()
            })

            return result

    except Exception as e:
        logging.error(f"操作执行失败 [{op_name}]: {str(e)}")
        save_history({
            "operation": op_name,
            "email": session.headers.get("X-User-Email", "unknown"),
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
