import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import io
import shutil
from pathlib import Path

from tool.excutor import ToolExecutor
from tool.parser import ToolParser


class TestToolExecutorRealFiles(unittest.TestCase):
    def setUp(self):
        # 创建独立的测试目录
        self.test_dir = Path("./test_code_space")
        self.test_dir.mkdir(exist_ok=True)

        # 初始化执行器并设置测试目录
        self.executor = ToolExecutor()
        self.executor.code_space = self.test_dir
        self.executor.user_output = []
        self.executor.model_output = []

    def tearDown(self):
        # 清理测试目录
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    # --------------------------
    # _handle_write 测试用例
    # --------------------------
    def test_handle_write_success(self):
        filename = "test.py"
        code = "print('hello')"

        with patch("builtins.open", mock_open()) as mocked_file:
            self.executor._handle_write(filename, code)

            # 验证文件操作
            mocked_file.assert_called_with(self.test_dir/filename, 'w', encoding='utf-8')
            mocked_file().write.assert_called_once_with(code)

        # 验证输出
        self.assertIn(f"📝 已写入文件: {filename}", self.executor.user_output[0])
        self.assertIn(f"File written: {filename}", self.executor.model_output)

    def test_handle_write_invalid_filename(self):
        self.executor._handle_write("../invalid.py", "code")

        self.assertIn("文件名不能包含路径", self.executor.user_output[0])
        self.assertIn("Write failed", self.executor.model_output[0])





    # --------------------------
    # _handle_test 测试用例
    # --------------------------
    def test_handle_test_success(self):
        """测试全部通过的情况"""
        # 创建测试文件
        test_code = """
def test_addition():
    assert 1+1 == 2

def test_subtraction():
    assert 5-3 == 2
        """
        (self.test_dir / "test.py").write_text(test_code, encoding='utf-8')

        self.executor._handle_test()

        self.assertIn("✅ 所有测试通过", self.executor.user_output[0])


    # --------------------------
    # test_handle_run_file_not_found
    # --------------------------
    def test_handle_run_file_not_found(self):
        # 确保main.py不存在
        if (self.test_dir / "main.py").exists():
            (self.test_dir / "main.py").unlink()

        self.executor._handle_run()

        # 验证错误信息
        self.assertIn("main.py不存在", self.executor.user_output[0])
        self.assertIn("Run failed", self.executor.model_output[0])

    # --------------------------
    # test_handle_run_missing_main
    # --------------------------
    def test_handle_run_missing_main(self):
        # 创建没有main函数的文件
        code = """
def wrong_function():
    print("hello")
        """
        (self.test_dir / "main.py").write_text(code)

        self.executor._handle_run()

        # 验证错误信息
        self.assertIn("main()函数不存在", self.executor.user_output[0])
        self.assertIn("Run failed", self.executor.model_output[0])

    # --------------------------
    # test_handle_run_success
    # --------------------------
    def test_handle_run_success(self):
        # 创建正确的main.py
        code = """
def main():
    print("测试成功")
    print("输出捕获正常")
        """
        (self.test_dir / "main.py").write_text(code, encoding='utf-8')

        # 执行并捕获输出
        self.executor._handle_run()

        # 验证输出
        output = "\n".join(self.executor.user_output)
        self.assertIn("🔄 运行结果:", output)
        self.assertIn("测试成功", output)
        self.assertIn("输出捕获正常", output)

    # --------------------------
    # test_handle_test_failure
    # --------------------------
    def test_handle_test_failure(self):
        """测试存在失败用例的情况"""
        # 创建包含失败用例的测试文件
        test_code = """
def test_correct():
    assert 10 > 5

def test_failure():
    assert 2 * 3 == 7  # 失败用例
    
def test_another_failure():
    assert "hello" == "world"  # 失败用例
        """
        (self.test_dir / "test.py").write_text(test_code, encoding='utf-8')

        self.executor._handle_test()

        output = "\n".join(self.executor.model_output)
        self.assertIn("test_failure", output)
        self.assertIn('assert 2 * 3 == 7', output)
        self.assertIn("test_another_failure", output)
        self.assertIn('assert "hello" == "world"', output)

    def test_handle_test_no_file(self):
        """测试文件不存在的情况"""
        self.executor._handle_test()
        self.assertIn("test.py不存在", self.executor.user_output[0])

    def test_multiple_write_operations(self):
        """验证连续写入多个文件"""
        test_content = """
        <write path="main.py">print("hello")</write>
        <write path="test.py">assert True</write>
        """

        tools = ToolParser.parse(test_content)
        self.assertEqual(len(tools), 2)  # 确认解析到两个工具

        self.executor.process(tools)

        # 验证文件存在
        self.assertTrue((self.test_dir / "main.py").exists())
        self.assertTrue((self.test_dir / "test.py").exists())

        # 验证文件内容
        with open(self.test_dir / "main.py", 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), 'print("hello")')
        with open(self.test_dir / "test.py", 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), 'assert True')

if __name__ == '__main__':
    unittest.main()