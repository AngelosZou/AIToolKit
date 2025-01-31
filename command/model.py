from typing import List, Tuple

import ollama

from .commands import registry, Command, CommandContext
from core.cache import Cache

@registry.register(
    path="/model/list",
    description="检查可用模型"
)
class ModelCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        return ollama.list, ""

@registry.register(
    path="/model/set",
    description="设置当前启用模型(重启生效)"
)
class ModelChangeCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "模型参数缺失", ""
        Cache.get_instance().active_model = args[0]
        return f"已修改为模型 {args[0]}", ""
