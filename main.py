import os
import sys
from pathlib import Path

from colorama import Fore, Style

import core.cache
from command.commands import CommandHandler
from command.file import read_file_content
from core import cache
from core.Project import Project
from core.SurrogateIO import sio_print, try_create_message
from core.cache import Configure, GlobalFlag
from core.communicate import communicate
from core.history import History, MessageRole
from core.prompt import reload_prompt
from core.source.sources import SourceRegistry
from core.sync.StateManager import StateManager, State, InitStateManager
from tool.base_tool import process_model_output
from tui.message import MsgType
from tui.widget.UserInput import get_input_from_textual


async def main():
    if Project.instance is None:
        try_create_message(MsgType.SYSTEM)
        sio_print(f"\n选择一个项目或创建一个项目来开始对话")
        return
    init_manager = InitStateManager.get_or_create()
    await init_manager.set_state(InitStateManager.InitState.STARTING)
    cmd_handler = CommandHandler()

    await init_manager.set_state(InitStateManager.InitState.LOADING_CONFIGURE)
    configure = core.cache.Configure.get_instance()

    await init_manager.set_state(InitStateManager.InitState.CHECKING_SOURCE)
    if configure.active_ai is None:
        try_create_message(MsgType.SYSTEM)
        sio_print(f"\n未选择AI加载器来源")
        sio_print(f"\n可选的AI列表：")
        sio_print(SourceRegistry.sources)
        sio_print("使用/ai set <AI名>来设置AI")
    else:
        try_create_message(MsgType.SYSTEM)
        sio_print(f"\n当前AI加载器来源：{configure.active_ai}")

    await init_manager.set_state(InitStateManager.InitState.LOADING_HISTORY)
    history = History.get_or_create()

    reload_prompt(History.get_or_create())

    already_warn_cache = False  # 是否已经提醒过缓存未提交

    await init_manager.set_state(InitStateManager.InitState.LOADING_REFERENCE)
    reload_file(history)

    await init_manager.set_state(InitStateManager.InitState.LOADING_CODE)
    reload_code(history)

    await init_manager.set_state(InitStateManager.InitState.FINISH)
    try_create_message(MsgType.SYSTEM)
    GlobalFlag.get_instance().finish_init = True
    sio_print(f"\n对话已启动")

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
                        history.add_message(MessageRole.SYSTEM, for_model, for_user)
                    try_create_message(MsgType.SYSTEM)
                    sio_print(f"\n[系统提示] {for_user}")
                    continue

                if not already_warn_cache and len(cache.CatchInformation.get_instance().info) != 0:
                    try_create_message(MsgType.SYSTEM)
                    sio_print(
                        "\n[系统提示] 请注意，缓存中有未提交的信息，请使用/submit提交给AI，再次输入交流将强制交互主AI并忽视缓存")
                    already_warn_cache = True
                    continue
                already_warn_cache = False

                history.add_message(MessageRole.USER, user_input, user_input)
                # ------------------------------
                # ↑ 用户输入处理结束
                # ------------------------------

                GlobalFlag.get_instance().force_stop = False
            else:
                skip_count += 1
                if skip_count > int(
                        Configure.get_instance().max_skip_input_turn / 2) and Configure.get_instance().max_skip_input_turn != -1:
                    history.add_message(MessageRole.SYSTEM,
                                        f"[系统消息] 已经连续跳过{skip_count}轮用户输入，请减少不必要的工具使用，达到最大轮次{Configure.get_instance().max_skip_input_turn}将强制停止AI控制",
                                        "")
            GlobalFlag.get_instance().skip_user_input = False

            # ------------------------------
            # 重新加载提示词、文件、代码、工具
            reload_prompt(history, info=False)
            reload_file(history, info=False)
            reload_code(history, info=False)
            reload_tool(history, info=False)

            # ------------------------------
            # 调用AI
            # ------------------------------
            try:
                think, full_response = await communicate(history.to_message())
            except Exception as e:
                sio_print(f" communicate 错误: {e}")
            # ------------------------------

            history.add_message(MessageRole.ASSISTANT, full_response, full_response, think)

            # 处理AI使用工具
            result = process_model_output(full_response)
            if len(result["user_message"]) != 0:
                try_create_message(MsgType.SYSTEM)
                sio_print(result["user_message"])
            if len(result['model_feedback']) != 0:
                history.add_message(MessageRole.SYSTEM, result['model_feedback'], result['user_message'])

            GlobalFlag.get_instance().is_communicating = False
            # 保存对话记录
            history.save()

        except KeyboardInterrupt:
            sio_print("\n检测到中断信号，正在退出...")
            Configure.get_instance().save()
            cmd_handler.running = False
        except Exception as e:
            sio_print(f"\n发生错误: {str(e)}")


