from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Center, Middle, Vertical, VerticalScroll, Horizontal
from textual.widgets import Label, Button

from tui.widget.SettingsForm import SettingsForm


class SettingsScreen(ModalScreen):
    """设置全屏模态窗口"""
    """优化后的设置全屏模态窗口"""
    CSS = """
    SettingsScreen {
        align: center middle;
    }
    
    #settings-dialog {
        width: 60%;
        height: 80%;
        border: round $primary;
        background: $surface;
        padding: 2;
    }
    
    #settings-content {
        height: 100%;
        overflow-y: auto;
        padding: 1;
    }
    
    #settings-title {
        text-style: bold;
        width: 100%;
        content-align: center top;
        padding: 1;
        border-bottom: solid $primary;
    }
    
    .dialog-buttons {
        margin-top: 1;
        padding: 1;
        height: auto;
        align: center middle;  /* 正确对齐 */
    }
    """


    def compose(self) -> ComposeResult:
        with VerticalScroll(id="settings-dialog"):
            yield Label("⚙ 设置 ⚙", id="settings-title")
            with VerticalScroll(id="settings-content"):
                yield SettingsForm()
            yield Horizontal(
                Button("保存", id="save-settings", variant="primary"),
                Button("取消", id="cancel-settings"),
                classes="dialog-buttons",
            )


    @on(Button.Pressed, "#save-settings")
    def save_settings(self, event: Button.Pressed):
        try:
            self.query_one(SettingsForm).save_settings()
            self.dismiss()
            self.app.notify("设置保存成功！")
        except Exception as e:
            self.app.notify(f"保存失败: {str(e)}", severity="error")

    @on(Button.Pressed, "#cancel-settings")
    def cancel_settings(self, event: Button.Pressed):
        self.dismiss()