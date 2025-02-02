import re

class ToolParser:
    @staticmethod
    def parse(content: str):
        tools = []

        # 解析缓存工具
        for match in re.finditer(r'<cache>(.*?)</cache>', content, re.DOTALL):
            tools.append(('cache', match.group(1).strip()))

        # 解析搜索工具
        for match in re.finditer(r'<search\s+(.+?)\s*>', content):
            tools.append(('search', match.group(1).strip()))

        # 解析网页获取工具
        for match in re.finditer(r'<fetch\s+([^>]+)\s*>', content):
            tools.append(('fetch', match.group(1).strip()))

        # 解析总结工具
        if re.search(r'<summary>', content):
            tools.append(('summary', ''))

        return tools