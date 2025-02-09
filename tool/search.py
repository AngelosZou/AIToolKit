import re
from typing import List, Tuple, Any

from core.cache import GlobalFlag, Configure
from tool.base_tool import ToolRegistry, BaseTool


@ToolRegistry.register('search')
class SearchCommand(BaseTool):

    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        tools = []
        # 解析搜索工具
        for match in re.finditer(r'<search\s+([^>]+)\s*>', content):
            tools.append(('search', match.group(1).strip()))
        return tools

    def execute(self, user_output, model_output, args):
        GlobalFlag.get_instance().skip_user_input = True
        try:
            try:
                from googleapiclient.discovery import build
            except ImportError:
                user_output.append("⚠ 请安装google-api-python-client库以使用搜索功能")
                model_output.append("Search failed")
                return
            # 调用搜索API（复用已有SearchCommand逻辑）
            api_key = Configure.get_instance().google_api_key
            cse_id = Configure.get_instance().google_cse_id

            if not api_key or not cse_id:
                user_output.append(f"⚠ 搜索失败: 未配置API密钥")
                model_output.append("搜索失败，用户没有配置API或CSE ID，不要再尝试搜索，知道用户再次要求。")
                return
            service = build("customsearch", "v1", developerKey=api_key)
            result = service.cse().list(q=args, cx=cse_id, num=5).execute()

            search_results = result.get('items', [])

            # 构建用户可见结果
            response = ["\n 搜索结果："]
            for idx, item in enumerate(search_results, 1):
                response.append(f"{idx}. {item['title']}")

            user_output.append("\n".join(response))
            # 构建模型可见结果（含标题和URL）
            model_response = ["已经获取以下搜索结果（标题 + URL）："]  # 新增提示语
            for idx, item in enumerate(search_results, 1):
                model_response.append(f"{idx}. 标题：{item['title']}\n   URL：{item['link']}")  # 结构化格式
            model_response.append("请使用获取网页工具来获取具体内容。")  # 保留原有提示

            model_output.append("\n".join(model_response))  # 替换原有简单提示

        except Exception as e:
            user_output.append(f"⚠ 搜索失败: {str(e)}")
            model_output.append(f"搜索遇到错误 {str(e)}\n根据错误提示，如果是你可以修复的问题，尝试修复，否则直到用户再次请求，不要使用搜索。")

