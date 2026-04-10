# backend/tests/test_pipeline.py
from unittest.mock import Mock, patch


def _settings_mock():
    return Mock(
        NEO4J_URI="bolt://localhost:7687",
        NEO4J_USERNAME="neo4j",
        NEO4J_PASSWORD="pass",
        NEO4J_DATABASE="pole",
        GROQ_API_KEY="test",
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        VECTOR_INDEX_NAME="crime_vector_index",
        VECTOR_DIMENSIONS=384,
        GRAPHRAG_TOP_K=5,
        BACKEND_PORT=8000,
        CORS_ORIGINS="*",
        LOG_LEVEL="INFO",
        LOG_QUERIES=True,
    )


def _build_pipeline():
    with patch("core.graphrag_pipeline.get_settings", return_value=_settings_mock()):
        from core.graphrag_pipeline import GraphRAGPipeline

        return GraphRAGPipeline()


def test_pipeline_classifies_structured_question():
    pipeline = _build_pipeline()

    assert pipeline._classify_question("How many crimes?") == "text2cypher"


def test_pipeline_classifies_semantic_question():
    pipeline = _build_pipeline()

    assert pipeline._classify_question("Tell me about drug crimes") == "vector_cypher"


def test_pipeline_classifies_lookup_question():
    pipeline = _build_pipeline()

    assert pipeline._classify_question("burglary") == "vector"


def test_pipeline_classifies_who_question():
    pipeline = _build_pipeline()

    assert pipeline._classify_question("Who investigated crime 123?") == "text2cypher"


def test_pipeline_fallback_mapping():
    pipeline = _build_pipeline()

    assert pipeline._get_fallback("text2cypher") == "vector_cypher"
    assert pipeline._get_fallback("vector") == "vector_cypher"
    assert pipeline._get_fallback("vector_cypher") == "text2cypher"


def test_pipeline_run_returns_enriched_response():
    pipeline = _build_pipeline()

    result_item = Mock(
        content="Crime count context",
        metadata={
            "cypher": "MATCH (c:Crime) RETURN count(c) AS total",
        },
    )
    pipeline._text2cypher = Mock()
    pipeline._text2cypher.search.return_value = Mock(items=[result_item])
    pipeline._rag_instances = {
        "text2cypher": Mock(search=Mock(return_value=Mock(answer="Found 42 crimes.")))
    }

    response = pipeline.run("How many crimes?")

    assert response["question"] == "How many crimes?"
    assert response["answer"] == "Found 42 crimes."
    assert response["cypher"] == "MATCH (c:Crime) RETURN count(c) AS total"
    assert response["results"] == [{"context": "Crime count context"}]
    assert response["graph_data"] == {"nodes": [], "edges": []}
    assert response["attempts"] == 1
    assert isinstance(response["execution_time_ms"], int)
    assert response["retriever_used"] == "text2cypher"
    assert response["retriever_context"] == ["Crime count context"]


def test_pipeline_run_with_fallback():
    pipeline = _build_pipeline()

    empty_result = Mock(answer="", retriever_result=Mock(items=[]))
    enriched_item = Mock(
        content="Crime: Burglary (ID: 123)",
        metadata={"crime_id": "123", "crime_type": "Burglary", "area": "WN"},
    )
    fallback_result = Mock(
        answer="Burglary incidents were found in area WN.",
        retriever_result=Mock(items=[enriched_item]),
    )
    pipeline._rag_instances = {
        "vector": Mock(search=Mock(return_value=empty_result)),
        "vector_cypher": Mock(search=Mock(return_value=fallback_result)),
    }

    response = pipeline.run("burglary")

    assert response["retriever_used"] == "vector → vector_cypher"
    assert response["answer"] == "Burglary incidents were found in area WN."
    assert response["results"] == [{"context": "Crime: Burglary (ID: 123)"}]
    assert response["retriever_context"] == ["Crime: Burglary (ID: 123)"]
    assert response["graph_data"]["nodes"]
    assert response["graph_data"]["edges"]


def test_pipeline_run_with_error():
    pipeline = _build_pipeline()

    pipeline._text2cypher = Mock()
    pipeline._text2cypher.search.side_effect = RuntimeError("Retriever exploded")
    pipeline._rag_instances = {"text2cypher": Mock()}

    response = pipeline.run("How many crimes?")

    assert response["question"] == "How many crimes?"
    assert response["error"] == "Retriever exploded"
    assert response["answer"] == "Unable to process query: Retriever exploded"
    assert response["results"] == []
    assert response["graph_data"] == {"nodes": [], "edges": []}


def test_pipeline_extract_graph_data():
    pipeline = _build_pipeline()

    items = [
        Mock(metadata={"crime_id": "123", "crime_type": "Burglary", "area": "WN"}),
        Mock(metadata={"crime_id": "456", "crime_type": "Drugs", "area": "WN"}),
        Mock(metadata=None),
    ]

    graph_data = pipeline._extract_graph_data_from_context(items)

    node_ids = {node["id"] for node in graph_data["nodes"]}
    assert "123" in node_ids
    assert "456" in node_ids
    assert "area_WN" in node_ids
    assert any(edge["relationship"] == "OCCURRED_IN" for edge in graph_data["edges"])


def test_pipeline_close():
    pipeline = _build_pipeline()
    driver = Mock()
    pipeline._driver = driver

    pipeline.close()

    driver.close.assert_called_once()
    assert pipeline._driver is None