def reload_file(history, info=True):
    if info:
        try_create_message(MsgType.SYSTEM)
        sio_print(f"\n清空AI文件记忆")
    # 移除history中具有file标签的消息
    history.history = [msg for msg in history.history if "file" not in msg.tags]
    # 遍历 ref_space/ 文件夹下的所有文件
    file_count = 0
    if (Project.instance.root_path / "ref_space/").exists():
        for file in (Project.instance.root_path / "ref_space/").iterdir():
            if file.is_file():
                # 使用file.read_file_content(file)读取文件内容
                try:
                    history.add_message_head(MessageRole.SYSTEM, read_file_content(file), "", tags=["file"])
                except ValueError as e:
                    if info:
                        sio_print(f"读取文件{file}失败，已跳过: {e}")
                    continue
                file_count += 1
        if file_count != 0:
            msg = f"从 参考文献 中读取到了{file_count}个本地文件提交给AI"
            if info:
                sio_print(msg)
        else:
            msg = f"未在 参考文献 中读取到本地文件"
            if info:
                sio_print(msg)


def reload_code(history, info=True):
    if info:
        try_create_message(MsgType.SYSTEM)
        sio_print(f"\n清空AI代码记忆")
    history.history = [msg for msg in history.history if "code" not in msg.tags]
    # 遍历 ref_space/ 文件夹下的所有文件
    file_count = 0
    if (Project.instance.root_path / "code_space/").exists():
        for file in (Project.instance.root_path / "code_space/").iterdir():
            if file.is_file():
                try:
                    history.add_message_head(MessageRole.SYSTEM,
                                             f"*代码空间*可编辑文件{file.name}" + read_file_content(file), "",
                                             tags=["code"])
                except ValueError as e:
                    if info:
                        sio_print(f"读取代码{file}失败，已跳过: {e}")
                    continue
                file_count += 1
        if file_count != 0:
            msg = f"从 代码空间 中读取到了{file_count}个本地文件提交给AI"
            if info:
                sio_print(msg)
        else:
            msg = f"未在 代码空间 中读取到本地文件"
            if info:
                sio_print(msg)


def reload_tool(history, info=True):
    if info:
        try_create_message(MsgType.SYSTEM)
        sio_print(f"\n清空AI代码记忆")
    history.history = [msg for msg in history.history if "tool" not in msg.tags]

    file_count = 0
    if Path("./resource/prompt/tool").exists():
        for file in Path("./resource/prompt/tool").iterdir():
            if file.is_file() and file.suffix == ".txt" and history.tool_settings.get(file.stem, True):
                try:
                    history.add_message_head(MessageRole.SYSTEM, f"加载*工具*信息{file.stem}" + read_file_content(file),
                                             "", tags=["tool"])
                except ValueError as e:
                    if info:
                        sio_print(f"读取工具{file}失败，已跳过: {e}")
                    continue
        if file_count != 0:
            msg = f"加载了{file_count}个启用的AI工具"
            if info:
                sio_print(msg)
        else:
            msg = f"没有启用任何工具"
            if info:
                sio_print(msg)


if __name__ == "__main__":
    from tui.ChatAPP import ChatApp

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        os.system("chcp 65001")
    except Exception as e:
        pass

    app = ChatApp()
    app.run()
