import copy
from pathlib import Path

from core.SurrogateIO import sio_print, try_create_message
from core.history import History, Message, MessageRole
from tui.message import MsgType


class Prompt:
    _active_prompt = None

    default_prompt = {
        "tools": True,
        "restrict": True,
        "summarizer": False,
    }

    @staticmethod
    def active_all():
        Prompt._active_prompt = {}
        return Prompt.get_or_create()

    @staticmethod
    def get_or_create():
        if Prompt._active_prompt is None:
            active_prompt = copy.copy(Prompt.default_prompt)
            if Path("./resource/prompt/").exists():
                for file in Path("./resource/prompt/").iterdir():
                    # 如果文件是txt
                    if file.is_file() and file.suffix == ".txt":
                        if file.stem not in active_prompt:
                            active_prompt[file.stem] = True
            Prompt._active_prompt = active_prompt
        for file in Path("./resource/prompt/").iterdir():
            if file.is_file() and file.suffix == ".txt":
                if file.stem not in Prompt._active_prompt:
                    Prompt._active_prompt[file.stem] = True
        return Prompt._active_prompt

    @staticmethod
    def set_active(name: str, active: bool):
        if name not in Prompt.get_or_create():
            return False
        Prompt._active_prompt[name] = active
        return True

    @staticmethod
    def is_active(name: str):
        if name not in Prompt.get_or_create():
            if Path(f"./resource/prompt/{name}.txt").exists():
                Prompt._active_prompt[name] = True
        return Prompt.get_or_create().get(name, False)



def reload_prompt(history: History):
    """
    重新加载提示词
    :param history:
    :return:
    """
    # for msg in history.history:
        # if msg.tags is not None and "prompt" in msg.tags:
        #     history.history.remove(msg)

    history.history = [msg for msg in history.history if "prompt" not in msg.tags]
    try_create_message(MsgType.SYSTEM)
    sio_print("清空AI提示词记忆")

    # 遍历 ./resource/prompt/ 文件夹下的所有文件
    prompt_msg = []
    if Path("./resource/prompt/").exists():
        for file in Path("./resource/prompt/").iterdir():
            # 如果文件是txt
            if file.is_file() and file.suffix == ".txt":
                # 如果没启用则跳过
                if not Prompt.is_active(file.stem):
                    continue
                # 使用file.read_file_content(file)读取文件内容
                prompt = file.read_text(encoding='utf-8')
                prompt_msg.append(Message(MessageRole.SYSTEM, prompt, f"加载提示词 {file.name}", tags=["prompt"], think=""))
                sio_print("加载提示词 " + file.name)

    # 将prompt放到history开头
    history.history = prompt_msg +history.history