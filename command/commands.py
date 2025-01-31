from typing import Dict, List, Tuple, Optional

# ----------------------
# 命令模式基础架构
# ----------------------

class CommandContext(dict):
    """命令执行上下文"""
    pass

class Command:
    """命令基类"""
    def __init__(self, name: str, description: str = "", parent: Optional['Command'] = None, usage=None):
        self.name = name
        self.description = description
        self.parent = parent
        self.subcommands: Dict[str, 'Command'] = {}
        self.usage = usage

    def add_subcommand(self, cmd: 'Command'):
        """添加子命令"""
        cmd.parent = self
        self.subcommands[cmd.name] = cmd
        return self

    def get_full_command(self) -> str:
        """获取完整命令路径"""
        path = []
        current = self
        while current and current.name != 'root':
            path.append(current.name)
            current = current.parent
        return '/' + '/'.join(reversed(path))

    def handle(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        """处理命令链"""
        if args and args[0] in self.subcommands:
            return self.subcommands[args[0]].handle(args[1:], context)
        return self.execute(args, context)

    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        """需要子类实现的具体逻辑"""
        raise NotImplementedError()

    def get_help(self, verbose: bool = False) -> str:
        """生成帮助信息"""
        help_text = [
            f"命令: {self.get_full_command()}",
            f"描述: {self.description}",
        ]
        if self.usage is not None:
            help_text.append(f"用法: {self.usage}")

        if self.subcommands:
            help_text.append("\n可用子命令:")
            help_text += [f"  {cmd.name.ljust(15)} {cmd.description}" for cmd in self.subcommands.values()]

        return '\n'.join(help_text)

class CommandRoot(Command):
    """根命令"""
    def __init__(self):
        super().__init__(name='root', description="根命令")

    def execute(self, args: List[str], context: CommandContext) -> Tuple[str, str]:
        return "请输入有效命令（使用 /help 查看可用命令）", ""

# ----------------------
# 命令注册装饰器
# ----------------------

class CommandRegistry:
    def __init__(self):
        self.root = CommandRoot()
        self._commands = {}

    def register(self, path: str, **kwargs):
        """命令注册装饰器"""
        def decorator(cls):
            parts = path.strip('/').split('/')
            current = self.root

            # 构建命令层级
            for idx, part in enumerate(parts):
                if part not in current.subcommands:
                    if idx == len(parts)-1:  # 最后一级命令
                        cmd = cls(name=part, **kwargs)
                        current.add_subcommand(cmd)
                    else:  # 中间路径
                        temp_cmd = Command(name=part, description=f"{part}命令组")
                        current.add_subcommand(temp_cmd)
                        current = temp_cmd
                else:
                    current = current.subcommands[part]
            return cls
        return decorator

registry = CommandRegistry()


# ----------------------
# 重构后的命令处理器
# ----------------------

class CommandHandler:
    """重构后的命令处理器"""
    def __init__(self):
        self.running = True
        self.registry = registry

    def handle_command(self, user_input: str) -> Tuple[str, str]:
        """处理用户输入"""
        if not user_input.startswith('/'):
            return f"无效命令格式，必须以/开头", ""

        # 解析命令路径
        parts = user_input[1:].strip().split()
        if not parts:
            return "请输入有效命令", ""

        context = CommandContext(running=self.running)
        try:
            # 执行命令链
            result, content = self.registry.root.handle(parts, context)
            self.running = context.get('running', self.running)
            return result, content
        except Exception as e:
            return f"命令执行错误: {str(e)}", ""


registry.register(path="/fetch",
                  description="网页内容获取",
                  usage="/fetch <URL>")