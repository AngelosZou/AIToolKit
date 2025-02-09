# 总结模型，用于总结一段内容
from pathlib import Path

import util.fomatter as formatter
from core.cache import CatchInformation
from core.communicate import communicate


def process(content: str, send_to_cache: bool = False) -> str:
    path = Path("./resource/prompt/agent/summarizer.txt")
    prompt = path.read_text(encoding='utf-8')

    print("总结子系统启动")
    _, full_response = communicate([{'role': 'user', 'content': prompt + content}])

    res = formatter.delete_think(''.join(full_response))

    if send_to_cache:
        CatchInformation.get_instance().info = "由代理总结AI总结的信息：" + res
        print("\n\n总结信息已缓存，使用/submit提交给主AI")


    return res