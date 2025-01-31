from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

from .commands import registry, Command, CommandContext


@registry.register(
    path="/fetch",
    description="网页内容获取",
    usage="/fetch <URL>"
)
class FetchCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "URL参数缺失", ""

        url = args[0].strip()
        try:
            content = fetch_web_content(url)
            return f"已获取网页内容：{url}", f"[网页摘要]: {content}"
        except Exception as e:
            return f"网页获取失败: {str(e)}", ""


def fetch_web_content(url: str, timeout: int = 10) -> str:
    """获取并解析网页内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # 带流式传输的请求以防止大文件
        with requests.get(url, headers=headers, timeout=timeout, stream=True) as response:
            response.raise_for_status()

            # 检测编码
            if response.encoding is None:
                response.encoding = 'utf-8'

            # 读取部分内容进行解析
            content = []
            for chunk in response.iter_content(decode_unicode=True, chunk_size=1024):
                if chunk:
                    content.append(chunk)
                if len(content) > 20:  # 限制读取20个chunk（约20KB）
                    break

            text = ''.join(content)

            # 使用BeautifulSoup提取主要内容
            soup = BeautifulSoup(text, 'html.parser')

            # 移除不需要的元素
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'meta']):
                element.decompose()

            # 提取文本内容
            content = []
            for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'article']):
                content.append(tag.get_text(strip=True, separator=' '))

            # 合并并限制输出长度
            full_text = '\n'.join(content)
            return full_text[:5000] + "..." if len(full_text) > 5000 else full_text

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"网络请求失败: {str(e)}")
    except ImportError:
        raise ImportError("需要安装依赖库：requests和beautifulsoup4，请执行 `pip install requests beautifulsoup4`")
    except Exception as e:
        raise RuntimeError(f"内容解析失败: {str(e)}")