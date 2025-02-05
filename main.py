import json
import time
from pathlib import Path

from colorama import Fore, Style

import core.cache
from command.commands import CommandHandler
from command.file import read_file_content
from core import cache
from core.cache import Configure, GlobalFlag
from core.communicate import communicate
from core.history import save_history
from tool.base_tool import process_model_output
from util.fomatter import delete_think


def main():
    cmd_handler = CommandHandler()

    configure = core.cache.Configure.get_instance()

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

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

    communicate.message = []
    message: [dict] = communicate.message
    communicate.name = timestamp

    path = Path("./resource/prompt/tools.txt")
    prompt = path.read_text(encoding='utf-8')
    message.append({'role': 'system', 'content': prompt})
    path = Path("./resource/prompt/restrict.txt")
    prompt = path.read_text(encoding='utf-8')
    message.append({'role': 'system', 'content': prompt})

    already_warn_cache = False # 是否已经提醒过缓存未提交

    # 遍历 ./ref_space/ 文件夹下的所有文件
    file_count = 0
    if Path("./ref_space/").exists():
        for file in Path("./ref_space/").iterdir():
            if file.is_file():
                # 使用file.read_file_content(file)读取文件内容
                message.append({'role': 'system', 'content': f"读取到了本地文件 {read_file_content(file)}"})
                file_count += 1
        if file_count != 0:
            print(f"\n从 ./ref_space/ 中读取到了{file_count}个本地文件提交给AI")
        else:
            print(f"\n未在 ./ref_space/ 中读取到本地文件")

    skip_count = 0
    while cmd_handler.running:
        try:
            if (not GlobalFlag.get_instance().skip_user_input or
                    (skip_count >= configure.max_skip_input_turn != -1)
                or GlobalFlag.get_instance().force_stop):
                print(f"{Fore.RED}------------------------------------------------------{Style.RESET_ALL}")

                user_input = input("请输入内容（输入/help查看指令）: ").strip()
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

                GlobalFlag.get_instance().force_stop = False
            else:
                skip_count += 1
                if skip_count > int(Configure.get_instance().max_skip_input_turn/2):
                    message.append({'role': 'system', 'content': f"[系统消息] 已经连续跳过{skip_count}轮用户输入，请减少不必要的工具使用，达到最大轮次{Configure.get_instance().max_skip_input_turn}将强制停止AI控制"})
            GlobalFlag.get_instance().skip_user_input = False

            # ------------------------------
            # 调用AI
            # ------------------------------
            full_response = communicate(message)
            # ------------------------------

            message.append({'role': 'assistant', 'content': delete_think(full_response)})

            # 处理AI使用工具
            result = process_model_output(full_response)
            print(result["user_message"])
            if len(result['model_feedback']) != 0:
                message.append({'role': 'system', 'content': result['model_feedback']})

            save_history(timestamp, message)

        except KeyboardInterrupt:
            print("\n检测到中断信号，正在退出...")
            Configure.get_instance().save()
            cmd_handler.running = False
        except Exception as e:
            print(f"\n发生错误: {str(e)}")





if __name__ == "__main__":
    main()