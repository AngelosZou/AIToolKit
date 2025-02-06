import os
import json
from pathlib import Path
from typing import List, Dict
from textual import work
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.theme import Theme, BUILTIN_THEMES
from textual.widgets import Button, Footer, Input, Label, RichLog, Tree
from textual.widget import Widget
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from textual.binding import Binding

# 消息类型颜色配置类
class MessageType:
    USER = "#6C8EBF"    # 用户消息颜色
    SYSTEM = "#B85450"  # 系统消息颜色
    RECEIVED = "#82B366" # 接收消息颜色
    THINK = "#AAAAAA"    # 思考状态颜色

# 响应数据对象，用于存储思考和响应内容
class ResponseObject:
    def __init__(self):
        self.think = ""    # 正在思考的中间过程信息
        self.response = "" # 最终响应内容

# 历史记录侧边栏组件
class HistorySidebar(Tree):
    def __init__(self):
        super().__init__("Chat History", id="sidebar")
        self.show_root = False  # 隐藏根节点
        self.history_dir = Path("../history/")  # 历史记录存储目录
        self.load_history()

    # 加载历史记录文件到树形组件
    def load_history(self):
        self.clear()
        for file in self.history_dir.glob("*.json"):
            node = self.root.add(file.name, {"file": str(file)})
            node.allow_expand = False  # 禁止展开节点

# 消息显示区域组件
class MessageDisplay(VerticalScroll):
    current_response = reactive(ResponseObject())  # 响应状态响应式变量

    # 监控响应对象变化并更新显示
    def watch_current_response(self, response: ResponseObject) -> None:
        self.update_display(response)

    # 更新消息显示内容
    def update_display(self, response: ResponseObject):
        self.query(".thinking").remove()
        self.query(".responding").remove()

        if response.think:
            self.mount(Label(response.think, classes="thinking", markup=False))
        if response.response:
            self.mount(Label(response.response, classes="responding", markup=False))

# 自定义聊天输入框组件
class ChatInput(Input):
    # 处理键盘事件
    def _on_key(self, event):
        if event.key == "enter":
            event.prevent_default().stop()
            self.post_message(self.Submitted(self, self.value))  # 提交消息
            self.value = ""
        elif event.key == "E":
            event.prevent_default().stop()
            self.insert("\n", len(self.value))  # 插入换行符

# 主应用程序类
class ChatApp(App):
    CSS = """
    #main { padding: 0 1; }
    #sidebar { width: 20%; }
    #content { width: 60%; }
    #tools { width: 20%; }
    .thinking { padding: 1; color: $text-muted; }
    """

    def on_mount(self) -> None:
        self.theme = "textual-light"  # 设置默认主题

    BINDINGS = [Binding("ctrl+s", "toggle_settings", "Settings")]  # 快捷键绑定

    def __init__(self):
        super().__init__()
        self.messages: List[Dict] = []  # 消息存储列表
        self.current_response = ResponseObject()  # 当前响应对象

    # 组合UI组件
    def compose(self) -> ComposeResult:
        yield Horizontal(
            HistorySidebar(),  # 左侧历史记录栏
            VerticalScroll(    # 中间主内容区域
                MessageDisplay(id="messages"),
                ChatInput(placeholder="Type your message..."),
                id="content"
            ),
            VerticalScroll(    # 右侧工具面板
                Button("Settings", id="settings"),
                Button("Tools", id="tools"),
                Button("Exit", id="exit"),
                id="right-panel"
            ),
            id="main"
        )
        yield Footer()  # 底部状态栏

    # 处理历史记录文件选择事件
    @on(Tree.NodeSelected)
    def load_history_file(self, event: Tree.NodeSelected):
        if file_path := event.node.data.get("file"):
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    self.messages = json.load(f)
                    self.refresh_messages()
            except Exception as e:
                self.notify(f"Error loading file: {str(e)}", severity="error")

    # 刷新消息显示
    def refresh_messages(self):
        display = self.query_one(MessageDisplay)
        display.current_response = ResponseObject()
        for msg in self.messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            content = content.replace("[", "\\[").replace("]", "\\]")
            color = MessageType.USER if role == "user" else MessageType.RECEIVED
            self.append_message(content, color)

    # 后台生成响应（模拟实现）
    @work(thread=True)
    def generate_response(self, prompt: str):
        response = ResponseObject()
        # 模拟分步思考过程
        for i in range(3):
            response.think = f"Thinking step {i+1}..."
            self.call_from_thread(self.update_response, response)

        # 最终响应结果
        response.think = ""
        response.response = "Here is the final answer"
        self.call_from_thread(self.finalize_response, response)

    # 更新响应状态
    def update_response(self, response: ResponseObject):
        self.current_response = response
        self.query_one(MessageDisplay).current_response = response

    # 完成响应处理
    def finalize_response(self, response: ResponseObject):
        self.messages.append({"role": "assistant", "content": response.response})
        self.current_response = ResponseObject()
        self.refresh_messages()

    # 处理消息提交事件
    @on(ChatInput.Submitted)
    def handle_message(self, event: ChatInput.Submitted):
        self.messages.append({"role": "user", "content": event.value})
        self.append_message(event.value, MessageType.USER)
        self.generate_response(event.value)

    # 添加消息到显示区域
    def append_message(self, text: str, color: str):
        display = self.query_one(MessageDisplay)
        display.mount(Label(text, markup=False))
        display.scroll_end(animate=False)

    # 处理按钮点击事件
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.exit(str(event.button))

if __name__ == "__main__":
    app = ChatApp()
    app.run()