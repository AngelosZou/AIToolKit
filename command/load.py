from typing import List, Tuple

from core.communicate import communicate
from core.history import change_main_history, History
from .commands import registry, Command, CommandContext


@registry.register(
    path="/load",
    description="加载历史数据，覆盖当前对话历史"
)
class LoadCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        change_main_history(History.load(args[0]))
        return "使用历史数据覆盖当前对话", ""

