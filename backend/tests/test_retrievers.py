from unittest.mock import ANY, Mock, patch

import pytest


def _result_with_items(items):
    return Mock(items=items)


def _wrapper():
    from core.retrievers import Text2CypherRetrieverWithRetry

    return Text2CypherRetrieverWithRetry(
        driver=Mock(),
        llm=Mock(),
        neo4j_schema="schema",
        examples=["example"],
        neo4j_database="pole",
        custom_prompt="prompt",
    )


def test_text2cypher_retry_wrapper_retries_on_error():
    wrapper = _wrapper()
    first_retriever = Mock()
    second_retriever = Mock()
    first_retriever.search.side_effect = RuntimeError("bad cypher")
    second_retriever.search.return_value = _result_with_items([Mock(content="ok")])

    with patch.object(wrapper, "_build_retriever", side_effect=[first_retriever, second_retriever]) as build:
        result = wrapper.search("How many crimes?")

    assert len(result.items) == 1
    assert build.call_count == 2
    assert first_retriever.search.called
    assert second_retriever.search.called


def test_text2cypher_retry_wrapper_retries_on_empty():
    wrapper = _wrapper()
    first_retriever = Mock()
    second_retriever = Mock()
    first_retriever.search.return_value = _result_with_items([])
    second_retriever.search.return_value = _result_with_items([Mock(content="filled")])

    with patch.object(wrapper, "_build_retriever", side_effect=[first_retriever, second_retriever]) as build:
        result = wrapper.search("How many crimes?")

    assert [item.content for item in result.items] == ["filled"]
    assert build.call_count == 2


def test_text2cypher_retry_wrapper_max_retries():
    wrapper = _wrapper()
    retrievers = [Mock(), Mock(), Mock()]
    for retriever in retrievers:
        retriever.search.side_effect = RuntimeError("still failing")

    with patch.object(wrapper, "_build_retriever", side_effect=retrievers) as build:
        with pytest.raises(RuntimeError, match="still failing"):
            wrapper.search("How many crimes?")

    assert build.call_count == 3


def test_build_text2cypher_retriever():
    with patch("core.retrievers.get_schema_introspector") as mock_schema:
        with patch("core.retrievers.get_few_shot_loader") as mock_loader:
            with patch("core.retrievers.format_text2cypher_examples") as mock_format:
                with patch("core.retrievers.get_text2cypher_custom_prompt") as mock_prompt:
                    with patch("core.retrievers.Text2CypherRetrieverWithRetry") as mock_wrapper:
                        mock_schema.return_value.introspect.return_value = "schema"
                        mock_loader.return_value.get_examples.return_value = [{"question": "q", "cypher": "c"}]
                        mock_format.return_value = ["formatted"]
                        mock_prompt.return_value = "custom prompt"

                        from core.retrievers import build_text2cypher_retriever

                        build_text2cypher_retriever(driver=Mock(), llm=Mock(), neo4j_database="pole")

    mock_schema.return_value.introspect.assert_called_once()
    mock_loader.return_value.get_examples.assert_called_once()
    mock_wrapper.assert_called_once_with(
        driver=ANY,
        llm=ANY,
        neo4j_schema="schema",
        examples=["formatted"],
        neo4j_database="pole",
        custom_prompt="custom prompt",
    )


def test_build_vector_retriever():
    with patch("core.retrievers.VectorRetriever") as mock_vector_retriever:
        from core.retrievers import build_vector_retriever

        driver = Mock()
        embedder = Mock()
        build_vector_retriever(
            driver=driver,
            embedder=embedder,
            index_name="crime_vector_index",
            neo4j_database="pole",
        )

    mock_vector_retriever.assert_called_once_with(
        driver=driver,
        index_name="crime_vector_index",
        embedder=embedder,
        neo4j_database="pole",
        return_properties=["id", "type", "date", "last_outcome", "note", "charge"],
    )


def test_build_vector_cypher_retriever():
    with patch("core.retrievers.VectorCypherRetriever") as mock_vector_cypher:
        from core.retrievers import build_vector_cypher_retriever

        driver = Mock()
        embedder = Mock()
        build_vector_cypher_retriever(
            driver=driver,
            embedder=embedder,
            index_name="crime_vector_index",
            neo4j_database="pole",
        )

    kwargs = mock_vector_cypher.call_args.kwargs
    retrieval_query = kwargs["retrieval_query"]

    assert "PARTY_TO" in retrieval_query
    assert "OCCURRED_AT" in retrieval_query
    assert "LOCATION_IN_AREA" in retrieval_query
    assert "INVESTIGATED_BY" in retrieval_query
