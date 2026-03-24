# backend/tests/test_pipeline.py
import pytest
from unittest.mock import Mock, patch
import time




def test_pipeline_orchestrates_full_flow(mock_settings):
    """Test pipeline runs all 3 steps and returns complete response"""
    with patch('core.pipeline.get_cypher_generator') as mock_gen:
        with patch('core.pipeline.get_query_executor') as mock_exec:
            with patch('core.pipeline.get_answer_generator') as mock_ans:
                with patch('core.pipeline.get_schema_introspector') as mock_schema:
                    with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                        # Mock Cypher generator
                        mock_generator = Mock()
                        mock_generator.generate.return_value = "MATCH (c:Crime) RETURN count(c)"
                        mock_gen.return_value = mock_generator

                        # Mock query executor
                        mock_executor = Mock()
                        mock_executor.execute.return_value = {
                            "results": [{"count": 100}],
                            "cypher": "MATCH (c:Crime) RETURN count(c)",
                            "attempts": 1,
                            "graph_data": {"nodes": [], "edges": []}
                        }
                        mock_exec.return_value = mock_executor

                        # Mock answer generator
                        mock_answer_gen = Mock()
                        mock_answer_gen.generate.return_value = "Found 100 crimes."
                        mock_ans.return_value = mock_answer_gen

                        # Mock schema and examples (avoid actual Neo4j connection)
                        mock_schema.return_value = Mock()
                        mock_loader.return_value = Mock()

                        from core.pipeline import Pipeline

                        pipeline = Pipeline()
                        response = pipeline.run("How many crimes?")

                        assert response["question"] == "How many crimes?"
                        assert response["answer"] == "Found 100 crimes."
                        assert response["cypher"] == "MATCH (c:Crime) RETURN count(c)"
                        assert response["results"] == [{"count": 100}]
                        assert response["attempts"] == 1
                        assert "execution_time_ms" in response


def test_pipeline_initialization_caches_schema_and_examples(mock_settings):
    """Test pipeline initializes schema and examples at startup"""
    with patch('core.pipeline.get_cypher_generator') as mock_gen:
        with patch('core.pipeline.get_query_executor') as mock_exec:
            with patch('core.pipeline.get_answer_generator') as mock_ans:
                with patch('core.pipeline.get_schema_introspector') as mock_schema:
                    with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                        mock_introspector = Mock()
                        mock_introspector.introspect.return_value = "NODES: Crime"
                        mock_schema.return_value = mock_introspector

                        mock_few_shot = Mock()
                        mock_few_shot.load.return_value = [{"question": "test", "cypher": "test"}]
                        mock_loader.return_value = mock_few_shot

                        # Return empty mocks for the other getters
                        mock_gen.return_value = Mock()
                        mock_exec.return_value = Mock()
                        mock_ans.return_value = Mock()

                        from core.pipeline import Pipeline

                        pipeline = Pipeline()
                        pipeline.initialize()

                        mock_introspector.introspect.assert_called_once()
                        mock_few_shot.load.assert_called_once()