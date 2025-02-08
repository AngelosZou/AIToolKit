from textual import on
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button
from pathlib import Path
import re

from core.history import History
from core.Project import Project


class RenameInput(Input):
    """重命名输入框，限制特殊字符和最大长度"""

    BINDINGS = [("escape", "cancel", "取消")]

    def __init__(self):
        super().__init__(
            placeholder="输入新名称 (允许字母/数字/_-，最大50字符)",
            max_length=50
        )

    def action_cancel(self) -> None:
        """按ESC键关闭输入框"""
        self.app.query_one("#rename-container").remove()


class RenameVertical(Vertical):
    """重命名输入框容器"""

    def __init__(self):
        super().__init__(RenameInput(),
                         Horizontal(
                             Button("确认", id="confirm-rename"),
                             Button("取消", id="cancel-rename"),
                         ),
                         id="rename-container")

    @on(Button.Pressed, "#confirm-rename")
    def confirm_rename(self, event: Button.Pressed) -> None:
        """确认重命名操作"""
        input_box = self.query_one(RenameInput)
        new_name = input_box.value.strip()
        history = History.MAIN_HISTORY
        history_dir = Path("./history")

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

            # 刷新侧边栏
            from tui.widget.CombinedSidebar import CombinedSidebar
            self.app.query_one(CombinedSidebar).load_history()
            self.notify(f"重命名为 {new_name} 成功")
        except Exception as e:
            self.notify(f"重命名失败: {str(e)}", severity="error")
        finally:
            self.app.query_one("#rename-container").remove()

    @on(Button.Pressed, "#cancel-rename")
    def cancel_rename(self, event: Button.Pressed) -> None:
        """取消重命名操作"""
        self.app.query_one("#rename-container").remove()