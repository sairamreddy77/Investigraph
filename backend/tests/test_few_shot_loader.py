import pytest
from unittest.mock import patch, mock_open


def test_few_shot_loader_loads_examples():
    """Test loader loads examples from YAML"""
    yaml_content = """
examples:
  - question: "How many crimes?"
    cypher: "MATCH (c:Crime) RETURN count(c)"
  - question: "List people"
    cypher: "MATCH (p:Person) RETURN p"
"""
    with patch('builtins.open', mock_open(read_data=yaml_content)):
        from core.few_shot_loader import FewShotLoader

        loader = FewShotLoader()
        examples = loader.load_examples()

        assert len(examples) == 2
        assert examples[0]["question"] == "How many crimes?"
        assert "MATCH (c:Crime)" in examples[0]["cypher"]


def test_few_shot_loader_formats_for_prompt():
    """Test loader formats examples for LLM prompt"""
    yaml_content = """
examples:
  - question: "Q1"
    cypher: "QUERY1"
"""
    with patch('builtins.open', mock_open(read_data=yaml_content)):
        from core.few_shot_loader import FewShotLoader

        loader = FewShotLoader()
        formatted = loader.format_for_prompt()

        assert "Q1" in formatted
        assert "QUERY1" in formatted
