from typing import List, Tuple

import ollama

from .commands import registry, Command, CommandContext
from core.cache import Configure

@registry.register(
    path="/model/ollama/list",
    description="检查本地可用的ollama模型"
)
class ModelCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        return ollama.list, ""

@registry.register(
    path="/model/set",
    description="为当前启用的AI源选择启用的模型"
)
class ModelChangeCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "模型参数缺失", ""
        configure = Configure.get_instance()
        ai_source = configure.active_ai
        if ai_source is None:
            return "未选择AI加载器来源，使用/ai set 设置", ""
        configure.active_model[ai_source] = args[0]
        return f"已修改 {ai_source} 的模型为 {args[0]}", ""
