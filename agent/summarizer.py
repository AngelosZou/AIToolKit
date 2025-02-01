# 总结模型，用于总结一段内容
from ollama import chat
from pathlib import Path

from core.cache import Cache, CatchInformation
import util.fomatter as formatter


def process(content: str, send_to_cache: bool = False) -> str:
    path = Path("./resource/prompt/summarizer.txt")
    prompt = path.read_text(encoding='utf-8')

    print("总结子系统启动")
    stream = chat(
        model=Cache.get_instance().active_model,
        messages=[{'role': 'user', 'content': prompt + content}],
        stream=True
    )

    print("\n总结信息: ", end='', flush=True)

    full_response = []

    for chunk in stream:
        content = chunk.message.content
        print(content, end='', flush=True)
        full_response.append(content)

    res = formatter.delete_think(''.join(full_response))

    if send_to_cache:
        CatchInformation.get_instance().info = "由代理总结AI总结的信息：" + res
        print("\n\n总结信息已缓存，使用/submit提交给主AI")


    return res