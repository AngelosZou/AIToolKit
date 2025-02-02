import time
from pathlib import Path

import core.cache
from command.commands import CommandHandler
from core import cache
from core.cache import Configure, GlobalFlag
from tool.excutor import process_model_output
from util.fomatter import delete_think


def write_stream_to_md(user_input: str, stream, filename: str = "conversation.md"):
    """实时将流式响应写入Markdown文件"""
    md_file = Path(filename)
    try:
        with md_file.open('a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"\n\n## 对话记录 - {timestamp}\n")
            f.write(f"**用户输入**: {user_input}\n**AI回复**: ")

            full_response = []
            try:
                for chunk in stream:
                    content = ""
                    if Configure.get_instance().active_ai == "Ollama":
                        content = chunk.message.content
                    elif Configure.get_instance().active_ai in ["OpenAI_API", "SiliconFlow", "DeepSeek_API"]:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                    print(content, end='', flush=True)
                    full_response.append(content)
                f.write(''.join(full_response))
            except KeyboardInterrupt:
                print("\n检测到中断信号，打断模型输出，抛弃未完成的信息")
                f.write(''.join(full_response)+"\t 输出中断。")
                f.write("\n")

                return ""
            return ''.join(full_response)
    except Exception as e:
        print(f"\n文件写入错误: {str(e)}")
        return None

def main():
    cmd_handler = CommandHandler()

    configure = core.cache.Configure.get_instance()

    if configure.active_ai is None:
        print(f"\n未选择AI加载器来源")
        print(f"\n可选的AI列表：")
        print(core.cache.AVAILABLE_AI)
        print("使用/ai set <AI名>来设置AI")
    else:
        print(f"\n当前AI加载器来源：{configure.active_ai}")

    # ------------------------------
    # 处理不同的可用模型
    # ------------------------------
    if configure.active_ai == "Ollama":
        if "Ollama" not in configure.active_model or configure.active_model["Ollama"] is None:
            try:
                import ollama
                from ollama import chat
            except ImportError:
                print("请安装ollama库以使用Ollama模型")
                print("pip install ollama")
                return
            print(f"\n模型未加载")
            print(f"\n可选的模型列表：")
            print(ollama.list())
            print("使用/model set <模型名>来设置模型")
        else:
            print(f"\n当前模型：{configure.active_model['Ollama']}")
    elif configure.active_ai in ["OpenAI_API", "SiliconFlow"]:
        if "OpenAI_API" not in configure.active_model or configure.active_model["OpenAI_API"] is None:
            print(f"\n模型未加载")
            print("请使用/model set <模型名>来设置模型")
            if configure.active_ai == "OpenAI_API":
                print(f"模型包括但不限于：\n gpt-4o, chatgpt-4o-latest, gpt-4o-mini, o1, o1-mini, o3-mini")
                print("通过 https://platform.openai.com/settings/organization/limits 检查你的模型可用性")
            elif configure.active_ai == "SiliconFlow":
                print("通过 https://cloud.siliconflow.cn/models 检查你的模型可用性")
        else:
            print(f"\n当前模型：{configure.active_model[configure.active_ai]}")
        try:
            from openai import OpenAI
        except ImportError:
            print("请安装openai库以使用API")
            print("pip install openai")


    message: [dict] = []

    path = Path("./resource/prompt/tools.txt")
    prompt = path.read_text(encoding='utf-8')
    message.append({'role': 'system', 'content': prompt})
    path = Path("./resource/prompt/restrict.txt")
    prompt = path.read_text(encoding='utf-8')
    message.append({'role': 'system', 'content': prompt})

    already_warn_cache = False # 是否已经提醒过缓存未提交

    while cmd_handler.running:
        try:
            if not GlobalFlag.get_instance().skip_user_input:
                user_input = input("\n请输入内容（输入/help查看指令）: ").strip()
                if not user_input:
                    continue

                # 处理指令
                if user_input.startswith('/'):
                    [for_user, for_model] = cmd_handler.handle_command(user_input)
                    if len(for_model) != 0:
                        message.append({'role': 'system', 'content': for_model})
                    print(f"\n[系统提示] {for_user}")
                    continue


                if not already_warn_cache and len(cache.CatchInformation.get_instance().info)!=0:
                    print("\n[系统提示] 请注意，缓存中有未提交的信息，请使用/submit提交给AI，再次输入交流将强制交互主AI并忽视缓存")
                    already_warn_cache = True
                    continue
                already_warn_cache = False

                message.append({'role': 'user', 'content': user_input})
                # ------------------------------
                # ↑ 用户输入处理结束
                # ------------------------------
            GlobalFlag.get_instance().skip_user_input = False

            # 检查模型
            if Configure.get_instance().active_model is None:
                print("使用/model set <模型名>来设置模型")
                continue

            # ------------------------------
            # 调用模型
            # ------------------------------
            if configure.active_ai == "Ollama":
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
                    continue

                url = ""
                api = ""
                if configure.active_ai == "OpenAI_API":
                    api = configure.openai_api_key
                    url = "https://api.openai.com/v1"
                elif configure.active_ai == "SiliconFlow":
                    api = configure.siliconflow_api_key
                    url = "https://api.siliconflow.cn/v1"
                client = OpenAI(api_key=api, base_url=url)

                # 替换message中的所有system为user以匹配模型的输入
                if configure.active_ai == "OpenAI_API":
                    for i in range(len(message)):
                        if message[i]['role'] == 'system':
                            message[i]['role'] = 'user'

                stream = client.chat.completions.create(
                    model=configure.active_model[configure.active_ai],
                    messages=message,
                    stream=True,
                )
            else:
                print("AI加载器来源不可用")
                continue

            print("\nAI回复: ", end='', flush=True)
            full_response = write_stream_to_md(user_input, stream)

            message.append({'role': 'assistant', 'content': delete_think(full_response)})

            # 处理AI使用工具
            result = process_model_output(full_response)
            print(result["user_message"])
            if len(result['model_feedback']) != 0:
                message.append({'role': 'system', 'content': result['model_feedback']})


        except KeyboardInterrupt:
            print("\n检测到中断信号，正在退出...")
            Configure.get_instance().save()
            cmd_handler.running = False
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    main()