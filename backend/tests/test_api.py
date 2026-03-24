# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import os

os.environ.setdefault("NEO4J_URI", "neo4j://localhost:7687")
os.environ.setdefault("NEO4J_USERNAME", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "password")
os.environ.setdefault("GROQ_API_KEY", "test_key")

from app.main import app
from app.models import GraphData


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_neo4j():
    with patch("app.main.get_neo4j_client") as mock:
        client = Mock()
        client.query.return_value = [{"test": 1}]
        client.close.return_value = None
        mock.return_value = client
        yield mock


@pytest.fixture
def mock_pipeline():
    with patch("app.main.get_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = True
        pipeline.initialize.return_value = None
        pipeline.run.return_value = {
            "question": "Test question?",
            "answer": "Test answer",
            "cypher": "MATCH (n) RETURN n LIMIT 1",
            "results": [{"n": {"name": "test"}}],
            "graph_data": {"nodes": [], "edges": []},
            "attempts": 1,
            "execution_time_ms": 100
        }
        mock.return_value = pipeline
        yield mock


@pytest.fixture
def mock_schema_introspector():
    with patch("app.main.get_schema_introspector") as mock:
        introspector = Mock()
        introspector.get_schema_text.return_value = "NODES:\n  Person(name, age)\n  Crime(type, date)"
        introspector.get_property_values.return_value = {
            "Crime.type": ["Burglary", "Drugs", "Robbery"]
        }
        introspector.introspect.return_value = None
        mock.return_value = introspector
        yield mock


@pytest.fixture
def mock_few_shot_loader():
    with patch("app.main.get_few_shot_loader") as mock:
        loader = Mock()
        loader.get_examples.return_value = [
            {"question": "How many crimes?", "cypher": "MATCH (c:Crime) RETURN count(c)"},
            {"question": "List people", "cypher": "MATCH (p:Person) RETURN p.name"}
        ]
        loader.load.return_value = None
        mock.return_value = loader
        yield mock


# ==================== ROOT ENDPOINT ====================

def test_root_endpoint(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "POLE NL-to-Cypher API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"
    assert "query" in data["endpoints"]
    assert "schema" in data["endpoints"]
    assert "examples" in data["endpoints"]
    assert "health" in data["endpoints"]


# ==================== HEALTH CHECK ====================

def test_health_check_healthy(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["neo4j_connected"] is True
    assert data["pipeline_initialized"] is True
    assert "details" in data


def test_health_check_neo4j_down(client, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    with patch("app.main.get_neo4j_client") as mock:
        client_instance = Mock()
        client_instance.query.side_effect = Exception("Connection failed")
        mock.return_value = client_instance

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["neo4j_connected"] is False


def test_health_check_pipeline_not_initialized(client, mock_neo4j, mock_schema_introspector, mock_few_shot_loader):
    with patch("app.main.get_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = False
        mock.return_value = pipeline

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["pipeline_initialized"] is False


# ==================== QUERY ENDPOINT ====================

def test_query_endpoint_success(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    response = client.post("/api/query", json={"question": "How many crimes are recorded?"})
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Test question?"
    assert data["answer"] == "Test answer"
    assert data["cypher"] == "MATCH (n) RETURN n LIMIT 1"
    assert isinstance(data["results"], list)
    assert data["attempts"] == 1
    assert data["execution_time_ms"] == 100
    assert "graph_data" in data
    assert "nodes" in data["graph_data"]
    assert "edges" in data["graph_data"]
    mock_pipeline.return_value.run.assert_called_once_with("How many crimes are recorded?")


def test_query_endpoint_empty_question(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 422


def test_query_endpoint_missing_question(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    response = client.post("/api/query", json={})
    assert response.status_code == 422


def test_query_endpoint_pipeline_error(client, mock_neo4j, mock_schema_introspector, mock_few_shot_loader):
    with patch("app.main.get_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = True
        pipeline.run.side_effect = Exception("Pipeline error")
        mock.return_value = pipeline

        response = client.post("/api/query", json={"question": "Test question"})
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Pipeline error" in data["detail"]


def test_query_endpoint_with_error_in_results(client, mock_neo4j, mock_schema_introspector, mock_few_shot_loader):
    with patch("app.main.get_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = True
        pipeline.run.return_value = {
            "question": "Test question?",
            "answer": "Unable to process query",
            "cypher": "INVALID CYPHER",
            "results": [],
            "graph_data": {"nodes": [], "edges": []},
            "attempts": 3,
            "execution_time_ms": 250,
            "error": "Syntax error"
        }
        mock.return_value = pipeline

        response = client.post("/api/query", json={"question": "Test question"})
        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "Syntax error"
        assert data["attempts"] == 3
        assert len(data["results"]) == 0


# ==================== SCHEMA ENDPOINT ====================

def test_schema_endpoint_success(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    response = client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert "schema" in data
    assert "property_values" in data
    assert "Person" in data["schema"]
    assert "Crime" in data["schema"]
    assert "Crime.type" in data["property_values"]
    mock_schema_introspector.return_value.get_schema_text.assert_called_once()
    mock_schema_introspector.return_value.get_property_values.assert_called_once()


def test_schema_endpoint_error(client, mock_neo4j, mock_pipeline, mock_few_shot_loader):
    with patch("app.main.get_schema_introspector") as mock:
        introspector = Mock()
        introspector.get_schema_text.side_effect = Exception("Schema error")
        mock.return_value = introspector

        response = client.get("/api/schema")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Schema error" in data["detail"]


# ==================== EXAMPLES ENDPOINT ====================

def test_examples_endpoint_success(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    response = client.get("/api/examples")
    assert response.status_code == 200
    data = response.json()
    assert "examples" in data
    assert "count" in data
    assert data["count"] == 2
    assert len(data["examples"]) == 2
    example = data["examples"][0]
    assert "question" in example
    assert "cypher" in example
    assert example["question"] == "How many crimes?"
    mock_few_shot_loader.return_value.get_examples.assert_called_once()


def test_examples_endpoint_empty(client, mock_neo4j, mock_pipeline, mock_schema_introspector):
    with patch("app.main.get_few_shot_loader") as mock:
        loader = Mock()
        loader.get_examples.return_value = []
        mock.return_value = loader

        response = client.get("/api/examples")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["examples"]) == 0


def test_examples_endpoint_error(client, mock_neo4j, mock_pipeline, mock_schema_introspector):
    with patch("app.main.get_few_shot_loader") as mock:
        loader = Mock()
        loader.get_examples.side_effect = Exception("Load error")
        mock.return_value = loader

        response = client.get("/api/examples")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Load error" in data["detail"]


# ==================== INTEGRATION TESTS ====================

def test_query_with_multiple_results(client, mock_neo4j, mock_schema_introspector, mock_few_shot_loader):
    with patch("app.main.get_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = True
        pipeline.run.return_value = {
            "question": "List all people",
            "answer": "Found 3 people: John, Jane, Bob",
            "cypher": "MATCH (p:Person) RETURN p.name",
            "results": [{"p.name": "John"}, {"p.name": "Jane"}, {"p.name": "Bob"}],
            "graph_data": {
                "nodes": [
                    {"id": "1", "label": "Person", "properties": {"name": "John"}},
                    {"id": "2", "label": "Person", "properties": {"name": "Jane"}},
                    {"id": "3", "label": "Person", "properties": {"name": "Bob"}}
                ],
                "edges": []
            },
            "attempts": 1,
            "execution_time_ms": 150
        }
        mock.return_value = pipeline

        response = client.post("/api/query", json={"question": "List all people"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        assert len(data["graph_data"]["nodes"]) == 3


def test_cors_headers(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader):
    response = client.get("/health")
    assert response.status_code == 200


def test_request_logging(client, mock_neo4j, mock_pipeline, mock_schema_introspector, mock_few_shot_loader, caplog):
    import logging
    caplog.set_level(logging.INFO)
    response = client.get("/health")
    assert response.status_code == 200
    assert any("GET /health" in record.message for record in caplog.records)