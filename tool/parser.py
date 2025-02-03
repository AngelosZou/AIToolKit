import re

class ToolParser:
    @staticmethod
    def parse(content: str):
        tools = []

        # 解析缓存工具
        for match in re.finditer(r'<cache>(.*?)</cache>', content, re.DOTALL):
            tools.append(('cache', match.group(1).strip()))

        # 解析搜索工具
        for match in re.finditer(r'<search\s+([^>]+)\s*>', content):
            tools.append(('search', match.group(1).strip()))

        # 解析网页获取工具
        for match in re.finditer(r'<fetch\s+([^>]+)\s*>', content):
            tools.append(('fetch', match.group(1).strip()))

        # 解析总结工具
        if re.search(r'<summary>', content):
            tools.append(('summary', ''))

        # 解析代码编写工具
        write_pattern = re.compile(
            r'<write\s+path="([^"]+)"[^>]*>\n?(.*?)\n?</write>',
            re.DOTALL  # 允许跨行匹配
        )

        # 解析所有write标签
        for match in write_pattern.finditer(content):
            filename = match.group(1).strip()
            code = match.group(2).strip()
            tools.append(('write', (filename, code)))

        # 解析代码运行工具
        if re.search(r'<run>', content):
            tools.append(('run', ''))

        # 解析代码测试工具
        if re.search(r'<test>', content):
            tools.append(('test', ''))

        return tools