import time
from pathlib import Path
from ollama import chat
import ollama
import core.cache
from command.commands import CommandHandler
from core.cache import Cache


def write_stream_to_md(user_input: str, stream, filename: str = "conversation.md"):
    """实时将流式响应写入Markdown文件"""
    md_file = Path(filename)
    try:
        with md_file.open('a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            # f.write(f"\n\n## 对话记录 - {timestamp}\n")
            # f.write(f"**用户输入**: {user_input}\n**AI回复**: ")

            full_response = []
            for chunk in stream:
                content = chunk.message.content
                print(content, end='', flush=True)
                # f.write(content)
                # f.flush()
                full_response.append(content)
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

    history: str = ""

    while cmd_handler.running:
        try:
            user_input = input("\n请输入内容（输入/help查看指令）: ").strip()
            if not user_input:
                continue

            # 处理指令
            if user_input.startswith('/'):
                [for_user, for_model] = cmd_handler.handle_command(user_input)
                history += for_model
                print(f"\n[系统提示] {for_user}")
                continue

            history += f"\n[用户输入] {user_input}\n"

            # 处理普通对话
            stream = chat(
                model=Cache.get_instance().active_model,
                messages=[{'role': 'user', 'content': history}],
                stream=True
            )

            print("\nAI回复: ", end='', flush=True)
            full_response = write_stream_to_md(user_input, stream)

            history += f"\n[AI回复] {full_response}\n"

            if full_response:
                print("\n\n对话已实时保存")

        except KeyboardInterrupt:
            print("\n检测到中断信号，正在退出...")
            Cache.get_instance().save()
            cmd_handler.running = False
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    main()