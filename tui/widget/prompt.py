from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Checkbox, Button

from core.history import History
from core.prompt import Prompt, reload_prompt


class PromptManager(VerticalScroll):
    def __init__(self):
        super().__init__(id="prompt-container")
        self.prompt_dir = Path("./resource/prompt/")
        self.prompt_files = []
        if self.prompt_dir.exists():
            self.prompt_files = list(self.prompt_dir.glob("*.txt"))

    def compose(self) -> ComposeResult:
        for file in self.prompt_files:
            name = file.stem
            yield Checkbox(name, value=Prompt.is_active(name), id=f"prompt-{name}")
        with Horizontal(id="prompt-buttons"):
            yield Button("确认", id="confirm-prompt")
            yield Button("取消", id="cancel-prompt")

    @on(Button.Pressed, "#confirm-prompt")
    def on_confirm(self):
        # 更新所有提示词状态
        for checkbox in self.query(Checkbox):
            name = checkbox.label.__str__()
            active = checkbox.value
            Prompt.set_active(name, active)

        # 重新加载提示词到历史记录
        reload_prompt(History.get_or_create())
        self.app.notify("提示词更改已更新至AI记忆")

        self.remove()

    @on(Button.Pressed, "#cancel-prompt")
    def on_cancel(self):
        self.remove()