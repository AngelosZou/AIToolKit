from pathlib import Path
from typing import Dict, List, Tuple, Any, Pattern
import re

from core.cache import CatchInformation, SearchResult
from util.fomatter import delete_think


class BaseTool:
    """工具命令基类"""
    tool_type: str

    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        """解析内容返回工具参数列表（需要子类覆盖）"""
        raise NotImplementedError

    def execute(self, user_output, model_output, args) -> None:
        """执行命令"""
        raise NotImplementedError

class ToolRegistry:
    """工具注册表"""
    commands: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, tool_type: str):
        """注册装饰器"""
        def decorator(command_class: BaseTool):
            cls.commands[tool_type] = {
                'class': command_class
            }
            command_class.tool_type = tool_type
            return command_class
        return decorator


# ----------------------
# 重构后的工具处理器
# ----------------------
class ToolProcessor:
    has_summary = False

    def __init__(self):
        self.parser = ToolParser()
        self.command_map = {cmd['class'].tool_type: cmd['class'] for cmd in ToolRegistry.commands.values()}

    def process(self, content: str) -> dict:
        content: str = delete_think(content)
        tools: list[Tuple[str, Any]] = self.parser.parse(content)
        if "summary" in [tool[0] for tool in tools]:
            ToolProcessor.has_summary = True

        model_output = []
        user_output = []
        for idx, (tool_type, args) in enumerate(tools):
            if tool_type not in self.command_map:
                continue

            command_class = self.command_map[tool_type]
            command = command_class()
            command.execute(user_output, model_output, args)

        ToolProcessor.has_summary = False
        return {
            'user_message': "\n".join(user_output),
            'model_feedback': "\n".join(model_output),
        }

class ToolParser:
    @staticmethod
    def parse(content: str) -> List[Tuple[str, Any]]:
        tools = []
        for cmd_type, cmd_info in ToolRegistry.commands.items():
            command_class: BaseTool = cmd_info['class']

            tools.extend(command_class.parse(content))

        return tools

# ----------------------
# 保持原有接口不变
# ----------------------
def process_model_output(content: str) -> dict:
    return ToolProcessor().process(content)