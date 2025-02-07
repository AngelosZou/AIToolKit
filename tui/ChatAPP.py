import asyncio
from pathlib import Path
from typing import List

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.widgets import (
    Tree,
    Button
)

import main
from core.SurrogateIO import sio_print
from tui.message import MsgType, ChatMessage, MessageDisplay
from core.cache import GlobalFlag
from core.history import History
from core.sync.StateManager import StateManager, State
from tui.widget.RenameInput import RenameVertical, RenameInput
from tui.widget.prompt import PromptManager
from .widget.UserInput import UserInput


async def fake_main():
    while True:
        state_manager = StateManager.get_or_create()
        await state_manager.wait_for_state(State.FINISH_INPUT)
        # await asyncio.sleep(5)
        await state_manager.set_state(State.WAITING_FOR_INPUT)
        sio_print("Fake main running")
        GlobalFlag.get_instance().is_communicating = True
        sio_print("Fake main running")
        await asyncio.sleep(5)
        sio_print("Hello")
        GlobalFlag.get_instance().is_communicating = False


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
    
    /* 重命名 */
    #rename-container {
        padding: 1;
        border: round $primary;
        margin-top: 1;
    }
    
    #rename-container Input {
        width: 100%;
    }
    
    #rename-container Horizontal {
        margin-top: 1;
        align: right middle;
    }
    """

    instance = None

    def on_mount(self) -> None:
        self.theme = "textual-light"  # 设置默认主题
        self.run_worker(self.start_core())

    def __init__(self):
        super().__init__()
        self.messages: List[ChatMessage] = []
        self.show_raw = True
        GlobalFlag.get_instance().is_app_running = True
        ChatApp.instance = self

    async def start_core(self):
        asyncio.create_task(main.main())

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
                Button("重命名", id="rename"),
                Button("提示词", id="prompt"),
                Button("退出", id="exit"),
                id="tools"
            ),
            id="main"
        )

    @on(Button.Pressed, "#prompt")
    def handle_prompt(self, event: Button.Pressed) -> None:
        """处理提示词按钮点击"""
        if StateManager.get_or_create().state != State.WAITING_FOR_INPUT:
            self.notify("只能在输入阶段修改提示词")
            return

        tools = self.query_one("#tools")
        if tools.query("#prompt-container"):
            return  # 防止重复添加

        # 创建并显示提示词管理界面
        try:
            prompt_manager = PromptManager()
            tools.mount(prompt_manager)
            self.query_one(PromptManager).focus()
        except Exception as e:
            self.notify(f"加载提示词失败: {str(e)}", severity="error")

    @on(Button.Pressed, "#toggle-view")
    def toggle_view_mode(self):
        self.show_raw = not self.show_raw
        self.query_one(MessageDisplay).show_raw = self.show_raw

    @on(Button.Pressed, "#rename")
    def handle_rename(self, event: Button.Pressed) -> None:
        """处理重命名按钮点击"""
        if StateManager.get_or_create().state != State.WAITING_FOR_INPUT:
            self.notify("只能在输入阶段重命名")
            return

        # 创建输入组件
        tools = self.query_one("#tools")
        if tools.query("#rename-container"):
            return  # 防止重复添加
        input_container = RenameVertical()
        tools.mount(input_container)
        self.query_one(RenameVertical).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.exit(str(event.button))
            GlobalFlag.get_instance().is_app_running = False

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
        if StateManager.get_or_create().state != State.WAITING_FOR_INPUT:
            self.notify("只能在输入阶段切换对话")
            return
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