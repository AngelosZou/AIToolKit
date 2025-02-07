import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from colorama import Fore, Style

import core.cache
from core.SurrogateIO import sio_print, try_create_message
from tui.message import MsgType
from tui.widget.UserInput import get_input_from_textual
from command.commands import CommandHandler
from command.file import read_file_content
from core import cache
from core.cache import Configure, GlobalFlag
from core.communicate import communicate
from core.history import History, MessageRole
from core.source.sources import SourceRegistry
from core.sync.StateManager import StateManager, State
from tool.base_tool import process_model_output


def start_process():
    """
    开始一段新对话的初始化处理
    :return:
    """


async def main():
    # try_create_message(MsgType.SYSTEM)
    # sio_print(f"事件循环: {loop}")
    # if loop is None:
    #     loop = asyncio.get_running_loop()
    cmd_handler = CommandHandler()

    configure = core.cache.Configure.get_instance()

    if configure.active_ai is None:
        try_create_message(MsgType.SYSTEM)
        sio_print(f"\n未选择AI加载器来源")
        sio_print(f"\n可选的AI列表：")
        sio_print(SourceRegistry.sources)
        sio_print("使用/ai set <AI名>来设置AI")
    else:
        try_create_message(MsgType.SYSTEM)
        sio_print(f"\n当前AI加载器来源：{configure.active_ai}")

    history = History.get_or_create()

    try_create_message(MsgType.SYSTEM)
    # path = Path("./resource/prompt/tools.txt")
    # prompt = path.read_text(encoding='utf-8')
    # history.add_message(MessageRole.SYSTEM, prompt, f"加载提示词 tools.txt")
    # sio_print("加载提示词 tools.txt")
    path = Path("./resource/prompt/restrict.txt")
    prompt = path.read_text(encoding='utf-8')
    history.add_message(MessageRole.SYSTEM, prompt, f"加载提示词 restrict.txt")
    sio_print("加载提示词 restrict.txt")

    already_warn_cache = False # 是否已经提醒过缓存未提交

    try_create_message(MsgType.SYSTEM)
    # 遍历 ./ref_space/ 文件夹下的所有文件
    file_count = 0
    if Path("./ref_space/").exists():
        for file in Path("./ref_space/").iterdir():
            if file.is_file():
                # 使用file.read_file_content(file)读取文件内容
                history.add_message(MessageRole.SYSTEM, read_file_content(file), "")
                file_count += 1
        if file_count != 0:
            msg = f"从 ./ref_space/ 中读取到了{file_count}个本地文件提交给AI"
            history.add_message(MessageRole.SYSTEM, "", msg)
            sio_print(msg)
        else:
            msg = f"未在 ./ref_space/ 中读取到本地文件"
            history.add_message(MessageRole.SYSTEM, "", msg)
            sio_print(msg)

    skip_count = 0
    while cmd_handler.running:
        try:
            if (not GlobalFlag.get_instance().skip_user_input or
                    (skip_count >= configure.max_skip_input_turn != -1)
                or GlobalFlag.get_instance().force_stop):
                if not GlobalFlag.get_instance().is_app_running:
                    sio_print(f"{Fore.RED}------------------------------------------------------{Style.RESET_ALL}")

                # ------------------------------
                # 根据是否存在APP来处理数据
                if GlobalFlag.get_instance().is_app_running:
                    state_manager = StateManager.get_or_create()
                    await state_manager.set_state(State.WAITING_FOR_INPUT)
                    await state_manager.wait_for_state(State.FINISH_INPUT)
                    user_input = await get_input_from_textual()
                    await state_manager.set_state(State.PROCESSING)
                else:
                    user_input = input("请输入内容（输入/help查看指令）: ").strip()
                if not user_input:
                    continue

                # 处理指令
                if user_input.startswith('/'):
                    [for_user, for_model] = cmd_handler.handle_command(user_input)
                    if len(for_model) != 0:
                        # message.append({'role': 'system', 'content': for_model})
                        history.add_message(MessageRole.SYSTEM, for_model, for_user)
                    try_create_message(MsgType.SYSTEM)
                    sio_print(f"\n[系统提示] {for_user}")
                    continue


                if not already_warn_cache and len(cache.CatchInformation.get_instance().info)!=0:
                    try_create_message(MsgType.SYSTEM)
                    sio_print("\n[系统提示] 请注意，缓存中有未提交的信息，请使用/submit提交给AI，再次输入交流将强制交互主AI并忽视缓存")
                    already_warn_cache = True
                    continue
                already_warn_cache = False

                history.add_message(MessageRole.USER, user_input, user_input)
                # message.append({'role': 'user', 'content': user_input})
                # ------------------------------
                # ↑ 用户输入处理结束
                # ------------------------------

                GlobalFlag.get_instance().force_stop = False
            else:
                skip_count += 1
                if skip_count > int(Configure.get_instance().max_skip_input_turn/2) and skip_count != -1:
                    history.add_message(MessageRole.SYSTEM, f"[系统消息] 已经连续跳过{skip_count}轮用户输入，请减少不必要的工具使用，达到最大轮次{Configure.get_instance().max_skip_input_turn}将强制停止AI控制", "")
                    # message.append({'role': 'system', 'content': f"[系统消息] 已经连续跳过{skip_count}轮用户输入，请减少不必要的工具使用，达到最大轮次{Configure.get_instance().max_skip_input_turn}将强制停止AI控制"})
            GlobalFlag.get_instance().skip_user_input = False

            # ------------------------------
            # 调用AI
            # ------------------------------
            try:
                # think, full_response = await asyncio.get_running_loop().run_in_executor(None, communicate, history.to_message())
                think, full_response = await communicate(history.to_message())
            except Exception as e:
                sio_print(f" run_in_executor 失败: {e}")
            # think, full_response = communicate(history.to_message())
            # ------------------------------

            history.add_message(MessageRole.ASSISTANT, full_response, full_response, think)
            # message.append({'role': 'assistant', 'content': full_response})

            # 处理AI使用工具
            result = process_model_output(full_response)
            if len(result["user_message"]) != 0:
                try_create_message(MsgType.SYSTEM)
                sio_print(result["user_message"])
            if len(result['model_feedback']) != 0:
                history.add_message(MessageRole.SYSTEM, result['model_feedback'], result['user_message'])
                # message.append({'role': 'system', 'content': result['model_feedback']})

            GlobalFlag.get_instance().is_communicating = False
            # 保存对话记录
            history.save()
            # save_history(timestamp, message)

        except KeyboardInterrupt:
            sio_print("\n检测到中断信号，正在退出...")
            Configure.get_instance().save()
            cmd_handler.running = False
        except Exception as e:
            sio_print(f"\n发生错误: {str(e)}")





if __name__ == "__main__":
    asyncio.run(main())