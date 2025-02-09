from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Center, Middle, Vertical, VerticalScroll, Horizontal, HorizontalGroup
from textual.widgets import Label, Button, Checkbox

from core.history import History
from tui.widget.SettingsForm import SettingsForm


class ToolScreen(ModalScreen):
    """设置全屏模态窗口"""
    """优化后的设置全屏模态窗口"""
    CSS = """

    
    ToolScreen {
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

#all-tools {
    layout: grid;          /* 使用网格布局 */
    grid-size: 3;          /* 两列布局 */
    align: center middle;  /* 垂直水平居中 */
    height: auto;          /* 高度自适应 */
    min-height: 1;         /* 最小高度防止过小 */
    margin: 1 0;
}
"""


    def compose(self) -> ComposeResult:
        yield VerticalScroll(
                       Label("⚙ 工具启用 ⚙", id="settings-title"),
                        ToolContainer(id="all-tools"),
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
            for checkbox in self.query_one(ToolContainer).query(Checkbox):
                History.get_or_create().tool_settings[checkbox.id.split("-")[-1]] = checkbox.value
            self.dismiss()
            self.app.notify("设置工具设置成功！")
        except Exception as e:
            self.app.notify(f"保存失败: {str(e)}", severity="error")

    @on(Button.Pressed, "#cancel-settings")
    def cancel_settings(self, event: Button.Pressed):
        self.dismiss()


class ToolContainer(VerticalScroll):
    def compose(self) -> ComposeResult:
        his = History.get_or_create()
        # 获取所有工具
        path = Path("./resource/prompt/tool")
        # 遍历所有工具
        for tool in path.iterdir():
            if tool.is_file() and tool.suffix == ".txt":
                # 获取文件第一行的文本作为工具名
                with open(tool, "r", encoding='utf-8') as f:
                    tool_name = f.readline().strip()
                    # 使用工具名创建一个复选框
                    yield Checkbox(tool_name, value=his.tool_settings.get(tool.stem, True),
                                   id=f"tool-{tool.stem}", classes="setting-item")

