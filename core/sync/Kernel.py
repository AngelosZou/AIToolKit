import asyncio

import main


class MainKernel:
    # 管理主进程
    MAIN_INSTANCE = None

    @staticmethod
    def start_core():
        # 启动核心
        task = asyncio.create_task(main.main())
        MainKernel.MAIN_INSTANCE = task

    @staticmethod
    def end_core():
        # 关闭核心
        MainKernel.MAIN_INSTANCE.cancel()

    @staticmethod
    def restart_kernel():
        # 重启核心
        MainKernel.end_core()
        MainKernel.start_core()
