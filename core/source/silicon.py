from typing import Any

from core.SurrogateIO import sio_print
from core.cache import Configure
from core.source.sources import BaseSource, SourceRegistry


@SourceRegistry.register("SiliconFlow")
class SourceOpenAI(BaseSource):
    @classmethod
    def is_available(cls) -> bool:
        # 检查API
        if len(Configure.get_instance().siliconflow_api_key) == 0:
            sio_print("SiliconFlow API 未配置。")
            return False
        try:
            from openai import OpenAI
        except ImportError:
            sio_print("请安装openai库以使用 SiliconFlow API")
            sio_print("pip install openai")
            return False
        return True

    @classmethod
    def create_stream(cls, message: list[dict]) -> Any:
        configure = Configure.get_instance()
        api = configure.siliconflow_api_key
        url = "https://api.siliconflow.com/v1"
        try:
            from openai import OpenAI
        except ImportError as e:
            sio_print("openai库未安装")
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
        content, think_content = "", ""
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
        if chunk.choices[0].delta.model_extra["reasoning_content"] is not None:
            think_content = chunk.choices[0].delta.model_extra["reasoning_content"]
        return think_content, content