from typing import List, Tuple

from .commands import registry, Command, CommandContext

@registry.register(
    path="/help",
    description="帮助系统",
    usage="/help [命令路径]"
)
class HelpCommand(Command):
    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        current = registry.root
        breadcrumbs = []

        # 定位到目标命令
        for part in args:
            if part in current.subcommands:
                current = current.subcommands[part]
                breadcrumbs.append(part)
            else:
                return f"未找到命令: {'/'.join(breadcrumbs + [part])}", ""

        # 生成帮助信息
        help_text = [
            current.get_help(verbose=True),
            # "\n参数说明:",
            # "<必选参数> [可选参数]"
        ]
        return '\n'.join(help_text), ""