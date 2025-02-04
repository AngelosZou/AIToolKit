import time
from pathlib import Path

from colorama import Fore, Style

from core.cache import Configure, GlobalFlag



name:str
message:list[dict]


def communicate(message, user_input = "") -> str:
    configure = Configure.get_instance()
    # 检查模型
    if Configure.get_instance().active_model is None:
        print("使用/model set <模型名>来设置模型")
        return ""

    # ------------------------------
    # 调用模型
    # ------------------------------
    if configure.active_ai == "Ollama":
        try:
            import ollama
            from ollama import chat
        except ImportError:
            print("请安装ollama库以使用Ollama模型")
            print("pip install ollama")
            return ""
        stream = chat(
            model=Configure.get_instance().active_model["Ollama"],
            messages=message,
            stream=True
        )

    elif configure.active_ai in ["OpenAI_API", "SiliconFlow"]:
        try:
            from openai import OpenAI
        except ImportError:
            print("请安装openai库以使用OpenAI模型")
            print("pip install openai")
            return ""

        url = ""
        api = ""
        if configure.active_ai == "OpenAI_API":
            api = configure.openai_api_key
            url = "https://api.openai.com/v1"
        elif configure.active_ai == "SiliconFlow":
            api = configure.siliconflow_api_key
            url = "https://api.siliconflow.com/v1"
        client = OpenAI(api_key=api, base_url=url)

        # 替换message中的所有system为user以匹配模型的输入
        # if configure.active_ai == "OpenAI_API":
        for i in range(len(message)):
            if message[i]['role'] == 'system':
                message[i]['role'] = 'user'
                message[i]['content'] = "[系统消息] !该内容由系统根据流程生成! "+message[i]['content'] + "[系统消息结束]"
                message[i]['system'] = True

        stream = client.chat.completions.create(
            model=configure.active_model[configure.active_ai],
            messages=message,
            stream=True,
            max_tokens = 4096 * 2
        )
    else:
        print("AI加载器来源不可用")
        return ""

    print("\nAI回复: ", end='', flush=True)
    full_response = write_stream_to_md(user_input, stream)
    return full_response


def write_stream_to_md(user_input: str, stream, filename: str = "conversation.md"):
    """实时将流式响应写入Markdown文件"""
    md_file = Path(filename)
    try:
        start_time = time.time()
        print(f"\n{Fore.BLUE}------------------------------------------------------{Style.RESET_ALL}")
        with md_file.open('a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"\n\n## 对话记录 - {timestamp}\n")
            f.write(f"**用户输入**: {user_input}\n**AI回复**: ")

            full_response = []
            full_think = []
            try:
                for chunk in stream:
                    content = ""
                    think_content = ""
                    if Configure.get_instance().active_ai == "Ollama":
                        content = chunk.message.content
                    elif Configure.get_instance().active_ai == "OpenAI_API":
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                    elif Configure.get_instance().active_ai in [ "SiliconFlow", "DeepSeek_API"]:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                        if chunk.choices[0].delta.model_extra["reasoning_content"] is not None:
                            think_content = chunk.choices[0].delta.model_extra["reasoning_content"]
                    print(content, end='', flush=True)
                    print(f"{Fore.LIGHTBLACK_EX}{think_content}{Style.RESET_ALL}", end='', flush=True)
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
                f.write(full_response)
                print(f"{Fore.BLUE}\n耗时{time.time()-start_time:.2f}秒\n--------------------"
                      f"----------------------------------{Style.RESET_ALL}")
            except KeyboardInterrupt:
                print("\n检测到中断信号，打断模型输出，抛弃未完成的信息")
                f.write(full_response+"\t 输出中断。")
                f.write("\n")

                return ""
            return full_response
    except Exception as e:
        print(f"\n文件写入错误: {str(e)}")
        return None
