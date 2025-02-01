from typing import List, Tuple

from .commands import registry, Command, CommandContext
from core.cache import CatchInformation

@registry.register(
    path="/submit",
    description="将缓存内的信息提交给主AI",
)
class SubmitCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        info = CatchInformation.get_instance().info
        CatchInformation.get_instance().info = ""
        return "已将缓存的信息提交给AI", info