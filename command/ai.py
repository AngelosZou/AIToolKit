from typing import List, Tuple

from core.cache import Configure
from core.source.sources import SourceRegistry
from .commands import registry, Command, CommandContext


@registry.register(
    path="/ai/list",
    description="检查预设的可选AI加载源"
)
class ModelCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        return SourceRegistry.sources.keys().__str__(), ""

@registry.register(
    path="/ai/set",
    description="设置启用的AI加载源",
    usage="/ai set <AI名>"
)
class ModelChangeCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "参数缺失", ""
        if args[0] not in SourceRegistry.sources.keys():
            return "源不存在，使用/ai list 检查", ""
        Configure.get_instance().active_ai = args[0]
        return f"已修改AI源为 {args[0]}", ""
