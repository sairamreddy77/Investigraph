# backend/tests/test_config.py
import pytest
from pydantic import ValidationError


def test_config_loads_from_env(monkeypatch):
    """Test that config loads environment variables correctly"""
    monkeypatch.setenv("NEO4J_URI", "neo4j://localhost:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("NEO4J_DATABASE", "pole")
    monkeypatch.setenv("GROQ_API_KEY", "test_key")

    from app.config import get_settings

    settings = get_settings()
    assert settings.NEO4J_URI == "neo4j://localhost:7687"
    assert settings.NEO4J_USERNAME == "neo4j"
    assert settings.NEO4J_PASSWORD == "password"
    assert settings.NEO4J_DATABASE == "pole"
    assert settings.GROQ_API_KEY == "test_key"

def test_config_validates_required_fields(monkeypatch):
    """Test that missing required fields raise validation error"""
    from app.config import Settings

    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_USERNAME", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings()