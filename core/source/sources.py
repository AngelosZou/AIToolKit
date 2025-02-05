from typing import List, Dict, Any


class BaseSource:
    source_name: str

    @classmethod
    def is_available(cls) -> bool:
        # 检查AI源是否可用，是否配置正确
        raise NotImplementedError

    @classmethod
    def create_stream(cls, message: list[dict]) -> Any:
        """将对话发送给AI源，返回流式响应的流"""
        raise NotImplementedError

    @classmethod
    def catch_chunk_in_stream(cls, chunk)-> [str, str]:
        """从chunk中获取数据，第一个返回值为思考过程，第二个返回值为主要响应"""
        raise NotImplementedError


class SourceRegistry:
    sources: Dict[str, BaseSource.__class__] = {}

    @classmethod
    def register(cls, source_name: str):
        """注册装饰器"""
        def decorator(source_class: BaseSource.__class__):
            cls.sources[source_name] = source_class
            source_class.source_name = source_name
            return source_class
        return decorator