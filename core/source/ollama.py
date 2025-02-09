from typing import Any

from core.SurrogateIO import sio_print
from core.cache import Configure
from core.source.sources import BaseSource, SourceRegistry


@SourceRegistry.register("Ollama")
class SourceOpenAI(BaseSource):
    @classmethod
    def is_available(cls) -> bool:
        try:
            import ollama
            from ollama import chat
        except ImportError:
            sio_print("请安装ollama库以使用Ollama模型")
            sio_print("pip install ollama")
            return False
        return True

    @classmethod
    def create_stream(cls, message: list[dict]) -> Any:
        try:
            from ollama import chat
        except ImportError as e:
            sio_print("ollama 库未安装")
            raise e
        stream = chat(
            model=Configure.get_instance().active_model["Ollama"],
            messages=message,
            stream=True
        )
        return stream

    @classmethod
    def catch_chunk_in_stream(cls, chunk)-> [str, str]:
        content = chunk.message.content
        return "", content