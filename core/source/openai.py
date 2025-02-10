from typing import Any

from core.SurrogateIO import sio_print
from core.cache import Configure
from core.source.sources import BaseSource, SourceRegistry


@SourceRegistry.register("OpenAI_API")
class SourceOpenAI(BaseSource):
    @classmethod
    def is_available(cls) -> bool:
        # 检查API
        if len(Configure.get_instance().openai_api_key) == 0:
            sio_print("OpenAI API 未配置。")
            return False
        try:
            from openai import OpenAI
        except ImportError:
            sio_print("请安装openai库以使用OpenAI模型")
            sio_print("pip install openai")
            return False
        return True

    @classmethod
    def create_stream(cls, message: list[dict]) -> Any:
        # 把所有system都换成user
        for i in range(len(message)):
            if message[i]['role'] == 'system':
                message[i]['role'] = 'user'
                message[i]['content'] = "[系统消息] !该内容由系统根据流程生成! "+message[i]['content'] + "[系统消息结束]"
                message[i]['system'] = True
        configure = Configure.get_instance()
        api = configure.openai_api_key
        url = "https://api.openai.com/v1"
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
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            return "", content
        return "", ""