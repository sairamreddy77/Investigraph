# backend/tests/test_llm.py
import asyncio
import importlib
from unittest.mock import Mock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_llm_singletons():
    llm_module = importlib.import_module("app.llm")
    llm_module._groq_client = None
    llm_module._groq_llm = None
    yield
    llm_module._groq_client = None
    llm_module._groq_llm = None


def test_groq_client_initializes(mock_settings):
    with patch("app.llm.Groq") as mock_groq:
        from app.llm import get_groq_client

        get_groq_client()

        mock_groq.assert_called_once_with(api_key="test_key")


def test_groq_client_generates_response(mock_settings):
    with patch("app.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated Cypher query"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        from app.llm import GroqClient

        client = GroqClient()
        result = client.chat_completion(
            system_prompt="You are a Cypher generator",
            user_prompt="Generate query",
            temperature=0,
        )

        assert result == "Generated Cypher query"
        mock_client.chat.completions.create.assert_called_once()


def test_groq_llm_invoke(mock_settings):
    with patch("app.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="test answer"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        from app.llm import GroqLLM

        llm = GroqLLM(model_name="llama-3.3-70b-versatile")
        result = llm.invoke("test prompt")

        assert result.content == "test answer"


def test_groq_llm_ainvoke(mock_settings):
    with patch("app.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="async answer"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        from app.llm import GroqLLM

        llm = GroqLLM()
        result = asyncio.run(llm.ainvoke("test prompt"))

        assert result.content == "async answer"


def test_groq_llm_singleton(mock_settings):
    with patch("app.llm.Groq") as mock_groq:
        from app.llm import get_groq_llm

        llm_one = get_groq_llm()
        llm_two = get_groq_llm()

        assert llm_one is llm_two
        mock_groq.assert_called_once()


def test_groq_llm_uses_model_params(mock_settings):
    with patch("app.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="parametrized answer"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        from app.llm import GroqLLM

        llm = GroqLLM(
            model_name="llama-3.3-70b-versatile",
            model_params={"temperature": 0.4, "max_tokens": 123},
        )
        llm.invoke("test prompt")

        mock_client.chat.completions.create.assert_called_once_with(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "test prompt"}],
            temperature=0.4,
            max_tokens=123,
        )
