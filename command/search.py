# 在原有导入基础上添加

from typing import List, Tuple

from core.cache import Cache, SearchResult
from .commands import registry, Command, CommandContext


@registry.register(
    path="/search",
    description="通过Google搜索内容",
    usage="/search <查询关键词>"
)
class SearchCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "请输入搜索关键词", ""

        try:
            from googleapiclient.discovery import build
        except ImportError:
            return "请安装google-api-python-client库以使用搜索功能", ""

        query = ' '.join(args)
        api_key = Cache.get_instance().google_api_key
        cse_id = Cache.get_instance().google_cse_id

        if not api_key or not cse_id:
            return "搜索功能未配置，请联系管理员设置API密钥。", ""

        try:
            service = build("customsearch", "v1", developerKey=api_key)
            result = service.cse().list(q=query, cx=cse_id, num=5).execute()
            items = result.get('items', [])

            if not items:
                return "未找到相关搜索结果", ""

            # 缓存搜索结果
            result = SearchResult.get_instance()
            result.search_results = items

            # 格式化结果
            response = ["搜索结果："]
            for idx, item in enumerate(items, 1):
                response.append(f"{idx}. [{item['title']}]({item['link']})")

            return "\n".join(response) + "\n\n使用/fetch <序号> 获取对应内容", ""
        except Exception as e:
            return f"搜索失败：{str(e)}", ""