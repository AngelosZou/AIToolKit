from typing import List, Tuple

from core.cache import Configure, CatchInformation
from .commands import registry, Command, CommandContext


@registry.register(
    path="/cache",
    description="显示当前缓存内的信息"
)
class CacheCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if len (CatchInformation.get_instance().info) == 0:
            return "缓存为空", ""
        return CatchInformation.get_instance().info, ""
