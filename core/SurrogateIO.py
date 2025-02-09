import re

from core.cache import GlobalFlag
from tui.message import MsgType


def sio_print(msg, end="\n", flush=False)->None:
    """
    根据APP启用与否，将数据转发到APP的消息显示组件，或者打印到终端
    """
    from tui.ChatAPP import ChatApp
    from tui.message import MessageDisplay

    if GlobalFlag.get_instance().is_app_running:
        # 使用正则表达式去除
        msg = re.sub(r'\x1b\[\d+m', '', msg)
        ChatApp.instance.query_one(MessageDisplay).append_content(msg+end)
        ChatApp.instance.query_one(MessageDisplay).add_content(msg+end)
    else:
        print(msg, end=end, flush=flush)


def try_create_message(role: MsgType, content: str="", think: str = "") -> None:
    from tui.ChatAPP import ChatApp
    from tui.message import MessageDisplay
    if GlobalFlag.get_instance().is_app_running:
        ChatApp.instance.query_one(MessageDisplay).create_message(role, content, think)
