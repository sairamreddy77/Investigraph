# backend/tests/conftest.py
import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing"""
    driver = Mock()
    session = MagicMock()
    # Make session.return_value a context manager
    session_context = MagicMock()
    session_context.__enter__ = MagicMock(return_value=session)
    session_context.__exit__ = MagicMock(return_value=None)
    driver.session = MagicMock(return_value=session_context)
    return driver


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing"""
    monkeypatch.setenv("NEO4J_URI", "neo4j://localhost:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("NEO4J_DATABASE", "pole")
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
