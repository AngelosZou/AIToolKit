import csv
import json
from pathlib import Path


class CommandHandler:
    """指令处理类"""
    def __init__(self):
        self.running = True

    def handle_command(self, user_input: str) -> [str,str]:
        """处理用户指令"""
        if user_input.startswith('/exit'):
            self.running = False
            return "正在退出程序...", ""
        elif user_input.startswith('/file'):
            return self.process_file(user_input)
        else:
            return f"未知指令: {user_input.split()[0]}", ""

    @staticmethod
    def process_file(command: str) -> [str, str]:
        """处理文件读取指令"""
        try:
            _, filepath = command.split(maxsplit=1)
            return f"读取到了本地文件{filepath}", f"[解析的本地文件{filepath}]: {read_file_content(filepath.strip())}"
        except ValueError:
            return "文件路径参数缺失", ""
        except Exception as e:
            return f"文件处理失败: {str(e)}", ""


def read_file_content(filepath: str) -> str:
    """读取并解析多种文件格式"""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    if path.suffix == '.txt':
        return path.read_text(encoding='utf-8')
    elif path.suffix == '.csv':
        return csv_to_text(path)
    elif path.suffix == '.json':
        return json_to_text(path)
    elif path.suffix == '.py':
        return f"Python代码文件内容:\n```python\n{path.read_text(encoding='utf-8')}\n```"
    else:
        raise ValueError(f"不支持的文件格式: {path.suffix}")

def csv_to_text(filepath: Path) -> str:
    """将CSV转换为自然语言描述"""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        output = [f"CSV文件包含 {len(reader.fieldnames)} 列: {', '.join(reader.fieldnames)}"]
        for i, row in enumerate(reader, 1):
            output.append(f"行 {i}: {', '.join(f'{k}={v}' for k,v in row.items())}")
    return "\n".join(output)

def json_to_text(filepath: Path) -> str:
    """将JSON转换为自然语言描述"""
    data = json.loads(filepath.read_text(encoding='utf-8'))
    return f"JSON数据结构摘要:\n{json.dumps(data, indent=2, ensure_ascii=False)}"

