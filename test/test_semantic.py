from tool.semantic import SearchTool, RecommendTool


def test_s2_search():
    tool = SearchTool()
    user_output = []
    model_output = []
    query = "natural language processing"
    limit = 5
    tool.execute(user_output, model_output, (query, limit))
    
    assert len(user_output) > 0, "No output received from s2_search."
    assert "找到" in user_output[0], "Search results not found in the output."
    assert len(model_output) > 0, "No model output received from s2_search."

def test_s2_recommend():
    tool = RecommendTool()
    user_output = []
    model_output = []
    # Replace with a valid paper_id from a previous search
    paper_id = "649def34f8be52c8b66281af98ae884c09aef38b"
    limit = 5
    tool.execute(user_output, model_output, (paper_id, limit))
    
    assert len(user_output) > 0, "No output received from s2_recommend."
    assert f"基于论文 {paper_id}" in user_output[0], "Recommendation header not found in the output."
    assert len(model_output) > 0, "No model output received from s2_recommend."