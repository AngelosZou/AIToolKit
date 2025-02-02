from typing import List, Tuple

from core.cache import Configure
from .commands import registry, Command, CommandContext


@registry.register(
    path="/exit",
    description="退出程序"
)
class ExitCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        context['running'] = False
        Configure.get_instance().save()
        return "正在退出程序...", ""