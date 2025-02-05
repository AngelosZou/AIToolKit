from typing import Any

from core.cache import Configure
from core.source.sources import BaseSource, SourceRegistry


@SourceRegistry.register("OpenAI_API")
class SourceOpenAI(BaseSource):
    @classmethod
    def is_available(cls) -> bool:
        # 检查API
        if len(Configure.get_instance().openai_api_key) == 0:
            print("OpenAI API 未配置。")
            return False
        try:
            from openai import OpenAI
        except ImportError:
            print("请安装openai库以使用OpenAI模型")
            print("pip install openai")
            return False
        return True

    @classmethod
    def create_stream(cls, message: list[dict]) -> Any:
        configure = Configure.get_instance()
        api = configure.openai_api_key
        url = "https://api.openai.com/v1"
        try:
            from openai import OpenAI
        except ImportError as e:
            print("openai库未安装")
            raise e
        client = OpenAI(api_key=api, base_url=url)
        stream = client.chat.completions.create(
            model=configure.active_model[configure.active_ai],
            messages=message,
            stream=True
        )
        return stream

    @classmethod
    def catch_chunk_in_stream(cls, chunk)-> [str, str]:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            return "", content
        return "", ""