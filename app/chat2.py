from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
from typing import List
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal, ScrollableContainer
from textual.widgets import (
    Tree,
    Label,
    MarkdownViewer,
    TextArea,
    Button,
    Input,
    Footer
)
from textual.reactive import reactive

# --- 数据定义 ---
class MsgType(Enum):
    USER = ("用户", "#6C8EBF")
    SYSTEM = ("系统", "#B85450")
    ASSISTANT = ("助手", "#82B366")

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
    timestamp: datetime = field(default_factory=datetime.now)

# --- 输入框组件 ---
class ChatInput(Input):
    def _on_key(self, event):
        # Shift+Enter 换行，Enter 发送
        if event.key == "enter" and not event.shift:
            event.prevent_default().stop()
            self.post_message(self.Submitted(self, self.value))
            self.value = ""
        elif event.key == "enter" and event.shift:
            event.prevent_default().stop()
            self.insert("\n")

# --- 消息显示组件 ---
class MessageDisplay(VerticalScroll):
    show_raw: reactive[bool] = reactive(False)
    messages: reactive[List[ChatMessage]] = reactive([])

    def watch_messages(self):
        self.refresh_display()

    def watch_show_raw(self):
        self.refresh_display()

    def refresh_display(self):
        self.remove_children()
        for msg in self.messages:
            container = ScrollableContainer(
                Horizontal(
                    Label(
                        f"{msg.type.role} [{msg.timestamp:%H:%M}]",
                        classes="msg-header"
                    ),
                    classes="msg-header-container"
                ),
                classes="message-container"
            )

            # 设置容器颜色边框
            container.styles.border = ("heavy", msg.type.color)

            if self.show_raw:
                content = TextArea(
                    text=msg.content,
                    read_only=True,
                    language=None,
                    classes="raw-content"
                )
                content.styles.height = "auto"
                content.styles.max_height = 30
            else:
                content = MarkdownViewer(md=msg.content, classes="md-content")

            container.mount(content)
            self.mount(container)
        self.scroll_end(animate=False)

# --- 主应用 ---
class ChatApp(App):

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.exit(str(event.button))

    def on_mount(self) -> None:
        self.theme = "textual-light"  # 设置默认主题

    CSS = """
    /* 布局结构 */
    #main {
        layout: horizontal;
        height: 100%;
        overflow: hidden;
    }
    #sidebar {
        width: 25%;
        border-right: heavy $primary;
    }
    #chat-area {
        width: 50%;
        height: 100%;
    }
    #tools {
        width: 25%;
        border-left: heavy $primary;
    }

    /* 消息容器 */
    .message-container {
        margin: 1 0;
        padding: 0 1;
        height: auto;
        max-height: 40vh;
    }

    /* 消息头 */
    .msg-header-container {
        height: 3;
        margin-bottom: 1;
    }
    .msg-header {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 0 2;
    }

    /* 原始模式内容 */
    .raw-content {
        height: auto;
        scrollbar-size: 0 0;
        background: $surface;
    }
    .raw-content:focus {
        border: none;
    }

    /* 输入框 */
    #chat-input {
        height: auto;
        min-height: 3;
        max-height: 20;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            # 历史侧边栏
            HistorySidebar(),
            # 主聊天区
            VerticalScroll(
                MessageDisplay(id="messages"),
                ChatInput(placeholder="输入消息 (Shift+Enter换行)", id="chat-input"),
                id="chat-area"
            ),
            # 工具面板
            VerticalScroll(
                Button("切换视图", id="toggle-view"),
                Button("保存记录", id="save"),
                Button("退出", id="exit"),
                id="tools"
            ),
            id="main"
        )
        yield Footer()

    @on(Button.Pressed, "#toggle-view")
    def toggle_view_mode(self):
        self.query_one(MessageDisplay).show_raw = not self.query_one(MessageDisplay).show_raw

    @on(ChatInput.Submitted)
    def handle_message(self, event: ChatInput.Submitted):
        new_msg = ChatMessage(
            content=event.value.strip(),
            type=MsgType.USER
        )
        self.query_one(MessageDisplay).messages.append(new_msg)
        self.process_response(event.value)

    @work(thread=True)
    def process_response(self, prompt: str):
        # 模拟异步处理
        import time
        time.sleep(1)

        response = ChatMessage(
            content=f"已收到：{prompt}",
            type=MsgType.ASSISTANT
        )

        self.call_from_thread(
            self.query_one(MessageDisplay).messages.append,
            response
        )

# 历史记录侧边栏（修正版）
class HistorySidebar(Tree):
    def __init__(self):
        super().__init__("历史记录", id="sidebar")
        self.history_dir = Path("../history")
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
                with open(file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    self.app.messages = [
                        ChatMessage(
                            content=msg["content"],
                            type=MsgType[msg["role"].upper()]
                        ) for msg in raw
                    ]
                    self.app.query_one(MessageDisplay).refresh_display()
            except Exception as e:
                self.app.notify(f"加载失败: {str(e)}", severity="error")



if __name__ == "__main__":
    app = ChatApp()
    app.run()