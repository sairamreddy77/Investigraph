# backend/tests/test_cypher_generator.py
import pytest
from unittest.mock import Mock, patch


def test_cypher_generator_builds_prompt(mock_settings):
    """Test generator builds complete prompt with schema and examples"""
    with patch('core.cypher_generator.get_groq_client'):
        with patch('core.cypher_generator.get_schema_introspector') as mock_schema:
            with patch('core.cypher_generator.get_few_shot_loader') as mock_loader:
                mock_schema.return_value.introspect.return_value = "NODES: Person, Crime"
                mock_loader.return_value.format_for_prompt.return_value = "Example 1: ..."

                from core.cypher_generator import CypherGenerator

                generator = CypherGenerator()
                prompt = generator._build_system_prompt("")

                assert "NODES: Person, Crime" in prompt
                assert "Example 1: ..." in prompt
                assert "RULES" in prompt


def test_cypher_generator_generates_cypher(mock_settings):
    """Test generator calls LLM and returns Cypher"""
    with patch('core.cypher_generator.get_groq_client') as mock_groq:
        with patch('core.cypher_generator.get_schema_introspector') as mock_schema:
            with patch('core.cypher_generator.get_few_shot_loader') as mock_loader:
                mock_schema.return_value.introspect.return_value = "NODES: Crime"
                mock_loader.return_value.format_for_prompt.return_value = "Examples"

                mock_client = Mock()
                mock_client.chat_completion.return_value = "MATCH (c:Crime) RETURN count(c)"
                mock_groq.return_value = mock_client

                from core.cypher_generator import CypherGenerator

                generator = CypherGenerator()
                cypher = generator.generate("How many crimes?")

                assert "MATCH (c:Crime)" in cypher
                assert "RETURN count(c)" in cypher
                mock_client.chat_completion.assert_called_once()


def test_cypher_generator_includes_error_context_on_retry(mock_settings):
    """Test generator includes error context when retrying"""
    with patch('core.cypher_generator.get_groq_client') as mock_groq:
        with patch('core.cypher_generator.get_schema_introspector') as mock_schema:
            with patch('core.cypher_generator.get_few_shot_loader') as mock_loader:
                mock_schema.return_value.introspect.return_value = "NODES: Crime"
                mock_loader.return_value.format_for_prompt.return_value = "Examples"
                mock_client = Mock()
                mock_client.chat_completion.return_value = "MATCH (c:Crime) RETURN count(c)"
                mock_groq.return_value = mock_client

                from core.cypher_generator import CypherGenerator

                generator = CypherGenerator()
                error_context = "Previous query failed with: Invalid syntax"
                generator.generate("How many crimes?", error_context=error_context)

                call_args = mock_client.chat_completion.call_args
                system_prompt = call_args[0][0]

                assert "Invalid syntax" in system_prompt
