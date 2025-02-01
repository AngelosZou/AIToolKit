import util.fomatter as formatter

def test_formatter():
    assert formatter.delete_think("<think> abd\n cdcd </think> 123")  == " 123"