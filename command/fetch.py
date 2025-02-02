import re
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from requests import RequestException

from core.cache import CatchInformation, SearchResult
from .commands import registry, Command, CommandContext


@registry.register(
    path="/fetch",
    description="获取网页内容",
    usage="/fetch <URL或搜索序号>"
)
class FetchCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "请输入URL或搜索序号", ""

        input_arg = args[0].strip()
        res = SearchResult.get_instance()
        cache = CatchInformation.get_instance()

        # 处理数字输入（搜索序号）
        if input_arg.isdigit():
            index = int(input_arg) - 1
            if index < 0 or index >= len(res.search_results):
                return "无效的序号，请先进行搜索", ""
            url = res.search_results[index]['link']
        else:
            url = input_arg

        try:
            content = fetch_web_content(url)
            # 更新缓存信息
            res.url = url
            cache.info = content
            return (
                f"成功获取网页内容：{url}\n"
                "使用/summary 总结内容或/submit 提交给AI处理",
                ""
            )
        except Exception as e:
            return f"网页获取失败：{str(e)}", ""


# Constants
MAX_RAW_SIZE = 16 * 1024 * 1024  # 256KB安全截断
COMMON_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'big5', 'shift_jis', 'windows-1252']
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def detect_encoding(response: requests.Response, raw_data: bytes) -> str:
    """三层编码检测机制（无第三方依赖）"""
    # Layer 1: 验证响应头编码
    if response.encoding and response.encoding.lower() not in ['iso-8859-1', 'ascii']:
        try:
            _ = raw_data.decode(response.encoding, errors='strict')
            return response.encoding
        except (UnicodeDecodeError, LookupError):
            pass

    # Layer 2: 解析HTML meta标签
    meta_enc = None
    try:
        try:
            import lxml
        except ImportError:
            raise ImportError("lxml库未安装，请使用pip安装lxml库")
        soup = BeautifulSoup(raw_data[:16384], 'html.parser', from_encoding='utf-8')
        if meta := soup.find('meta', charset=True):
            meta_enc = meta['charset']
        else:
            if meta := soup.find('meta', {'http-equiv': re.compile(r'content-type', re.I)}):
                if match := re.search(r'charset\s*=\s*([\w-]+)', meta.get('content', ''), re.I):
                    meta_enc = match.group(1)
        if meta_enc:
            try:
                _ = raw_data.decode(meta_enc, errors='strict')
                return meta_enc
            except (UnicodeDecodeError, LookupError):
                pass
    except Exception:
        pass

    # Layer 3: 常见编码探测
    for enc in COMMON_ENCODINGS:
        try:
            _ = raw_data.decode(enc, errors='strict')
            return enc
        except UnicodeDecodeError:
            continue

    # Final fallback
    return 'utf-8'  # 即使有损也优先返回UTF-8

def extract_main_content(soup: BeautifulSoup, url: str) -> str:
    """智能正文定位策略"""
    # 知名站点专用规则
    if 'wikipedia.org' in url:
        if main := soup.find('div', id='mw-content-text'):
            return main.get_text('\n', strip=True)

    # 通用语义标签探测
    selectors = [
        ('article', None),
        ('main', None),
        ('div.content', 'class'),
        ('div.main-content', 'class'),
        ('div.post-content', 'class'),
        ('div.article-body', 'class')
    ]
    for selector, attr in selectors:
        if attr:
            elem = soup.find('div', class_=selector)
        else:
            elem = soup.find(selector)
        if elem:
            return elem.get_text('\n', strip=True)

    # 暴力模式：全文本提取
    return soup.body.get_text('\n', strip=True) if soup.body else ''

def fetch_web_content(url: str, timeout: int = 15) -> str:
    """
    增强版网页内容抓取函数
    :param url: 目标网页URL
    :param timeout: 超时时间（秒）
    :return: 清理后的正文内容（5000字符截断）
    """
    try:
        headers = {'User-Agent': USER_AGENT}

        # 流式下载（带智能截断）
        with requests.get(url, headers=headers, timeout=timeout, stream=True) as response:
            response.raise_for_status()

            # 收集原始字节数据
            raw_data = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    raw_data.extend(chunk)
                    # 提前终止条件检测
                    if b'</html>' in chunk.lower() or len(raw_data) > MAX_RAW_SIZE:
                        break

            # 编码检测与解码
            encoding = detect_encoding(response, bytes(raw_data))
            try:
                html = raw_data.decode(encoding, errors='replace')
            except LookupError:
                html = raw_data.decode('utf-8', errors='replace')

            # 内容提取管道
            soup = BeautifulSoup(html, 'lxml')
            for tag in ['script', 'style', 'nav', 'footer', 'header', 'meta', 'noscript']:
                [t.decompose() for t in soup.find_all(tag)]

            main_text = extract_main_content(soup, url)
            return _truncate_text(main_text)

    except RequestException as e:
        return f"[Network Error] {str(e)}"
    except Exception as e:
        return f"[Parser Error] {str(e)}"

def _truncate_text(text: str, threshold: int = 5000) -> str:
    text = text.strip()
    if len(text) > threshold:
        return text[:threshold].rsplit('\n', 1)[0] + "\n...(truncated)"
    return text