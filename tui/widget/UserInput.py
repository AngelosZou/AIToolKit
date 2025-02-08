from copy import copy

from textual import events
from textual.widgets import Input, TextArea

from core.Project import Project
from core.SurrogateIO import sio_print
from core.cache import GlobalFlag
from core.sync.Kernel import MainKernel
from tui.message import MsgType, MessageDisplay, ChatMessage
from core.sync.StateManager import StateManager, State, InitStateManager


class UserInput(TextArea):
    to_send = ""

    async def _on_key(self, event):
        if event.key == "enter":
            event.prevent_default().stop()
            self.insert("\n")
        if event.key == "E":
            if Project.instance is None:
                self.notify("请选择一个项目或创建一个项目来开始对话")
                return
            init_manager = InitStateManager.get_or_create()
            if not GlobalFlag.get_instance().finish_init:
                self.notify("核心未启动，请选择一个对话或创建一个新对话")
                return
            state_manager = StateManager.get_or_create()
            if state_manager.state != State.WAITING_FOR_INPUT:
                self.notify("当前不是输入状态")
                return
            # 提交消息
            event.prevent_default().stop()
            value = copy(self.text)
            self.text = ""
            # 更新到客户端
            self.app.query_one(MessageDisplay).messages.append(ChatMessage(
                content = value,
                type = MsgType.USER,
                think = ""
            ))
            self.app.query_one(MessageDisplay).refresh_display()
            UserInput.to_send = value
            state_manager = StateManager.get_or_create()
            await state_manager.set_state(State.FINISH_INPUT)

async def get_input_from_textual():
    return UserInput.to_send

