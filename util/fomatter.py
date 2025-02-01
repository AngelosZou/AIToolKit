import re


def delete_think(content: str):
    """
    去除所有</think>以及之前的信息
    """
    return re.sub(r".*?</think>", "", content, flags=re.DOTALL)
