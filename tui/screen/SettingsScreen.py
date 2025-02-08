from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Center, Middle, Vertical, VerticalScroll, Horizontal, HorizontalGroup
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
        width: 70%;
        height: 100%;
        border: round $primary;
        background: $surface;
        padding: 2;
    }
    
    #settings-content {
        height: auto;
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
        height: auto;
        align: center bottom;
    }
    """

    CSS += """
.setting-item {
    layout: grid;          /* 使用网格布局 */
    grid-size: 1;          /* 两列布局 */
    align: center middle;  /* 垂直水平居中 */
    height: 5;          /* 高度自适应 */
    min-height: 5;         /* 最小高度防止过小 */
    margin: 1 0;
}
"""


    def compose(self) -> ComposeResult:
        yield VerticalScroll(
                       Label("⚙ 设置 ⚙", id="settings-title"),
                        SettingsForm(),
                        HorizontalGroup(
                            Button("保存", id="save-settings", variant="primary"),
                            Button("取消", id="cancel-settings"),
                            classes="dialog-buttons",
                        ),

                        id="settings-dialog",
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