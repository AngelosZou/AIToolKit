from tool.code import EditCommand


def test_parser():
    code = """
<insert path="main.py" line=3>
    print("Test insertion line 1")
    print("Test insertion line 2")
</insert>
    """
    result = EditCommand.parse(code)