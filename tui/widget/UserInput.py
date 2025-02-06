from copy import copy

from textual import events
from textual.widgets import Input, TextArea

from tui.message import MsgType, MessageDisplay, ChatMessage
from core.sync.StateManager import StateManager, State


class UserInput(TextArea):
    to_send = ""

    async def _on_key(self, event):
        if event.key == "enter":
            event.prevent_default().stop()
            self.insert("\n")
        if event.key == "E":
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

