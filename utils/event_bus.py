# govee_community_tool/utils/event_bus.py

class EventBus:
    """简单的全局事件总线"""
    def __init__(self):
        self._listeners = {}

    def on(self, event_name, callback):
        """注册事件监听"""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def emit(self, event_name, *args, **kwargs):
        """触发事件"""
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                callback(*args, **kwargs)

# 全局实例
event_bus = EventBus()