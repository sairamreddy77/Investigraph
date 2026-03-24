# backend/tests/test_integration.py
"""
Integration tests for the complete POLE NL-to-Cypher QA pipeline.
Tests the full flow from question input to answer generation with mocked Neo4j and Groq.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import time


class TestIntegrationFullPipeline:
    """Test complete pipeline integration with mocked external services"""

    def test_successful_query_flow_first_attempt(self, mock_settings):
        """Test successful query generation and execution on first attempt"""
        with patch('core.pipeline.get_cypher_generator') as mock_gen:
            with patch('core.pipeline.get_query_executor') as mock_exec:
                with patch('core.pipeline.get_answer_generator') as mock_ans:
                    with patch('core.pipeline.get_schema_introspector') as mock_schema:
                        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                            # Setup mocks
                            mock_generator = Mock()
                            mock_generator.generate.return_value = "MATCH (c:Crime) RETURN count(c) AS total"
                            mock_gen.return_value = mock_generator

                            mock_executor = Mock()
                            mock_executor.execute.return_value = {
                                "results": [{"total": 42}],
                                "cypher": "MATCH (c:Crime) RETURN count(c) AS total",
                                "attempts": 1,
                                "graph_data": {"nodes": [], "edges": []}
                            }
                            mock_exec.return_value = mock_executor

                            mock_answer_gen = Mock()
                            mock_answer_gen.generate.return_value = "There are 42 crimes recorded in the database."
                            mock_ans.return_value = mock_answer_gen

                            mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Crime"))
                            mock_loader.return_value = Mock(load=Mock(return_value=[]))

                            from core.pipeline import Pipeline

                            pipeline = Pipeline()
                            response = pipeline.run("How many crimes are recorded?")

                            # Verify response structure
                            assert response["question"] == "How many crimes are recorded?"
                            assert response["answer"] == "There are 42 crimes recorded in the database."
                            assert response["cypher"] == "MATCH (c:Crime) RETURN count(c) AS total"
                            assert response["results"] == [{"total": 42}]
                            assert response["attempts"] == 1
                            assert "execution_time_ms" in response
                            assert response["execution_time_ms"] >= 0

                            # Verify each component was called correctly
                            mock_generator.generate.assert_called_once()
                            mock_executor.execute.assert_called_once()
                            mock_answer_gen.generate.assert_called_once()


    def test_retry_on_syntax_error(self, mock_settings):
        """Test that pipeline retries when Cypher has syntax errors"""
        with patch('core.pipeline.get_cypher_generator') as mock_gen:
            with patch('core.pipeline.get_query_executor') as mock_exec:
                with patch('core.pipeline.get_answer_generator') as mock_ans:
                    with patch('core.pipeline.get_schema_introspector') as mock_schema:
                        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                            # Setup generator to return bad query first, then good query
                            mock_generator = Mock()
                            mock_gen.return_value = mock_generator

                            # Setup executor to simulate retry behavior
                            mock_executor = Mock()
                            mock_executor.execute.return_value = {
                                "results": [{"count": 10}],
                                "cypher": "MATCH (c:Crime) WHERE c.type = 'Drugs' RETURN count(c) AS count",
                                "attempts": 2,  # Took 2 attempts
                                "graph_data": {"nodes": [], "edges": []}
                            }
                            mock_exec.return_value = mock_executor

                            mock_answer_gen = Mock()
                            mock_answer_gen.generate.return_value = "Found 10 drug-related crimes."
                            mock_ans.return_value = mock_answer_gen

                            mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Crime"))
                            mock_loader.return_value = Mock(load=Mock(return_value=[]))

                            from core.pipeline import Pipeline

                            pipeline = Pipeline()
                            response = pipeline.run("Show all drug crimes")

                            # Verify retry happened
                            assert response["attempts"] == 2
                            assert response["results"] == [{"count": 10}]
                            assert response["answer"] == "Found 10 drug-related crimes."
                            assert "execution_time_ms" in response


    def test_retry_on_empty_results(self, mock_settings):
        """Test that pipeline retries when query returns empty results"""
        with patch('core.pipeline.get_cypher_generator') as mock_gen:
            with patch('core.pipeline.get_query_executor') as mock_exec:
                with patch('core.pipeline.get_answer_generator') as mock_ans:
                    with patch('core.pipeline.get_schema_introspector') as mock_schema:
                        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                            mock_generator = Mock()
                            mock_gen.return_value = mock_generator

                            # Executor simulates empty results on first attempt, then success
                            mock_executor = Mock()
                            mock_executor.execute.return_value = {
                                "results": [{"name": "John", "type": "Burglary"}],
                                "cypher": "MATCH (p:Person)-[:PARTY_TO]->(c:Crime) WHERE toLower(c.type) CONTAINS 'burglary' RETURN p.name, c.type",
                                "attempts": 2,
                                "graph_data": {"nodes": [], "edges": []}
                            }
                            mock_exec.return_value = mock_executor

                            mock_answer_gen = Mock()
                            mock_answer_gen.generate.return_value = "Found 1 person involved in burglary: John."
                            mock_ans.return_value = mock_answer_gen

                            mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Person, Crime"))
                            mock_loader.return_value = Mock(load=Mock(return_value=[]))

                            from core.pipeline import Pipeline

                            pipeline = Pipeline()
                            response = pipeline.run("Who is involved in burglaries?")

                            # Verify retry occurred
                            assert response["attempts"] == 2
                            assert len(response["results"]) > 0
                            assert response["answer"] == "Found 1 person involved in burglary: John."


    def test_empty_results_handling_after_max_retries(self, mock_settings):
        """Test graceful handling when query returns empty after all retries"""
        with patch('core.pipeline.get_cypher_generator') as mock_gen:
            with patch('core.pipeline.get_query_executor') as mock_exec:
                with patch('core.pipeline.get_answer_generator') as mock_ans:
                    with patch('core.pipeline.get_schema_introspector') as mock_schema:
                        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                            mock_generator = Mock()
                            mock_gen.return_value = mock_generator

                            # Executor returns empty results after all attempts
                            mock_executor = Mock()
                            mock_executor.execute.return_value = {
                                "results": [],
                                "cypher": "MATCH (p:Person) WHERE p.name = 'NonexistentPerson' RETURN p",
                                "attempts": 3,  # Max retries
                                "graph_data": {"nodes": [], "edges": []}
                            }
                            mock_exec.return_value = mock_executor

                            mock_answer_gen = Mock()
                            mock_answer_gen.generate.return_value = "No results found. The query returned 0 records. Try rephrasing your question or using different search terms."
                            mock_ans.return_value = mock_answer_gen

                            mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Person"))
                            mock_loader.return_value = Mock(load=Mock(return_value=[]))

                            from core.pipeline import Pipeline

                            pipeline = Pipeline()
                            response = pipeline.run("Find person named NonexistentPerson")

                            # Verify graceful handling
                            assert response["attempts"] == 3
                            assert response["results"] == []
                            assert "No results found" in response["answer"]
                            assert "execution_time_ms" in response


    def test_multi_hop_query_with_relationships(self, mock_settings):
        """Test complex multi-hop query through relationships"""
        with patch('core.pipeline.get_cypher_generator') as mock_gen:
            with patch('core.pipeline.get_query_executor') as mock_exec:
                with patch('core.pipeline.get_answer_generator') as mock_ans:
                    with patch('core.pipeline.get_schema_introspector') as mock_schema:
                        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                            mock_generator = Mock()
                            mock_generator.generate.return_value = (
                                "MATCH (p:Person)-[:PARTY_TO]->(c:Crime)-[:OCCURRED_AT]->(l:Location)-[:LOCATION_IN_AREA]->(a:AREA) "
                                "WHERE toLower(c.type) CONTAINS 'drug' AND toLower(a.areaCode) = 'wn' "
                                "RETURN p.name, p.surname, c.type, a.areaCode"
                            )
                            mock_gen.return_value = mock_generator

                            mock_executor = Mock()
                            mock_executor.execute.return_value = {
                                "results": [
                                    {"p.name": "John", "p.surname": "Smith", "c.type": "Drugs", "a.areaCode": "WN"},
                                    {"p.name": "Sarah", "p.surname": "Jones", "c.type": "Drugs", "a.areaCode": "WN"}
                                ],
                                "cypher": mock_generator.generate.return_value,
                                "attempts": 1,
                                "graph_data": {
                                    "nodes": [
                                        {"id": "p1", "label": "Person", "name": "John Smith"},
                                        {"id": "p2", "label": "Person", "name": "Sarah Jones"}
                                    ],
                                    "edges": [
                                        {"from": "p1", "to": "c1", "label": "PARTY_TO"},
                                        {"from": "p2", "to": "c2", "label": "PARTY_TO"}
                                    ]
                                }
                            }
                            mock_exec.return_value = mock_executor

                            mock_answer_gen = Mock()
                            mock_answer_gen.generate.return_value = "Found 2 people involved in drug crimes in the WN area: John Smith and Sarah Jones."
                            mock_ans.return_value = mock_answer_gen

                            mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Person, Crime, Location, AREA"))
                            mock_loader.return_value = Mock(load=Mock(return_value=[]))

                            from core.pipeline import Pipeline

                            pipeline = Pipeline()
                            response = pipeline.run("Find people involved in drug crimes in area WN")

                            # Verify complex query handling
                            assert response["attempts"] == 1
                            assert len(response["results"]) == 2
                            assert response["graph_data"]["nodes"]
                            assert response["graph_data"]["edges"]
                            assert "John Smith" in response["answer"]
                            assert "Sarah Jones" in response["answer"]


    def test_aggregation_query_with_ordering(self, mock_settings):
        """Test aggregation query with ORDER BY and LIMIT"""
        with patch('core.pipeline.get_cypher_generator') as mock_gen:
            with patch('core.pipeline.get_query_executor') as mock_exec:
                with patch('core.pipeline.get_answer_generator') as mock_ans:
                    with patch('core.pipeline.get_schema_introspector') as mock_schema:
                        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                            mock_generator = Mock()
                            mock_generator.generate.return_value = (
                                "MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)-[:LOCATION_IN_AREA]->(a:AREA) "
                                "RETURN a.areaCode, count(c) AS crime_count "
                                "ORDER BY crime_count DESC LIMIT 1"
                            )
                            mock_gen.return_value = mock_generator

                            mock_executor = Mock()
                            mock_executor.execute.return_value = {
                                "results": [{"a.areaCode": "WN", "crime_count": 45}],
                                "cypher": mock_generator.generate.return_value,
                                "attempts": 1,
                                "graph_data": {"nodes": [], "edges": []}
                            }
                            mock_exec.return_value = mock_executor

                            mock_answer_gen = Mock()
                            mock_answer_gen.generate.return_value = "The area with the highest number of crimes is WN with 45 crimes."
                            mock_ans.return_value = mock_answer_gen

                            mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Crime, Location, AREA"))
                            mock_loader.return_value = Mock(load=Mock(return_value=[]))

                            from core.pipeline import Pipeline

                            pipeline = Pipeline()
                            response = pipeline.run("Which area has the most crimes?")

                            # Verify aggregation handling
                            assert response["attempts"] == 1
                            assert response["results"][0]["crime_count"] == 45
                            assert "WN" in response["answer"]
                            assert "45" in response["answer"]


    def test_execution_time_tracking(self, mock_settings):
        """Test that execution time is properly tracked"""
        with patch('core.pipeline.get_cypher_generator') as mock_gen:
            with patch('core.pipeline.get_query_executor') as mock_exec:
                with patch('core.pipeline.get_answer_generator') as mock_ans:
                    with patch('core.pipeline.get_schema_introspector') as mock_schema:
                        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                            mock_generator = Mock()
                            mock_generator.generate.return_value = "MATCH (c:Crime) RETURN count(c)"
                            mock_gen.return_value = mock_generator

                            mock_executor = Mock()
                            # Simulate some processing time
                            def slow_execute(*args, **kwargs):
                                time.sleep(0.01)  # 10ms
                                return {
                                    "results": [{"count": 100}],
                                    "cypher": "MATCH (c:Crime) RETURN count(c)",
                                    "attempts": 1,
                                    "graph_data": {"nodes": [], "edges": []}
                                }
                            mock_executor.execute.side_effect = slow_execute
                            mock_exec.return_value = mock_executor

                            mock_answer_gen = Mock()
                            mock_answer_gen.generate.return_value = "Found 100 crimes."
                            mock_ans.return_value = mock_answer_gen

                            mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Crime"))
                            mock_loader.return_value = Mock(load=Mock(return_value=[]))

                            from core.pipeline import Pipeline

                            pipeline = Pipeline()
                            response = pipeline.run("Count crimes")

                            # Verify execution time is tracked
                            assert "execution_time_ms" in response
                            assert response["execution_time_ms"] >= 10  # At least 10ms due to sleep


class TestIntegrationWithMockedNeo4j:
    """Test integration with mocked Neo4j driver"""

    def test_neo4j_connection_in_pipeline(self, mock_settings):
        with patch('core.pipeline.get_cypher_generator') as mock_gen:
            with patch('core.pipeline.get_query_executor') as mock_exec:
                with patch('core.pipeline.get_answer_generator') as mock_ans:
                    with patch('core.pipeline.get_schema_introspector') as mock_schema:
                        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
                            mock_generator = Mock()
                            mock_generator.generate.return_value = "MATCH (c:Crime) RETURN c LIMIT 5"
                            mock_gen.return_value = mock_generator

                            mock_executor = Mock()
                            mock_executor.execute.return_value = {
                                "results": [
                                    {"c.type": "Burglary", "c.date": "2023-01-15"},
                                    {"c.type": "Drugs", "c.date": "2023-02-20"}
                                ],
                                "cypher": "MATCH (c:Crime) RETURN c LIMIT 5",
                                "attempts": 1,
                                "graph_data": {"nodes": [], "edges": []}
                            }
                            mock_exec.return_value = mock_executor

                            mock_answer_gen = Mock()
                            mock_answer_gen.generate.return_value = "Found 2 crimes: Burglary and Drugs."
                            mock_ans.return_value = mock_answer_gen

                            mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Crime"))
                            mock_loader.return_value = Mock(load=Mock(return_value=[]))

                            from core.pipeline import Pipeline

                            pipeline = Pipeline()
                            response = pipeline.run("Show recent crimes")

                            assert len(response["results"]) == 2
                            assert response["results"][0]["c.type"] == "Burglary"


    class TestIntegrationWithMockedGroq:
        """Test integration with mocked Groq LLM"""

        def test_groq_llm_invocation(self, mock_settings):
            with patch('core.cypher_generator.get_groq_client') as mock_get_client:
                with patch('core.cypher_generator.get_schema_introspector') as mock_schema:
                    with patch('core.cypher_generator.get_few_shot_loader') as mock_loader:
                        mock_client = Mock()
                        mock_client.chat_completion.return_value = "MATCH (p:Person) RETURN p.name LIMIT 10"
                        mock_get_client.return_value = mock_client

                        mock_schema.return_value = Mock(introspect=Mock(return_value="NODES: Person"))
                        mock_loader.return_value = Mock(format_for_prompt=Mock(return_value=""))

                        from core.cypher_generator import CypherGenerator

                        generator = CypherGenerator()
                        cypher = generator.generate("List all people")

                        assert mock_client.chat_completion.called
                        assert cypher == "MATCH (p:Person) RETURN p.name LIMIT 10"