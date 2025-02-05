from typing import Any

from core.cache import Configure
from core.source.sources import BaseSource, SourceRegistry


@SourceRegistry.register("DeepSeek")
class SourceOpenAI(BaseSource):
    @classmethod
    def is_available(cls) -> bool:
        # 检查API
        if len(Configure.get_instance().deepseek_api_key) == 0:
            print("DeepSeek API 未配置。")
            return False
        try:
            from openai import OpenAI
        except ImportError:
            print("请安装openai库以使用 DeepSeek API")
            print("pip install openai")
            return False
        return True

    @classmethod
    def create_stream(cls, message: list[dict]) -> Any:
        configure = Configure.get_instance()
        api = configure.deepseek_api_key
        url = "https://api.deepseek.com"
        try:
            from openai import OpenAI
        except ImportError as e:
            print("openai库未安装")
            raise e
        client = OpenAI(api_key=api, base_url=url)
        stream = client.chat.completions.create(
            model=configure.active_model[configure.active_ai],
            messages=validate_message_structure(message),
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


def validate_message_structure(messages: list[dict]) -> list[dict]:
    """
    处理消息列表使其符合交替的user-assistant结构
    1. 跳过开头的system消息（确保后续处理不影响初始设置）
    2. 在前一个消息是user的情况下，如果当前还是user则插入空assistant
    3. 保留原始消息内容不进行修改

    示例输入: [{'role':'user'}, {'role':'user'}]
    期望输出: [{'role':'user'}, {'role':'assistant', 'content':''}, {'role':'user'}]
    """
    if not messages:
        return []

    processed = [m for m in messages if m['role'] == "system"]

    for i in range(len(processed), len(messages)):
        current = messages[i].copy()
        prev_role = processed[i-1]['role']

        if current['role'] == 'user' and prev_role == 'user':
            processed.append({'role': 'assistant', 'content': ''})

        processed.append(current)

    return processed