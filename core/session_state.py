# govee_community_tool/core/session_state.py

class SessionState:
    """当前会话中的持久状态，程序关闭后丢失"""
    def __init__(self):
        self.email = ""
        self.password = ""

# 全局唯一实例
session_state = SessionState()