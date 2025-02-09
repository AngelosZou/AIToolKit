from command.file import read_file_content
from core.SurrogateIO import try_create_message, sio_print
from core.cache import GlobalFlag
from core.communicate import communicate
from core.history import History, MessageRole
from core.sync.StateManager import StateManager, State
from tool.base_tool import ToolProcessor
from tui.message import MsgType


async def process(description: str, ref=False):
    """
    使用description作为描述，使用一个子系统反复调试代码空间的代码，直到测试全部通过
    :param description:
    :param ref: 是否为AI加载参考文件
    :return:
    """

    from main import reload_code, reload_file

    prompt = read_file_content("./resource/prompt/agent/summarizer.txt")

    write = read_file_content("./resource/prompt/tool/write.txt")
    edit = read_file_content("./resource/prompt/tool/edit.txt")
    test = read_file_content("./resource/prompt/tool/test.txt")

    try_create_message(MsgType.SYSTEM)
    sio_print("调试器启动")

    test_res = ""

    count = 0
    while True:
        count += 1
        history = History()
        history.add_message(MessageRole.SYSTEM, prompt + write + edit + test, "")
        history.add_message(MessageRole.USER, "你需要完成的任务是："  + description, "")
        if len(test_res) != 0:
            history.add_message(MessageRole.SYSTEM, "当前代码的测试结果：" + test_res, "")
        reload_code(history, info=False)
        if ref:
            reload_file(history, info=False)

        try_create_message(MsgType.SYSTEM)
        sio_print(f"开始调试器轮次：{count}")
        think, model = await communicate(history.to_message())

        tool_processor = ToolProcessor()
        res = tool_processor.process(model + "\n <test>")
        if len(res["user_message"]) != 0:
            try_create_message(MsgType.SYSTEM)
            sio_print(res["user_message"])

        test_res = res['model_feedback']

        # 如果测试通过
        if "所有测试通过" in res["user_message"]:
            try_create_message(MsgType.SYSTEM)
            sio_print("所有测试通过，调试器结束")
            GlobalFlag.get_instance().occupy_user_input = False
            StateManager.get_or_create().set_state(State.WAITING_FOR_INPUT)
            return test_res



