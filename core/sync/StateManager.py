import asyncio
import enum


class State(enum.Enum):
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    FINISH_INPUT = "FINISH_INPUT"
    PROCESSING = "PROCESSING"


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


class InitStateManager:
    """初始化状态管理器"""
    instance = None

    @staticmethod
    def get_or_create():
        if InitStateManager.instance is None:
            InitStateManager.instance = InitStateManager()
        InitStateManager.instance.state = InitStateManager.InitState.STARTING
        return InitStateManager.instance

    class InitState(enum.Enum):
        STARTING = "STARTING"
        LOADING_CONFIGURE = "LOADING_CONFIGURE"
        CHECKING_SOURCE = "CHECKING_SOURCE"
        LOADING_HISTORY = "LOADING_HISTORY"
        LOADING_REFERENCE = "LOADING_REFERENCE"
        LOADING_CODE = "LOADING_CODE"
        FINISH = "FINISH"

    def __init__(self):
        self.condition = asyncio.Condition()
        self.state = InitStateManager.InitState.STARTING

    async def set_state(self, new_state: InitState):
        async with self.condition:
            self.state = new_state
            print(f"状态变更: {new_state}")
            self.condition.notify_all()  # 唤醒所有等待的任务

    async def wait_for_state(self, expected_state: InitState):
        async with self.condition:
            await self.condition.wait_for(lambda: self.state == expected_state)
            print(f"状态 {expected_state} 达成")