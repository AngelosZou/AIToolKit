from dataclasses import dataclass
from enum import Enum
from typing import List

from colorama import Fore, Style
from textual import on
from textual.containers import ScrollableContainer, VerticalScroll
from textual.events import Print
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import MarkdownViewer, TextArea

from core.cache import GlobalFlag


class MsgType(Enum):
    USER = ("user", "#E1FFFF")       # 用户消息
    SYSTEM = ("system", "#FAFAD2")   # 系统消息
    ASSISTANT = ("assistant", "#F5FFFA")  # 助手消息

    @staticmethod
    def from_role(role: str):
        return {
            "user": MsgType.USER,
            "system": MsgType.SYSTEM,
            "assistant": MsgType.ASSISTANT
        }[role]

    @property
    def color(self):
        return self.value[1]

    @property
    def role(self):
        return self.value[0]


@dataclass
class ChatMessage:
    content: str
    type: MsgType
    think: str = ""

# 消息显示组件
class MessageDisplay(VerticalScroll):
    show_raw: reactive[bool] = reactive(True)
    messages: reactive[List[ChatMessage]] = reactive([])
    last_text: TextArea = None

    # def on_mount(self) -> None:
    #     self.begin_capture_print()

    @on(Print)
    def on_print(self, event: Print):
        # self.notify(event.text)
        if GlobalFlag.get_instance().is_communicating:
            if self.messages[-1].type == MsgType.ASSISTANT:
                self.messages[-1].content += event.text
            else:
                self.messages.append(ChatMessage(content=event.text, type=MsgType.ASSISTANT))
                self.refresh_display()
        else:
            self.notify(event.text)

    def create_message(self, role: MsgType, content: str, think: str = "") -> None:
        self.messages.append(ChatMessage(content=content, type=role, think=think))
        self.refresh_display()

    def append_content(self, content: str) -> None:
        self.messages[-1].content += content
        # self.refresh_display()

    def watch_messages(self) -> None:
        self.refresh_display()

    def watch_show_raw(self) -> None:
        self.refresh_display()

    def refresh_display(self) -> None:
        self.remove_children()
        for msg in self.messages:
            if self.show_raw:
                self._add_raw_message(msg)
            else:
                self._add_rendered_message(msg)
        self.scroll_end(animate=False)

    def _add_rendered_message(self, msg: ChatMessage) -> None:
        """使用ScrollableContainer实现带边框的消息容器"""
        container = ScrollableContainer(
            MarkdownViewer("↓ AI烧烤中\n\n" + msg.think + "\n\n↑ 烧烤过程\n\n" + msg.content if len(msg.think) != 0 else msg.content),
            classes="message-container",
        )
        container.styles.border = ("heavy", msg.type.color)
        self.mount(container)

    def _add_raw_message(self, msg: ChatMessage) -> None:
        """使用TextArea的正确配置"""
        if len(msg.think) != 0:
            res = f"{msg.type.role}:\n{Fore.LIGHTBLACK_EX}{msg.think}{Style.RESET_ALL}\n\n{msg.content}"
        else:
            res = f"{msg.type.role}:\n{msg.content}"
        textarea = TextArea(
            text=res,
            read_only=True,
            language=None,  # 禁用语法高亮
            classes="raw-message",
        )
        textarea.styles.background = msg.type.color
        MessageDisplay.last_text = textarea
        self.mount(textarea)

    def add_content(self, content: str):
        if self.show_raw:
            MessageDisplay.last_text.insert(content, location=MessageDisplay.last_text.document.end)
            MessageDisplay.last_text.scroll_to(MessageDisplay.last_text.document.end)


