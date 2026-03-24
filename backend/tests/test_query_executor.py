# backend/tests/test_query_executor.py
import pytest
from unittest.mock import Mock, patch
from neo4j.exceptions import CypherSyntaxError


def test_query_executor_executes_successful_query(mock_settings, mock_neo4j_driver):
    """Test executor runs query and returns results"""
    with patch('core.query_executor.get_neo4j_client') as mock_get_client:
        with patch('core.query_executor.get_cypher_generator'):
            mock_client = Mock()
            mock_client.query.return_value = [{"count": 100}]
            mock_get_client.return_value = mock_client

            from core.query_executor import QueryExecutor

            executor = QueryExecutor()
            result = executor.execute("MATCH (c:Crime) RETURN count(c)", "How many crimes?")

            assert result["results"] == [{"count": 100}]
            assert result["attempts"] == 1
            assert "error" not in result


def test_query_executor_retries_on_syntax_error(mock_settings):
    """Test executor retries when syntax error occurs"""
    with patch('core.query_executor.get_neo4j_client') as mock_get_client:
        with patch('core.query_executor.get_cypher_generator') as mock_gen:
            mock_client = Mock()
            # First call fails, second succeeds
            mock_client.query.side_effect = [
                CypherSyntaxError("Invalid syntax"),
                [{"count": 100}]
            ]
            mock_get_client.return_value = mock_client

            mock_generator = Mock()
            mock_generator.generate.return_value = "MATCH (c:Crime) RETURN count(c)"
            mock_gen.return_value = mock_generator

            from core.query_executor import QueryExecutor

            executor = QueryExecutor()
            result = executor.execute("BAD QUERY", "How many crimes?")

            assert result["attempts"] == 2
            assert result["results"] == [{"count": 100}]
            mock_generator.generate.assert_called_once()  # Regenerate once


def test_query_executor_reformulates_on_empty_results(mock_settings):
    """Test executor reformulates query when results are empty"""
    with patch('core.query_executor.get_neo4j_client') as mock_get_client:
        with patch('core.query_executor.get_cypher_generator') as mock_gen:
            mock_client = Mock()
            # First call empty, second has results
            mock_client.query.side_effect = [
                [],  # Empty
                [{"count": 50}]
            ]
            mock_get_client.return_value = mock_client

            mock_generator = Mock()
            mock_generator.generate.return_value = "MATCH (c:Crime) RETURN count(c)"
            mock_gen.return_value = mock_generator

            from core.query_executor import QueryExecutor

            executor = QueryExecutor()
            result = executor.execute("MATCH (c:Crime) WHERE c.type='X' RETURN count(c)", "How many crimes?")

            assert result["attempts"] == 2
            assert result["results"] == [{"count": 50}]


def test_query_executor_fails_after_max_retries(mock_settings):
    """Test executor returns error after max retries"""
    with patch('core.query_executor.get_neo4j_client') as mock_get_client:
        with patch('core.query_executor.get_cypher_generator') as mock_gen:
            mock_client = Mock()
            mock_client.query.side_effect = CypherSyntaxError("Invalid")
            mock_get_client.return_value = mock_client

            mock_generator = Mock()
            mock_generator.generate.return_value = "BAD QUERY"
            mock_gen.return_value = mock_generator

            from core.query_executor import QueryExecutor

            executor = QueryExecutor()
            result = executor.execute("BAD QUERY", "How many crimes?")

            assert result["attempts"] == 3
            assert "error" in result
            assert len(result["results"]) == 0
