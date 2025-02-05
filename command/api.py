from typing import List, Tuple

from core.cache import Configure
from .commands import registry, Command, CommandContext


@registry.register(
    path="/api/google",
    description="设置谷歌搜索使用的API"
)
class GoogleApiCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "请提供API", ""
        Configure.get_instance().google_api_key = args[0]
        return "已更新谷歌搜索API", ""

@registry.register(
    path="/api/google_cse",
    description="设置谷歌搜索使用的CSE ID"
)
class GoogleCSECommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "请提供CSE ID", ""
        Configure.get_instance().google_cse_id = args[0]
        return "已更新谷歌搜索CSE ID", ""

@registry.register(
    path="/api/openai",
    description="设置OpenAI模型使用API"
)
class OpenAIAPICommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "请提供API", ""
        Configure.get_instance().openai_api_key = args[0]
        return "已更新OpenAI模型API", ""

@registry.register(
    path="/api/siliconflow",
    description="设置SiliconFlow模型使用API"
)
class SiliconAPICommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "请提供API", ""
        Configure.get_instance().siliconflow_api_key = args[0]
        return "已更新SiliconFlow模型API", ""

@registry.register(
    path="/api/deepseek",
    description="设置DeepSeek模型使用API"
)
class DeepSeekAPICommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        if not args:
            return "请提供API", ""
        Configure.get_instance().deepseek_api_key = args[0]
        return "已更新DeepSeek模型API", ""