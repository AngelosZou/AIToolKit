from agent import summarizer
from command.fetch import fetch_web_content
from core.cache import CatchInformation, SearchResult, GlobalFlag
from tool.parser import ToolParser
from util.fomatter import delete_think


class ToolExecutor:
    def __init__(self):
        self.cache = CatchInformation.get_instance()
        self.search_result = SearchResult.get_instance()
        self.user_output = []
        self.model_output = []
        self.should_terminate = False

    def process(self, tools):
        i = 0
        while i < len(tools) and not self.should_terminate:
            tool_type, content = tools[i]

            if tool_type == 'cache':
                self._handle_cache(content)
                i += 1

            elif tool_type == 'search':
                self._handle_search(content)
                i += 1
                self.should_terminate = True

            elif tool_type == 'fetch':
                # 检查后续是否有summary
                has_summary = i+1 < len(tools) and tools[i+1][0] == 'summary'
                self._handle_fetch(content, has_summary)
                if has_summary:
                    i += 2  # 跳过下一个summary工具
                else:
                    i += 1
                self.should_terminate = True

            elif tool_type == 'summary':
                self._handle_summary()
                i += 1
                self.should_terminate = True

    def _handle_cache(self, content):
        self.cache.info = content
        self.user_output.append("\n✅ 信息已缓存")

    def _handle_search(self, query):
        GlobalFlag.get_instance().skip_user_input = True
        try:
            try:
                from googleapiclient.discovery import build
            except ImportError:
                self.user_output.append("⚠️ 请安装google-api-python-client库以使用搜索功能")
                self.model_output.append("Search failed")
                return
            # 调用搜索API（复用已有SearchCommand逻辑）
            service = build("customsearch", "v1", developerKey=...)
            result = service.cse().list(q=query, cx=..., num=5).execute()

            self.search_result.search_results = result.get('items', [])

            # 构建用户可见结果
            response = ["\n🔍 搜索结果："]
            for idx, item in enumerate(self.search_result.search_results, 1):
                response.append(f"{idx}. {item['title']}")

            self.user_output.append("\n".join(response))
            self.model_output.append("Search results cached. Use /fetch [number] to view.")

        except Exception as e:
            self.user_output.append(f"⚠️ 搜索失败: {str(e)}")
            self.model_output.append("Search failed")

    def _handle_fetch(self, url, has_summary):
        GlobalFlag.get_instance().skip_user_input = True
        try:
            # 复用现有fetch_web_content函数
            content = fetch_web_content(url)
            self.cache.info = content

            self.user_output.append(f"\n\n🌐 成功获取网页内容: {url}")
            self.model_output.append(f"Web content cached: {url}")

            if has_summary:
                self._handle_summary()
            else:
                self.model_output.append(f"网页内容提取: {content}")

        except Exception as e:
            self.user_output.append(f"\n⚠️ 网页获取失败: {str(e)}\n")
            self.model_output.append("Fetch failed")

    def _handle_summary(self):
        GlobalFlag.get_instance().skip_user_input = True
        if not self.cache.info:
            self.user_output.append("⚠️ 没有可总结的缓存内容")
            return

        try:
            summary = summarizer.process(self.cache.info, send_to_cache=True)
            self.user_output.append("\n📝 总结已完成\n")
            self.model_output.append(f"Summary cached: {summary[:50]}...")
        except Exception as e:
            self.user_output.append(f"⚠️ 总结失败: {str(e)}")


def process_model_output(content: str):
    content = delete_think(content)
    # 解析工具指令
    tools = ToolParser.parse(content)

    # 执行工具处理
    executor = ToolExecutor()
    executor.process(tools)

    # 构建返回结果
    return {
        'user_message': "\n".join(executor.user_output),
        'model_feedback': "\n".join(executor.model_output),
        'should_terminate': executor.should_terminate
    }