import time
from copy import copy
from pathlib import Path

from colorama import Fore, Style

from core.cache import Configure, GlobalFlag
from core.source.sources import SourceRegistry, BaseSource

name:str
message:list[dict]


def communicate(message) -> str:
    configure = Configure.get_instance()
    # 检查模型
    if Configure.get_instance().active_model is None:
        print("使用/model set <模型名>来设置模型")
        return ""

    # 检查模型可用性
    if configure.active_ai not in configure.active_model:
        print(f"未设置AI源 {configure.active_ai} 对应的模型")
        print("使用 /model set <模型> 进行设置")
        return ""
    source_cls: BaseSource.__class__ = SourceRegistry.sources[configure.active_ai]
    if not source_cls.is_available:
        return ""

    # ------------------------------
    # 调用模型
    # ------------------------------

    # 替换message中的所有system为user以匹配模型的输入
    # 去除所有非开头的system
    flag = False
    for i in range(len(message)):
        if message[i]['role'] != 'system':
            flag = True
        if message[i]['role'] == 'system' and flag:
            message[i]['role'] = 'user'
            message[i]['content'] = "[系统消息] !该内容由系统根据流程生成! "+message[i]['content'] + "[系统消息结束]"
            message[i]['system'] = True

    stream = source_cls.create_stream(copy(message))

    print("\nAI回复: ", end='', flush=True)
    full_response = process_stream(stream, source_cls)
    return full_response


def process_stream(stream, source_cls: BaseSource.__class__):
    """实时将流式响应写入Markdown文件"""
    try:
        start_time = time.time()
        print(f"\n{Fore.BLUE}------------------------------------------------------{Style.RESET_ALL}")
        full_response = []
        full_think = []
        try:
            for chunk in stream:
                think_content, content = source_cls.catch_chunk_in_stream(chunk)
                print(f"{Fore.LIGHTBLACK_EX}{think_content}{Style.RESET_ALL}", end='', flush=True)
                if len(full_response) == 0 and len(content) != 0:
                    print("\n\n")
                print(content, end='', flush=True)
                full_response.append(content)
                # 如果最近的5段content组合中存在 <wait>, <end>，则停止
                if len(full_response) >= 5:
                    if "<wait>" in "".join(full_response[-5:]) or "<end>" in "".join(full_response[-5:]):
                        if "<end>" in "".join(full_response[-5:]):
                            GlobalFlag.get_instance().force_stop = True
                        break
                full_think.append(think_content)
            # 处理full_think
            full_think = "".join(full_think)
            if len(full_think) != 0:
                full_think = "<think>\n" + full_think + "\n</think>"
            full_response = full_think + ''.join(full_response)
            print(f"{Fore.BLUE}\n耗时{time.time()-start_time:.2f}秒\n--------------------"
                  f"----------------------------------{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print("\n检测到中断信号，打断模型输出，抛弃未完成的信息")

            return ""
        return full_response
    except Exception as e:
        print(f"\n文件写入错误: {str(e)}")
        return None
