import re
from typing import List, Tuple, Any

from agent import summarizer
from core.cache import GlobalFlag, CatchInformation
from tool.base_tool import ToolRegistry, BaseTool


@ToolRegistry.register('summary')
class SummaryCommand(BaseTool):
    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        tools = []
        if re.search(r'<summary>', content):
            tools.append(('summary', ''))
        return tools

    def execute(self, user_output, model_output, args):
        GlobalFlag.get_instance().skip_user_input = True
        if not CatchInformation.get_instance().info:
            user_output.append("⚠️ 没有可总结的缓存内容")
            return

        try:
            summary = summarizer.process(CatchInformation.get_instance().info, send_to_cache=True)
            user_output.append("\n📝 总结已完成")
            model_output.append(f"总结子AI系统的输出: {summary}")
        except Exception as e:
            user_output.append(f"⚠️ 总结失败: {str(e)}")