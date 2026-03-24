# backend/tests/test_llm.py
import importlib
import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def reset_llm_singleton():
    llm_module = importlib.import_module("app.llm")
    llm_module._groq_client = None
    yield
    llm_module._groq_client = None

def test_groq_client_initializes(mock_settings):
    """Test Groq client initializes with API key"""
    with patch('app.llm.Groq') as mock_groq:
        from app.llm import get_groq_client

        client = get_groq_client()

        mock_groq.assert_called_once_with(api_key="test_key")


def test_groq_client_generates_response(mock_settings):
    """Test Groq client generates LLM response"""
    with patch('app.llm.Groq') as mock_groq:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated Cypher query"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        from app.llm import generate_completion

        result = generate_completion(
            system_prompt="You are a Cypher generator",
            user_prompt="Generate query",
            temperature=0
        )

        assert result == "Generated Cypher query"
        mock_client.chat.completions.create.assert_called_once()
