import importlib
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path

from agent import summarizer
from command.fetch import fetch_web_content
from core.cache import CatchInformation, SearchResult, GlobalFlag, Configure
from tool.parser import ToolParser
from util.fomatter import delete_think


class ToolExecutor:
    def __init__(self):
        self.cache = CatchInformation.get_instance()
        self.search_result = SearchResult.get_instance()
        self.user_output = []
        self.model_output = []
        self.should_terminate = False
        self.code_space = Path("./code_space") # AI使用的代码空间
        self.code_space.mkdir(exist_ok=True)  # 确保代码空间存在

    def process(self, tools):
        i = 0
        while i < len(tools):
            tool_type, content = tools[i]

            print(f"Processing tool {i+1}/{len(tools)}: {tool_type}")

            if tool_type == 'cache':
                self._handle_cache(content)
                i += 1

            elif tool_type == 'search':
                self._handle_search(content)
                i += 1
                self.should_terminate = True

            elif tool_type == 'fetch':
                # 检查后续是否有summary
                # has_summary = i+1 < len(tools) and tools[i+1][0] == 'summary'
                has_summary = any(t[0] == 'summary' for t in tools[i+1:])
                self._handle_fetch(content, has_summary)
                i += 1
                self.should_terminate = True

            elif tool_type == 'summary':
                self._handle_summary()
                i += 1
                self.should_terminate = True

            elif tool_type == 'write':
                filename, code = content
                self._handle_write(filename, code)
                i += 1

            elif tool_type == 'run':
                self._handle_run()
                i += 1
                self.should_terminate = True

            elif tool_type == 'test':
                self._handle_test()
                i += 1
                self.should_terminate = True

    def _handle_write(self, filename, code):
        try:
            # 安全验证文件名
            if '/' in filename or '\\' in filename:
                raise ValueError("文件名不能包含路径")

            file_path = self.code_space / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

            self.user_output.append(f"\n📝 已写入文件: {filename}")
            self.model_output.append(f"File written: {filename}")
        except Exception as e:
            self.user_output.append(f"\n⚠️ 写入失败: {str(e)}")
            self.model_output.append(f"Write failed: {str(e)}")

    def _handle_run(self):
        try:
            main_file = self.code_space / "main.py"
            if not main_file.exists():
                raise FileNotFoundError("main.py不存在")

            # 动态导入模块
            spec = importlib.util.spec_from_file_location("main_module", str(main_file))
            module = importlib.util.module_from_spec(spec)
            sys.modules["main_module"] = module

            # 重定向输出
            output = []
            original_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                spec.loader.exec_module(module)
                if hasattr(module, 'main'):
                    module.main()
                else:
                    raise AttributeError("main()函数不存在")  # <-- 需要捕获这个异常
            except AttributeError as e:  # 新增异常捕获
                raise AttributeError("main()函数不存在") from e
            finally:
                sys.stdout.seek(0)
                output = sys.stdout.read()
                sys.stdout = original_stdout

            self.user_output.append("\n🔄 运行结果:\n" + output)
            self.model_output.append(f"Run output:\n{output}")

        except Exception as e:
            error_msg = f"运行错误: {str(e)}"
            self.user_output.append("\n⚠️ " + error_msg)  # <-- 确保错误信息包含关键提示
            self.model_output.append(f"Run failed: {str(e)}")

    def _handle_test(self):
        try:
            test_file = self.code_space / "test.py"

            # 验证测试文件存在
            if not test_file.exists():
                raise FileNotFoundError("测试文件test.py不存在")

            # 使用绝对路径执行pytest
            result = subprocess.run(
                ["pytest", str(test_file.absolute())],
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=str(self.code_space.absolute())
            )

            try:
                # 使用多阶段解析策略
                failed_tests = []
                current_failure = {}
                error_phase = None  # 标记当前解析阶段：header/details

                # 定义更全面的正则表达式
                failure_header_pattern = re.compile(
                    r'^FAILED .+?::(test_\w+) ?- ?(.+?)(:|$)'
                )
                error_header_pattern = re.compile(
                    r'^ERROR .+?::(test_\w+) ?- ?(.+?)(:|$)'
                )
                assertion_pattern = re.compile(r'^>?\s*assert (.+)$')
                error_type_pattern = re.compile(r'^(E\s+)?(\w+):?\s*(.*)$')

                for line in result.stdout.split('\n'):
                    # 阶段1：匹配失败头部信息
                    if header_match := failure_header_pattern.match(line):
                        current_failure = {
                            'name': header_match.group(1),
                            'error_type': 'AssertionError',
                            'message': header_match.group(2).strip(),
                            'details': []
                        }
                        error_phase = 'details'
                        continue
                    elif error_match := error_header_pattern.match(line):
                        current_failure = {
                            'name': error_match.group(1),
                            'error_type': 'ExecutionError',
                            'message': error_match.group(2).strip(),
                            'details': []
                        }
                        error_phase = 'details'
                        continue

                    # 阶段2：收集错误详情
                    if current_failure:
                        # 捕获断言语句
                        if assertion_match := assertion_pattern.match(line):
                            current_failure['assertion'] = assertion_match.group(1)
                        # 捕获错误类型（非断言错误）
                        elif error_type_match := error_type_pattern.match(line):
                            current_failure['error_type'] = error_type_match.group(2)
                            current_failure['message'] = error_type_match.group(3)
                        # 结束一个错误块的收集
                        elif line.strip() == '' and error_phase == 'details':
                            failed_tests.append(current_failure)
                            current_failure = {}
                            error_phase = None
                        # 收集错误详细信息
                        elif error_phase == 'details':
                            current_failure['details'].append(line.strip())
            except Exception as e:
                self.user_output.append(f"\n⚠️ 测试结果解析错误：{str(e)}")

            # 构建结果输出
            if result.returncode == 0:
                self.user_output.append("\n✅ 所有测试通过")
                self.model_output.append("All tests passed")
            else:
                # 在构建报告部分修改为：
                try:
                    report = ["\n❌ 未通过测试："]
                    for idx, test in enumerate(failed_tests, 1):
                        entry = [
                            f"{idx}. 测试函数：{test.get('name', '未知函数')}",
                            f"   错误类型：{test.get('error_type', '未知错误')}",
                            f"   错误信息：{test.get('message', '无详细信息')}"
                        ]

                        # 添加断言信息（如果有）
                        if 'assertion' in test:
                            entry.append(f"   断言语句：{test['assertion']}")

                        # 添加错误详情（最多3行）
                        if test.get('details'):
                            entry.append("   错误详情：")
                            entry.extend([f"      {d}" for d in test['details'][:3]])

                        report.append("\n".join(entry))

                    self.user_output.append("\n".join(report))
                except Exception as e:
                    self.user_output.append(f"\n⚠️ 用户报告构建错误：{str(e)}\n已将完整测试结果提交AI")
                self.model_output.append(f"测试失败详情：{result.stdout}")
                GlobalFlag.get_instance().skip_user_input = True

        except Exception as e:
            error_msg = f"测试执行错误：{str(e)}"
            self.user_output.append(f"\n⚠️ {error_msg}")
            self.model_output.append(f"Test failed: {str(e)}")

    def _handle_cache(self, content):
        self.cache.info = content
        self.user_output.append("\n✅ 信息已缓存")

    def _handle_search(self, query):
        GlobalFlag.get_instance().skip_user_input = True
        try:
            try:
                from googleapiclient.discovery import build
            except ImportError:
                self.user_output.append("⚠️ 请安装google-api-python-client库以使用搜索功能")
                self.model_output.append("Search failed")
                return
            # 调用搜索API（复用已有SearchCommand逻辑）
            api_key = Configure.get_instance().google_api_key
            cse_id = Configure.get_instance().google_cse_id

            if not api_key or not cse_id:
                self.user_output.append(f"⚠️ 搜索失败: 未配置API密钥")
                self.model_output.append("搜索失败，用户没有配置API或CSE ID，不要再尝试搜索，知道用户再次要求。")
                return
            service = build("customsearch", "v1", developerKey=api_key)
            result = service.cse().list(q=query, cx=cse_id, num=5).execute()

            self.search_result.search_results = result.get('items', [])

            # 构建用户可见结果
            response = ["\n🔍 搜索结果："]
            for idx, item in enumerate(self.search_result.search_results, 1):
                response.append(f"{idx}. {item['title']}")

            self.user_output.append("\n".join(response))
            # 构建模型可见结果（含标题和URL）
            model_response = ["已经获取以下搜索结果（标题 + URL）："]  # 新增提示语
            for idx, item in enumerate(self.search_result.search_results, 1):
                model_response.append(f"{idx}. 标题：{item['title']}\n   URL：{item['link']}")  # 结构化格式
            model_response.append("请使用获取网页工具来获取具体内容。")  # 保留原有提示

            self.model_output.append("\n".join(model_response))  # 替换原有简单提示

        except Exception as e:
            self.user_output.append(f"⚠️ 搜索失败: {str(e)}")
            self.model_output.append(f"搜索遇到错误 {str(e)}\n根据错误提示，如果是你可以修复的问题，尝试修复，否则直到用户再次请求，不要使用搜索。")

    def _handle_fetch(self, url, has_summary):
        GlobalFlag.get_instance().skip_user_input = True
        try:
            # 复用现有fetch_web_content函数
            content = fetch_web_content(url)
            self.cache.info = content

            self.user_output.append(f"\n\n🌐 成功获取网页内容: {url}")
            self.model_output.append(f"Web content cached: {url}")

            if not has_summary:
                self.model_output.append(f"网页内容提取: {content}")

        except Exception as e:
            self.user_output.append(f"\n⚠️ 网页获取失败: {str(e)}\n")
            self.model_output.append("Fetch failed")

    def _handle_summary(self):
        GlobalFlag.get_instance().skip_user_input = True
        if not self.cache.info:
            self.user_output.append("⚠️ 没有可总结的缓存内容")
            return

        try:
            summary = summarizer.process(self.cache.info, send_to_cache=True)
            self.user_output.append("\n📝 总结已完成\n")
            self.model_output.append(f"Summary cached: {summary}")
        except Exception as e:
            self.user_output.append(f"⚠️ 总结失败: {str(e)}")


def process_model_output(content: str):
    content = delete_think(content)
    # 解析工具指令
    tools = ToolParser.parse(content)

    # 执行工具处理
    executor = ToolExecutor()
    executor.process(tools)

    # 构建返回结果
    return {
        'user_message': "\n".join(executor.user_output),
        'model_feedback': "\n".join(executor.model_output),
        'should_terminate': executor.should_terminate
    }