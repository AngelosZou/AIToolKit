import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

from textual import on
from textual.message import Message
from textual.widgets import Tree

from core.Project import Project
from core.cache import GlobalFlag
from core.history import History
from core.sync.Kernel import MainKernel
from core.sync.StateManager import StateManager, State
from tui.message import ChatMessage, MsgType


class FileOperationMessage(Message):
    """文件操作消息"""
    def __init__(self, action: str, path: str) -> None:
        self.action = action  # add/delete/select_project
        self.path = path
        super().__init__()


class CombinedSidebar(Tree):
    """重构后的侧边栏组件"""

    def __init__(self):
        super().__init__("项目空间", id="sidebar")
        self.projects_root = self.root.add("· 项目", expand=True)
        self.current_project: Optional[Project] = None

        # 初始化项目目录
        self.projects_dir = Path("./projects")
        self.projects_dir.mkdir(exist_ok=True)

        self.load_projects()

    def add_project_root(self):
        """添加项目根节点"""
        self.projects_root = self.root.add("· 项目", expand=True)

    def select_project(self, project_name: str):
        """选择指定项目"""
        self.current_project = Project(project_name)
        self.current_project.setup()
        self.load_project_contents()
        self.post_message(FileOperationMessage("select_project", str(self.current_project.root_path)))

    def load_projects(self):
        """加载所有项目"""
        Project.instance = None
        self.root.remove_children()
        self.add_project_root()
        self.projects_root.remove_children()
        for project_name in Project.list_projects():
            self.projects_root.add_leaf(f"· {project_name}", {"type": "project", "name": project_name})
        self.projects_root.add_leaf("+ 新建项目", {"type": "new_project"})

    def load_project_contents(self):
        """加载当前项目内容"""
        # 清空历史节点
        self.root.remove_children()

        # 添加项目相关内容
        if self.current_project:
            self.history_root = self.root.add(f"对话历史", expand=True)
            self.ref_root = self.root.add(f"参考文件", expand=True)
            self.code_root = self.root.add(f"代码空间", expand=True)
            self.return_root = self.root.add("← 返回", {"type": "return"})

            self.load_history()
            self.load_space("ref")
            self.load_space("code")

    def load_history(self):
        """加载当前项目历史记录"""
        self.history_root.remove_children()
        for file in self.current_project.dirs["history"].glob("*.json"):
            self.history_root.add_leaf(
                file.stem,
                {"type": "history", "path": str(file)}
            )
        self.history_root.add_leaf("+ 新建对话", {"type": "new_history"})

    def load_space(self, space_type: str):
        """加载指定空间内容"""
        root = self.ref_root if space_type == "ref" else self.code_root
        root.remove_children()

        for file in self.current_project.dirs[space_type].glob("*"):
            if file.is_file():
                root.add_leaf(
                    f" {file.name}",
                    {"type": space_type, "path": str(file)}
                )
        root.add_leaf("+ 添加文件", {"type": f"new_{space_type}"})

    @on(Tree.NodeSelected)
    async def handle_selection(self, event: Tree.NodeSelected):
        """处理节点选择事件"""
        node = event.node
        data = node.data or {}

        if data.get("type", "") == "project":
            self.select_project(data["name"])
        elif data.get("type", "") == "new_project":
            self._create_new_project()
        elif data.get("type", "") == "history":
            await self._load_history(node)
        elif data.get("type", "") in ("ref", "code"):
            self._handle_file_selection(data["path"])
        elif data.get("type", "") == "new_history":
            await self._create_new_history()
        elif data.get("type", "").startswith("new_"):
            space_type = data["type"][4:]
            self._add_new_file(space_type)
        elif data.get("type", "") == "return":
            self.load_projects()

    async def _create_new_history(self):
        # 检查控制权
        if StateManager.get_or_create().state != State.WAITING_FOR_INPUT:
            self.app.notify("⚠ 请等待当前对话完成", severity="warning")
            return
        if GlobalFlag.get_instance().occupy_user_input:
            self.notify("请等待核心完成处理")
            return
        # 清空历史记录
        History.get_or_create().clear()
        # 刷新界面
        self._refresh_interface()
        # 重启核心
        self.notify("正在重启对话核心...")
        # 调用核心
        MainKernel.restart_kernel()
        self.notify("对话已启动")


    def _create_new_project(self):
        """创建新项目"""
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()
        project_name = tk.simpledialog.askstring("新建项目", "请输入项目名称:")
        if project_name:
            if (self.projects_dir / project_name).exists():
                self.app.notify("项目已存在!", severity="warning")
                return
            self.select_project(project_name)
            self.load_projects()

    def _handle_file_selection(self, file_path: str):
        """处理文件选择（删除确认）"""
        path = Path(file_path)

        # 创建临时 Tkinter 窗口并置顶
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)  # 设置对话框置顶

        # 在临时窗口上弹出确认对话框
        if messagebox.askyesno("确认",
                               f"确定要移除 {path.name} 吗？",
                               parent=root):
            try:
                path.unlink()
                # 更健壮的空间类型判断
                space_type = "ref" if path.parent.name == "ref_space" else "code"
                self.load_space(space_type)
                self.post_message(FileOperationMessage("delete", str(path)))
                # try_create_message(MsgType.SYSTEM)
                # sio_print(f"文件 {path.name} 已删除，重新进入对话以应用修改至AI")
            except Exception as e:
                self.app.notify(f"删除失败: {str(e)}", severity="error")
            finally:
                root.destroy()  # 确保销毁临时窗口
        else:
            root.destroy()  # 用户取消时也要销毁

    async def _load_history(self, node):
        """加载历史记录"""
        if StateManager.get_or_create().state != State.WAITING_FOR_INPUT:
            self.app.notify("⚠ 请等待当前对话完成", severity="warning")
            return

        # 重启核心
        self.notify("正在重启对话核心...")
        # 调用核心
        MainKernel.restart_kernel()

        History.load(Path(node.data["path"]).stem)
        self._refresh_interface()

    def _refresh_interface(self):
        """刷新界面"""
        self.app.messages = [
            ChatMessage(
                content=his.for_user,
                type=MsgType.from_role(his.role.value),
                think=his.think
            ) for his in History.MAIN_HISTORY.history
        ]
        self.app.refresh_messages()
        self.load_space("ref")
        self.load_space("code")

    def _add_new_file(self, space_type: str):
        """添加新文件"""
        root = tk.Tk()
        root.attributes('-topmost', True)  # 确保对话框置顶
        root.withdraw()

        file_path = filedialog.askopenfilename(
            title=f"选择要添加到{space_type}的文件",
            filetypes=[("All Files", "*.*")]
        )

        if not file_path:
            return

        src = Path(file_path)
        dest_dir = self.current_project.dirs[space_type]
        dest = dest_dir / src.name

        if dest.exists():
            self.app.notify(f"文件 {src.name} 已存在", severity="warning")
            return

        try:
            shutil.copy(src, dest_dir)
            self.load_space(space_type)
        except Exception as e:
            self.app.notify(f"添加失败: {str(e)}", severity="error")
        finally:
            root.destroy()