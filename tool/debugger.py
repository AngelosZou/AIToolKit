import asyncio
import re
from typing import List, Tuple, Any

from agent import debugger
from core.cache import GlobalFlag
from core.sync.StateManager import StateManager, State
from tool.base_tool import ToolRegistry, BaseTool


@ToolRegistry.register('debugger')
class DebuggerTool(BaseTool):
    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        tools = []

        pattern = r'<debugger\s+ref=(True|False)\s*>(.*?)</debugger>'
        for match in re.finditer(pattern, content, re.DOTALL):
            ref_value = match.group(1) == 'True'  # 转换为布尔值
            description = match.group(2).strip()  # 获取标签内文本并去除首尾空白
            tools.append(("debugger", (ref_value, description)))
            return tools

        return tools

    def execute(self, user_output, model_output, args):
        try:
            ref, description = args
            GlobalFlag.get_instance().occupy_user_input = True
            StateManager.get_or_create().set_state(State.PROCESSING)
            task = asyncio.create_task(debugger.process(description, ref))

        except Exception as e:
            user_output.append(f"\n⚠ 调试器错误: {str(e)}")
            model_output.append("failed")