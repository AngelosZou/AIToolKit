import re
from typing import List, Tuple, Any

from command.fetch import fetch_web_content
from core.cache import GlobalFlag, CatchInformation
from tool.base_tool import ToolRegistry, BaseTool, ToolProcessor


@ToolRegistry.register('fetch')
class FetchCommand(BaseTool):
    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        tools = []
        # 解析网页获取工具
        for match in re.finditer(r'<fetch\s+([^>]+)\s*>', content):
            tools.append(('fetch', match.group(1).strip()))
        return tools

    def execute(self, user_output, model_output, args):
        GlobalFlag.get_instance().skip_user_input = True
        try:
            content = fetch_web_content(args)
            CatchInformation.get_instance().info = content

            user_output.append(f"\n 成功获取网页内容: {args}")
            if not ToolProcessor.has_summary:
                model_output.append(f"Web content cached: {args}")

            model_output.append(f"网页内容提取: {content}")


        except Exception as e:
            user_output.append(f"\n⚠ 网页获取失败: {str(e)}")
            model_output.append("Fetch failed")