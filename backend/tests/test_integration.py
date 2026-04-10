# backend/tests/test_integration.py
from contextlib import ExitStack
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


def _initialize_pipeline(stack):
    graph_driver = stack.enter_context(patch("core.graphrag_pipeline.GraphDatabase.driver"))
    get_settings = stack.enter_context(
        patch("core.graphrag_pipeline.get_settings", return_value=_settings_mock())
    )
    get_groq_llm = stack.enter_context(patch("core.graphrag_pipeline.get_groq_llm"))
    get_embedder = stack.enter_context(patch("core.graphrag_pipeline.get_embedder"))
    build_text2cypher = stack.enter_context(
        patch("core.graphrag_pipeline.build_text2cypher_retriever")
    )
    build_vector = stack.enter_context(patch("core.graphrag_pipeline.build_vector_retriever"))
    build_vector_cypher = stack.enter_context(
        patch("core.graphrag_pipeline.build_vector_cypher_retriever")
    )
    graph_rag = stack.enter_context(patch("core.graphrag_pipeline.GraphRAG"))

    driver = Mock()
    llm = Mock()
    embedder = Mock()
    text2cypher = Mock()
    text2cypher._build_retriever.return_value = Mock(name="base_text2cypher")
    vector = Mock()
    vector_cypher = Mock()
    rag_text2cypher = Mock()
    rag_vector = Mock()
    rag_vector_cypher = Mock()

    graph_driver.return_value = driver
    get_groq_llm.return_value = llm
    get_embedder.return_value = embedder
    build_text2cypher.return_value = text2cypher
    build_vector.return_value = vector
    build_vector_cypher.return_value = vector_cypher
    graph_rag.side_effect = [rag_text2cypher, rag_vector, rag_vector_cypher]

    from core.graphrag_pipeline import GraphRAGPipeline

    pipeline = GraphRAGPipeline()
    pipeline.initialize()

    return pipeline, {
        "driver": driver,
        "llm": llm,
        "embedder": embedder,
        "text2cypher": text2cypher,
        "vector": vector,
        "vector_cypher": vector_cypher,
        "rag_text2cypher": rag_text2cypher,
        "rag_vector": rag_vector,
        "rag_vector_cypher": rag_vector_cypher,
        "get_settings": get_settings,
        "get_groq_llm": get_groq_llm,
        "get_embedder": get_embedder,
        "build_text2cypher": build_text2cypher,
        "build_vector": build_vector,
        "build_vector_cypher": build_vector_cypher,
    }


def test_full_pipeline_text2cypher_flow():
    with ExitStack() as stack:
        pipeline, mocks = _initialize_pipeline(stack)
        mocks["text2cypher"].search.return_value = Mock(
            items=[
                Mock(
                    content="Crime count context",
                    metadata={"cypher": "MATCH (c:Crime) RETURN count(c) AS total"},
                )
            ]
        )
        mocks["rag_text2cypher"].search.return_value = Mock(answer="There are 42 crimes.")

        response = pipeline.run("How many crimes are recorded?")

        assert response["retriever_used"] == "text2cypher"
        assert response["answer"] == "There are 42 crimes."
        assert response["cypher"] == "MATCH (c:Crime) RETURN count(c) AS total"
        assert response["results"] == [{"context": "Crime count context"}]


def test_full_pipeline_vector_flow():
    with ExitStack() as stack:
        pipeline, mocks = _initialize_pipeline(stack)
        item = Mock(content="Crime: Burglary (ID: 123)", metadata={})
        mocks["rag_vector"].search.return_value = Mock(
            answer="Found burglary incidents similar to your search.",
            retriever_result=Mock(items=[item]),
        )

        response = pipeline.run("burglary")

        assert response["retriever_used"] == "vector"
        assert response["answer"] == "Found burglary incidents similar to your search."
        assert response["retriever_context"] == ["Crime: Burglary (ID: 123)"]


def test_full_pipeline_fallback_flow():
    with ExitStack() as stack:
        pipeline, mocks = _initialize_pipeline(stack)
        mocks["rag_vector"].search.return_value = Mock(
            answer="",
            retriever_result=Mock(items=[]),
        )
        fallback_item = Mock(
            content="Crime: Burglary (ID: 123)",
            metadata={"crime_id": "123", "crime_type": "Burglary", "area": "WN"},
        )
        mocks["rag_vector_cypher"].search.return_value = Mock(
            answer="Fallback answer from graph-enriched context.",
            retriever_result=Mock(items=[fallback_item]),
        )

        response = pipeline.run("burglary")

        assert response["retriever_used"] == "vector → vector_cypher"
        assert response["answer"] == "Fallback answer from graph-enriched context."
        assert response["graph_data"]["nodes"]
        assert response["graph_data"]["edges"]


def test_full_pipeline_error_handling():
    with ExitStack() as stack:
        pipeline, mocks = _initialize_pipeline(stack)
        mocks["text2cypher"].search.side_effect = RuntimeError("All retrievers failed")

        response = pipeline.run("How many crimes are recorded?")

        assert response["retriever_used"] == "text2cypher"
        assert response["error"] == "All retrievers failed"
        assert response["answer"] == "Unable to process query: All retrievers failed"


def test_execution_time_tracking():
    with ExitStack() as stack:
        pipeline, mocks = _initialize_pipeline(stack)
        item = Mock(content="Crime: Burglary (ID: 123)", metadata={})
        mocks["rag_vector"].search.return_value = Mock(
            answer="Found burglary incidents.",
            retriever_result=Mock(items=[item]),
        )
        stack.enter_context(patch("core.graphrag_pipeline.time.time", side_effect=[100.0, 100.25]))

        response = pipeline.run("burglary")

        assert response["execution_time_ms"] == 250
