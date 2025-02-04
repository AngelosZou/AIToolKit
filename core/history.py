import json
import time
from pathlib import Path


def save_history(timestamp: str, message: list[dict]):
    """保存对话记录"""
    # 修改timestamp中的空格为下划线
    timestamp = timestamp.replace(":", "-")
    json_file = Path(f"./history/{timestamp}.json")
    if not json_file.parent.exists():
        json_file.parent.mkdir(parents=True)
    with json_file.open('w', encoding='utf-8') as f:
        f.write(json.dumps(message, ensure_ascii=False, indent=2))

def load_history(timestamp: str) -> list[dict]:
    """加载对话记录"""
    timestamp = timestamp.replace(":", "-")
    json_file = Path(f"./history/{timestamp}.json")
    if not json_file.exists():
        return []
    with json_file.open('r', encoding='utf-8') as f:
        content = json.loads(f.read())
    return content


