# backend/tests/conftest.py
import importlib
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing."""
    driver = Mock()
    session = MagicMock()
    session_context = MagicMock()
    session_context.__enter__ = MagicMock(return_value=session)
    session_context.__exit__ = MagicMock(return_value=None)
    driver.session = MagicMock(return_value=session_context)
    return driver


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setenv("NEO4J_URI", "neo4j://localhost:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("NEO4J_DATABASE", "pole")
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    monkeypatch.setenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    monkeypatch.setenv("VECTOR_INDEX_NAME", "crime_vector_index")
    monkeypatch.setenv("VECTOR_DIMENSIONS", "384")
    monkeypatch.setenv("GRAPHRAG_TOP_K", "5")

    config_module = importlib.import_module("app.config")
    config_module.get_settings.cache_clear()

    yield

    config_module.get_settings.cache_clear()


@pytest.fixture
def mock_groq_llm():
    """Return a mocked GroqLLM instance."""
    from app.llm import GroqLLM

    return Mock(spec=GroqLLM)


@pytest.fixture
def mock_embedder():
    """Return a mocked SentenceTransformer embedder."""
    from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings

    return Mock(spec=SentenceTransformerEmbeddings)


@pytest.fixture
def mock_graphrag_pipeline():
    """Return a mocked GraphRAG pipeline instance."""
    from core.graphrag_pipeline import GraphRAGPipeline

    return Mock(spec=GraphRAGPipeline)
