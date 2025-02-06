import json
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List
from colorama import Fore, Style

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, ScrollableContainer
from textual.widgets import (
    Tree,
    Label,
    MarkdownViewer,
    TextArea,
    Button,
    Input
)
from textual.reactive import reactive

from core.history import History
from .widget.UserInput import UserInput


# 消息类型定义
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
    show_raw: reactive[bool] = reactive(False)
    messages: reactive[List[ChatMessage]] = reactive([])

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
        self.mount(textarea)

# 主应用类
class ChatApp(App):
    CSS = """
    #main {
        layout: horizontal;
        height: 100%;
    }
    #sidebar {
        width: 20%;
        border-right: heavy $primary;
    }
    #content {
        width: 60%;
        padding: 1;
    }
    #tools {
        width: 20%;
        border-left: heavy $primary;
    }

    .message-header {
        height: 3;
        margin-bottom: 1;
    }
    .message-container {
        height: auto;
        scrollbar-size: 0 0;
        background: $surface;
    }
    .message-container:focus {
        border: none;
    }
    /* 原始模式内容 */
    .raw-message {
        height: auto;
        scrollbar-size: 0 0;
        background: $surface;
    }
    .raw-message:focus {
        border: none;
    }
    .chat-input {
        height: auto;
        min-height: 2;
        max-height: 5;
        margin-top: 1;
    }
    """

    def on_mount(self) -> None:
        self.theme = "textual-light"  # 设置默认主题

    def __init__(self):
        super().__init__()
        self.messages: List[ChatMessage] = []
        self.show_raw = False

    def compose(self) -> ComposeResult:
        yield Horizontal(
            HistorySidebar(),
            VerticalScroll(
                MessageDisplay(id="messages"),
                UserInput(id="chat-input", classes="chat-input"),
                id="content"
            ),
            VerticalScroll(
                Button("切换视图", id="toggle-view"),
                Button("保存记录", id="save"),
                Button("退出", id="exit"),
                id="tools"
            ),
            id="main"
        )

    @on(Button.Pressed, "#toggle-view")
    def toggle_view_mode(self):
        self.show_raw = not self.show_raw
        self.query_one(MessageDisplay).show_raw = self.show_raw

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.exit(str(event.button))

    def refresh_messages(self):
        display = self.query_one(MessageDisplay)
        display.messages = self.messages.copy()
        display.scroll_end()

# 历史记录侧边栏（修正版）
class HistorySidebar(Tree):
    def __init__(self):
        super().__init__("历史记录", id="sidebar")
        self.history_dir = Path("./history")
        self.history_dir.mkdir(exist_ok=True)
        self.load_history()

    def load_history(self):
        self.clear()
        for file in self.history_dir.glob("*.json"):
            self.root.add_leaf(file.stem, {"path": str(file)})

    @on(Tree.NodeSelected)
    def load_selected_history(self, event: Tree.NodeSelected):
        if (path := event.node.data.get("path")) and (file := Path(path)).exists():
            try:
                # 加载没有路径和后缀的纯文件名
                History.load(file.name.replace(".json", ""))
                history: History = History.MAIN_HISTORY
                self.app.messages = [
                    ChatMessage(
                        content=his.for_user,
                        type=MsgType.from_role(his.role.value if isinstance(his.role.value, str) else his.role.value[0]),
                        think=his.think
                    ) for his in history.history
                ]
                self.app.refresh_messages()
            except Exception as e:
                self.app.notify(f"加载失败: {str(e)}", severity="error")

if __name__ == "__main__":
    app = ChatApp()
    app.run()