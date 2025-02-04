import re

import requests
from typing import List, Tuple, Any

from core.cache import GlobalFlag
from tool.base_tool import BaseTool, ToolRegistry

directory = "./paper_space"

SEMANTIC_API = "https://api.semanticscholar.org/graph/v1"


@ToolRegistry.register("s2_search")
class SearchTool(BaseTool):
    """工具类用于搜索学术论文"""

    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        pattern = r'<s2_search\s+query="([^"]+)"\s+limit="(\d+)"\s*/>'
        matches = re.finditer(pattern, content)
        return [('s2_search', (m.group(1), int(m.group(2)))) for m in matches]

    def execute(self, user_output, model_output, args) -> None:
        query, limit = args
        if not query:
            user_output.append("搜索关键词为空。")
            return

        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        # headers = {"X-API-KEY": "YOUR_SEMANTIC_SCHOLAR_API_KEY"}
        headers = None
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,abstract,paperId,url"
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            user_output.append(f"搜索失败，状态码: {response.status_code}")
            model_output.append(f"论文搜索失败，状态码: {response.status_code}")
            GlobalFlag.get_instance().skip_user_input = True
            return

        results = response.json().get("data", [])
        if not results:
            user_output.append("未找到匹配的论文。")
            model_output.append("未找到匹配的论文。")
            GlobalFlag.get_instance().skip_user_input = True
            return

        user_output.append(f"找到 {len(results)} 篇论文：")
        all_res = []
        for idx, paper in enumerate(results, 1):
            title = paper.get("title")
            authors = ", ".join([author["name"] for author in paper.get("authors", [])[:3]])
            year = paper.get("year", "未知年份")
            url = paper.get("url", "无URL")
            user_output.append(f"{idx}. {title} | 作者: {authors} | 年份: {year} | 链接: {url}")
            all_res.append(f"{idx}. {title} | 作者: {authors} | 年份: {year} | 链接: {url}")
        model_output.append("".join(all_res))
        GlobalFlag.get_instance().skip_user_input = True


@ToolRegistry.register("s2_recommend")
class RecommendTool(BaseTool):
    """工具类用于根据基础论文推荐相关论文"""

    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        pattern = r'<s2_recommend\s+paper_id="([^"]+)"\s+limit="(\d+)"\s*/>'
        matches = re.finditer(pattern, content)
        return [('s2_recommend', (m.group(1), int(m.group(2)))) for m in matches]

    def execute(self, user_output, model_output, args) -> None:
        paper_id, limit = args
        if not paper_id:
            user_output.append("论文ID为空。")
            model_output.append("提供的论文ID为空。")
            return

        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        # headers = {"X-API-KEY": "YOUR_SEMANTIC_SCHOLAR_API_KEY"}
        headers = None
        params = {
            "fields": "title,authors,year,abstract,paperId,url",
            "limit": limit
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            user_output.append(f"推荐失败，状态码: {response.status_code}")
            model_output.append(f"推荐失败，状态码: {response.status_code}")
            GlobalFlag.get_instance().skip_user_input = True
            return

        data = response.json()

        results = data.get("data", [])
        if not results:
            if data.get("title", None) is None:
                user_output.append("未找到推荐的论文。")
                model_output.append("未找到推荐的论文。")
                GlobalFlag.get_instance().skip_user_input = True
                return
            results = [data]

        user_output.append(f"基于论文 {paper_id} 推荐的论文：")
        all_res = []
        all_res.append(f"基于论文 {paper_id} 推荐的论文：")
        for idx, paper in enumerate(results, 1):
            title = paper.get("title")
            # 仅保留前3作者
            authors = ", ".join([author["name"] for author in paper.get("authors", [])[:3]])
            year = paper.get("year", "未知年份")
            url = paper.get("url", "无URL")
            user_output.append(f"{idx}. {title} | 作者: {authors} | 年份: {year} | 链接: {url}")
            all_res.append(f"{idx}. {title} | 作者: {authors} | 年份: {year} | 链接: {url}")
        model_output.append(all_res)
        GlobalFlag.get_instance().skip_user_input = True
