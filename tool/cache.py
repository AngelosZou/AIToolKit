import re
from typing import List, Tuple, Any

from core.cache import CatchInformation
from tool.base_tool import ToolRegistry, BaseTool


@ToolRegistry.register('cache')
class CacheCommand(BaseTool):

    @classmethod
    def parse(cls, content: str) -> list[tuple[str, str]]:
        tools = []

        # 解析缓存工具
        for match in re.finditer(r'<cache>(.*?)</cache>', content, re.DOTALL):
            tools.append(('cache', match.group(1).strip()))

        return tools

    def execute(self, user_output, model_output,  args):
        user_output.append("\n✅ 信息已缓存")
        CatchInformation.get_instance().info = args
