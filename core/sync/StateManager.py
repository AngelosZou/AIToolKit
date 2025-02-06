import asyncio
import enum


class State(enum.Enum):
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    FINISH_INPUT = "FINISH_INPUT"


class StateManager:
    instance = None

    @staticmethod
    def get_or_create():
        if StateManager.instance is None:
            StateManager.instance = StateManager()
        return StateManager.instance

    def __init__(self):
        self.condition = asyncio.Condition()
        self.state: State = State.WAITING_FOR_INPUT  # 初始状态

    async def set_state(self, new_state: State):
        async with self.condition:
            self.state = new_state
            print(f"状态变更: {new_state}")
            self.condition.notify_all()  # 唤醒所有等待的任务

    async def wait_for_state(self, expected_state: State):
        async with self.condition:
            await self.condition.wait_for(lambda: self.state == expected_state)
            print(f"状态 {expected_state} 达成")