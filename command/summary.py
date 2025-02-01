from typing import List, Tuple

from .commands import registry, Command, CommandContext
from agent import summarizer
from core.cache import CatchInformation

@registry.register(
    path="/summary",
    description="使用代理AI对捕捉到的信息进行总结",
)
class SummaryCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        info = CatchInformation.get_instance().info
        summarizer.process(info, send_to_cache=True)
        return "", ""