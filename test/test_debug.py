from tool.base_tool import ToolProcessor
from tool.debugger import DebuggerTool


def test_d():
    code = """
<debugger ref=False>
在main.py中，add函数的实现存在逻辑错误。正确应该返回a与b的和而不是差。当前测试用例全部失败，需要通过修正代码让所有测试通过。
</debugger>
    """

    processor = ToolProcessor()

    processor.process(code)