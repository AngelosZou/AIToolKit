import time
from pathlib import Path
from ollama import chat
import ollama
import core.cache
from command.commands import CommandHandler
from core import cache
from core.cache import Cache, GlobalFlag
from tool.excutor import process_model_output
from util.fomatter import delete_think


def write_stream_to_md(user_input: str, stream, filename: str = "conversation.md"):
    """实时将流式响应写入Markdown文件"""
    md_file = Path(filename)
    try:
        with md_file.open('a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            # f.write(f"\n\n## 对话记录 - {timestamp}\n")
            # f.write(f"**用户输入**: {user_input}\n**AI回复**: ")

            full_response = []
            try:
                for chunk in stream:
                    content = chunk.message.content
                    print(content, end='', flush=True)
                    # f.write(content)
                    # f.flush()
                    full_response.append(content)
            except KeyboardInterrupt:
                print("\n检测到中断信号，打断模型输出，抛弃未完成的信息")
                return ""
            # f.write("\n")
            return ''.join(full_response)
    except Exception as e:
        print(f"\n文件写入错误: {str(e)}")
        return None

def main():
    cmd_handler = CommandHandler()

    cache_data = core.cache.Cache.get_instance()
    if cache_data.active_model is None:
        print(f"\n模型未加载")
        print(f"\n可选的模型列表：")
        print(ollama.list())
        print("使用/model set <模型名>来设置模型")
    else:
        print(f"\n当前模型：{cache_data.active_model}")

    message: [dict] = []

    history: str = ""

    # 加载提示词
    path = Path("./resource/prompt/tools.txt")
    prompt = path.read_text(encoding='utf-8')
    history += prompt + "\n\n"
    message.append({'role': 'system', 'content': prompt})
    path = Path("./resource/prompt/restrict.txt")
    prompt = path.read_text(encoding='utf-8')
    history += prompt + "\n\n"
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
                    history += for_model
                    if len(for_model) != 0:
                        message.append({'role': 'system', 'content': for_model})
                    print(f"\n[系统提示] {for_user}")
                    continue


                if not already_warn_cache and len(cache.CatchInformation.get_instance().info)!=0:
                    print("\n[系统提示] 请注意，缓存中有未提交的信息，请使用/submit提交给AI，再次输入交流将强制交互主AI并忽视缓存")
                    already_warn_cache = True
                    continue
                already_warn_cache = False

                history += f"\n[用户输入] {user_input}\n"
                message.append({'role': 'user', 'content': user_input})
                # ------------------------------
                # ↑ 用户输入处理结束
                # ------------------------------
            GlobalFlag.get_instance().skip_user_input = False

            # 处理普通对话
            stream = chat(
                model=Cache.get_instance().active_model,
                messages=message,
                stream=True
            )

            print("\nAI回复: ", end='', flush=True)
            full_response = write_stream_to_md(user_input, stream)

            history += f"\n[AI回复] {full_response}\n"
            message.append({'role': 'assistant', 'content': delete_think(full_response)})

            # 处理AI使用工具
            result = process_model_output(full_response)
            print(result["user_message"])
            history += f"\n[工具使用反馈] {result['model_feedback']}\n"
            if len(result['model_feedback']) != 0:
                message.append({'role': 'system', 'content': result['model_feedback']})


        except KeyboardInterrupt:
            print("\n检测到中断信号，正在退出...")
            Cache.get_instance().save()
            cmd_handler.running = False
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    main()