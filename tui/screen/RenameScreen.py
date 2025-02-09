import re
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Center, Middle, Vertical, VerticalScroll, Horizontal, HorizontalGroup
from textual.widgets import Label, Button, Checkbox, Input

from core.Project import Project
from core.history import History
from tui.widget.SettingsForm import SettingsForm


class RenameScreen(ModalScreen):
    """设置全屏模态窗口"""
    """优化后的设置全屏模态窗口"""
    CSS = """

    
    RenameScreen {
        align: center middle;
    }
    
    #settings-dialog {
        width: 60%;
        height: 60%;
        border: round $primary;
        background: $surface;
        padding: 2;
    }
    
    #settings-content {
        height: auto;
        padding: 1;
    }
    
    #rename-title {
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

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Label("重命名", id="rename-title"),
            Input(id="input", placeholder="输入新名称", max_length=50, validate_on=["submitted"]),
            HorizontalGroup(
                Button("保存", id="confirm-rename", variant="primary"),
                Button("取消", id="cancel-settings"),
                classes="dialog-buttons",
            ),

            id="settings-dialog",
        )


    @on(Button.Pressed, "#confirm-rename")
    def confirm_rename(self, event: Button.Pressed) -> None:
        """确认重命名操作"""
        input_box = self.query_one(Input)
        new_name = input_box.value.strip()
        history = History.MAIN_HISTORY

        # 验证输入
        if not new_name:
            self.notify("名称不能为空", severity="error")
            return

        if not re.match(r"^[\w-]+$", new_name):
            self.notify("名称包含非法字符 (只允许字母/数字/下划线/连字符)", severity="error")
            return

        if Project.instance is None:
            self.notify("未选择项目")
            return

        if History.MAIN_HISTORY is None:
            self.notify("未加载对话")
            return

        history_dir = Project.instance.root_path / "history"

        # 构建新旧路径
        old_path = history_dir / f"{history.name}.json"
        new_path = history_dir / f"{new_name}.json"

        if new_path.exists():
            self.notify("该名称已存在，请使用其他名称", severity="error")
            return

        try:
            # 执行重命名
            if old_path.exists():
                old_path.rename(new_path)
            history.name = new_name  # 更新当前历史名称
            history.save()  # 立即保存

            self.dismiss()

            # 刷新侧边栏
            from tui.widget.CombinedSidebar import CombinedSidebar
            self.app.query_one(CombinedSidebar).load_history()
            self.notify(f"重命名为 {new_name} 成功")
        except Exception as e:
            self.notify(f"重命名失败: {str(e)}", severity="error")

    @on(Button.Pressed, "#cancel-settings")
    def cancel_settings(self, event: Button.Pressed):
        self.dismiss()




