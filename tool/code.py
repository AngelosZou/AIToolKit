import importlib
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import List, Any, Tuple

from core.Project import Project
from core.cache import GlobalFlag
from tool.base_tool import ToolRegistry, BaseTool

@ToolRegistry.register('write')
class WriteCommand(BaseTool):

    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        tools = []
        # 解析代码编写工具
        write_pattern = re.compile(
            r'<write\s+path="([^"]+)"[^>]*>\n?(.*?)\n?</write>',
            re.DOTALL  # 允许跨行匹配
        )

        # 解析所有write标签
        for match in write_pattern.finditer(content):
            filename = match.group(1).strip()
            code = match.group(2).strip()
            tools.append(('write', (filename, code)))

        return tools




    def execute(self, user_output, model_output, args):
        try:
            self.filename, self.code = args
            if '/' in self.filename or '\\' in self.filename:
                raise ValueError("文件名不能包含路径")

            file_path = code_space() / self.filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.code)

            user_output.append(f"\n📝 已写入文件: {self.filename}")
            model_output.append(f"File written: {self.filename}")
        except Exception as e:
            user_output.append(f"\n⚠️ 写入失败: {str(e)}")
            model_output.append(f"Write failed: {str(e)}")


@ToolRegistry.register('run')
class RunCommand(BaseTool):
    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        tools = []
        if re.search(r'<run>', content):
            tools.append(('run', ''))
        return tools

    def execute(self, user_output, model_output, args):
        try:
            main_file = code_space() / "main.py"
            if not main_file.exists():
                raise FileNotFoundError("main.py不存在")

            spec = importlib.util.spec_from_file_location("main_module", str(main_file))
            module = importlib.util.module_from_spec(spec)
            sys.modules["main_module"] = module

            output = []
            original_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                spec.loader.exec_module(module)
                if hasattr(module, 'main'):
                    module.main()
                else:
                    raise AttributeError("main()函数不存在")
            finally:
                sys.stdout.seek(0)
                output = sys.stdout.read()
                sys.stdout = original_stdout

            user_output.append("\n🔄 运行结果:\n" + output)
            model_output.append(f"Run output:\n{output}")

        except Exception as e:
            error_msg = f"运行错误: {str(e)}"
            user_output.append("\n⚠️ " + error_msg)
            model_output.append(f"Run failed: {str(e)}")

@ToolRegistry.register('test')
class TestCommand(BaseTool):
    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        tools = []
        # 解析代码测试工具
        if re.search(r'<test>', content):
            tools.append(('test', ''))
        return tools

    def execute(self, user_output, model_output, args):
        try:
            test_file = code_space() / "test.py"

            # 验证测试文件存在
            if not test_file.exists():
                raise FileNotFoundError("测试文件test.py不存在")

            # 使用绝对路径执行pytest
            result = subprocess.run(
                ["pytest", str(test_file.absolute())],
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=str(code_space().absolute())
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
                user_output.append(f"\n⚠️ 测试结果解析错误：{str(e)}")

            # 构建结果输出
            if result.returncode == 0:
                user_output.append("\n✅ 所有测试通过")
                model_output.append("All tests passed")
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

                    user_output.append("\n".join(report))
                except Exception as e:
                    user_output.append(f"\n⚠️ 用户报告构建错误：{str(e)}\n已将完整测试结果提交AI")
                model_output.append(f"测试失败详情：{result.stdout}")
                GlobalFlag.get_instance().skip_user_input = True

        except Exception as e:
            error_msg = f"测试执行错误：{str(e)}"
            user_output.append(f"\n⚠️ {error_msg}")
            model_output.append(f"Test failed: {str(e)}")


@ToolRegistry.register('edit')
class EditCommand(BaseTool):

    @classmethod
    def parse(cls, content: str) -> List[Tuple[str, Any]]:
        """
        从给定的字符串中解析所有插入和删除的修改指令，并整合到一个工具中返回。

        指令格式：
          <insert path="文件路径" line=行号>
              插入的代码
          </insert>

          <delete path="文件路径" line=(起始行,结束行)>

        返回一个列表，其中包含一个元组，格式为:
            ("modify", { 文件路径: {"insert": [(行号, 代码), ...],
                                      "delete": [(起始行, 结束行), ...] },
                          ... })
        """
        modifications = {}

        # 解析insert标签：允许标签中有多行内容
        insert_pattern = re.compile(
            r'<insert\s+path="([^"]+)"\s+line=([0-9]+)\s*>\n?([\s\S]*?)\s*</insert>',
            re.DOTALL
        )

        # 解析delete标签：删除标签只包含属性，无内部内容
        delete_pattern = re.compile(
            r'<delete\s+path="([^"]+)"\s+line=\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*>'
        )


        # 处理所有insert指令
        for m in insert_pattern.finditer(content):
            file_path = m.group(1).strip()
            line_num = int(m.group(2))
            code = m.group(3)
            if file_path not in modifications:
                modifications[file_path] = {"insert": [], "delete": []}
            modifications[file_path]["insert"].append((line_num, code))

        # 处理所有delete指令
        for m in delete_pattern.finditer(content):
            file_path = m.group(1).strip()
            start_line = int(m.group(2))
            end_line = int(m.group(3))
            if file_path not in modifications:
                modifications[file_path] = {"insert": [], "delete": []}
            modifications[file_path]["delete"].append((start_line, end_line))

        return [("edit", (file_path, modifications[file_path])) for file_path in modifications]

    def execute(self, user_output, model_output, args):
        try:
            filename, modifications = args
            filename: str
            modifications: dict[str, list[tuple[int, int|str]]]



            if '/' in filename or '\\' in filename:
                raise ValueError("文件名不能包含路径")

            file_path = code_space() / filename

            if not file_path.exists() or file_path.suffix != ".py":
                raise ValueError("无效的Python文件路径")

            self.modify_py_file(file_path, modifications)

            user_output.append(f"\n 已修改文件: {filename}")
            model_output.append(f"File written: {filename}")
        except Exception as e:
            user_output.append(f"\n⚠ 写入失败: {str(e)}")
            model_output.append(f"Write failed: {str(e)}")

    @staticmethod
    def modify_py_file(file_path: Path, modifications: dict[str, list[tuple[int, int|str]]]):
        """
        Modify a Python file by inserting or removing lines at specific line numbers.

        :param file_path: Path object pointing to the .py file.
        :param modifications: A list of tuples where the first element is the line number,
                              and the second element is the new content (None to remove the line).
        """
        if not file_path.exists() or not file_path.suffix == ".py":
            raise ValueError("Invalid Python file path")

        with file_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        insertion = modifications.get("insert", [])
        deletion = modifications.get("delete", [])

        # 统计所有删除的行号
        delete_lines = set()
        for start, end in deletion:
            delete_lines.update(range(start, end + 1))

        insert_dict = {line_num: code for line_num, code in insertion}


        new_lines = []
        for i, line in enumerate(lines, start=1):
            if i in insert_dict:
                new_lines.append(insert_dict[i] + "\n")
            if i in delete_lines:
                continue
            new_lines.append(line)

        # 处理末尾
        if len(lines)+1 in insert_dict:
            new_lines.append("\n" + insert_dict[len(lines)+1] + "\n")


        with file_path.open("w", encoding="utf-8") as f:
            f.writelines(new_lines)



def code_space():
    return Project.instance.root_path / "code_space"