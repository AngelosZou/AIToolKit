import json
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MessageRole(Enum):
    USER = "user",
    SYSTEM = "system",
    ASSISTANT = "assistant"

    @staticmethod
    def from_role(role: str):
        return {
            "user": MessageRole.USER,
            "system": MessageRole.SYSTEM,
            "assistant": MessageRole.ASSISTANT
        }[role]

@dataclass
class Message:
    # 一条消息
    role: MessageRole
    for_model: str
    for_user: str
    think: str

    def __dict__(self):
        return {
            "role": self.role.value if isinstance(self.role.value, str) else self.role.value[0],
            "for_model": self.for_model,
            "for_user": self.for_user,
            "think": self.think
        }

    @staticmethod
    def from_dict(data: dict):
        return Message(MessageRole.from_role(data["role"]), data["for_model"], data["for_user"], data["think"])

class History:
    MAIN_HISTORY = None

    def __init__(self, history = None, name = None):
        if history is None:
            self.history: list[Message] = []
        if name is None:
            self.name = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    def to_message(self)->list[dict]:
        """转换成发送给模型的消息"""
        message = []
        for msg in self.history:
            message.append({
                "role": msg.role.value if isinstance(msg.role.value, str) else msg.role.value[0],
                "content": msg.for_model
            })
        return message

    def to_user(self)->list[dict]:
        """转换成发送给用户的消息"""
        message = []
        for msg in self.history:
            message.append({
                "role": msg.role.value if isinstance(msg.role.value, str) else msg.role.value[0],
                "content": msg.for_user
            })
        return message

    def add_message(self, role: MessageRole, for_model: str, for_user: str, think: str = ""):
        """添加一条消息"""
        self.history.append(Message(role, for_model, for_user, think))

    def save(self):
        """保存对话记录"""
        if self.history is None:
            return

        json_file = Path(f"./history/{self.name}.json")
        if not json_file.parent.exists():
            json_file.parent.mkdir(parents=True)
        to_save = [msg.__dict__() for msg in self.history]
        with json_file.open('w', encoding='utf-8') as f:
            f.write(json.dumps(to_save, ensure_ascii=False, indent=2))

    @staticmethod
    def get_or_create():
        """创建一个新的对话记录"""
        if History.MAIN_HISTORY is not None:
            return History.MAIN_HISTORY
        History.MAIN_HISTORY = History()
        return History.MAIN_HISTORY

    @staticmethod
    def load(name: str):
        """加载对话记录"""
        json_file = Path(f"./history/{name}.json")
        if not json_file.exists():
            print("文件不存在")
            History.MAIN_HISTORY = History()
            return History.MAIN_HISTORY
        with json_file.open('r', encoding='utf-8') as f:
            content = json.loads(f.read())
        history = History()
        for msg in content:
            history.add_message(MessageRole.from_role(msg["role"]), msg["for_model"], msg["for_user"], msg["think"])
        History.MAIN_HISTORY = history
        return history

def change_main_history(history: History):
    """更改主要历史记录"""
    History.MAIN_HISTORY.save()
    History.MAIN_HISTORY = history

