# backend/tests/test_api.py
import os
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("NEO4J_URI", "neo4j://localhost:7687")
os.environ.setdefault("NEO4J_USERNAME", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "password")
os.environ.setdefault("NEO4J_DATABASE", "pole")
os.environ.setdefault("GROQ_API_KEY", "test_key")
os.environ.setdefault("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
os.environ.setdefault("VECTOR_INDEX_NAME", "crime_vector_index")
os.environ.setdefault("VECTOR_DIMENSIONS", "384")
os.environ.setdefault("GRAPHRAG_TOP_K", "5")

from app.main import app


@pytest.fixture
def mock_neo4j():
    with patch("app.main.get_neo4j_client") as mock:
        neo4j_client = Mock()
        neo4j_client.query.return_value = [{"test": 1}]
        neo4j_client.close.return_value = None
        mock.return_value = neo4j_client
        yield mock


@pytest.fixture
def mock_pipeline():
    with patch("app.main.get_graphrag_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = True
        pipeline.initialize.return_value = None
        pipeline.close.return_value = None
        pipeline.run.return_value = {
            "question": "Test question?",
            "answer": "Test answer",
            "cypher": "MATCH (n) RETURN n LIMIT 1",
            "results": [{"context": "Crime: Burglary (ID: 123)"}],
            "graph_data": {"nodes": [], "edges": []},
            "attempts": 1,
            "execution_time_ms": 100,
            "retriever_used": "vector_cypher",
            "retriever_context": ["Crime: Burglary (ID: 123)"],
        }
        mock.return_value = pipeline
        yield mock


@pytest.fixture
def mock_schema_introspector():
    with patch("app.main.get_schema_introspector") as mock:
        introspector = Mock()
        introspector.get_schema_text.return_value = "NODES:\n  Person(name)\n  Crime(type, date)"
        introspector.get_property_values.return_value = {
            "Crime.type": ["Burglary", "Drugs", "Robbery"]
        }
        mock.return_value = introspector
        yield mock


@pytest.fixture
def mock_few_shot_loader():
    with patch("app.main.get_few_shot_loader") as mock:
        loader = Mock()
        loader.get_examples.return_value = [
            {"question": "How many crimes?", "cypher": "MATCH (c:Crime) RETURN count(c)"},
            {"question": "Who investigated crime 123?", "cypher": "MATCH (o:Officer) RETURN o.name"},
        ]
        mock.return_value = loader
        yield mock


@pytest.fixture
def mock_case_study_loader():
    with patch("app.main.get_case_study_loader") as mock:
        loader = Mock()
        loader.load.return_value = [{"id": "case-1", "title": "Drug network"}]
        loader.get_case_studies.return_value = [{"id": "case-1", "title": "Drug network"}]
        mock.return_value = loader
        yield mock


@pytest.fixture
def client(mock_neo4j, mock_pipeline, mock_case_study_loader):
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "POLE NL-to-Cypher API"
    assert data["status"] == "running"
    assert data["endpoints"]["query"] == "/api/query"


def test_health_check_healthy(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["neo4j_connected"] is True
    assert data["pipeline_initialized"] is True
    assert data["llm_available"] is True


def test_health_check_neo4j_down(client, mock_pipeline):
    with patch("app.main.get_neo4j_client") as mock:
        neo4j_client = Mock()
        neo4j_client.query.side_effect = Exception("Connection failed")
        mock.return_value = neo4j_client

        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["neo4j_connected"] is False
    assert data["llm_available"] is True


def test_health_check_pipeline_not_initialized(client):
    with patch("app.main.get_graphrag_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = False
        mock.return_value = pipeline

        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["pipeline_initialized"] is False
    assert data["llm_available"] is False


def test_query_endpoint_success(client, mock_pipeline):
    response = client.post("/api/query", json={"question": "How many crimes are recorded?"})

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Test question?"
    assert data["answer"] == "Test answer"
    assert data["cypher"] == "MATCH (n) RETURN n LIMIT 1"
    assert data["results"] == [{"context": "Crime: Burglary (ID: 123)"}]
    assert data["graph_data"] == {"nodes": [], "edges": []}
    assert data["attempts"] == 1
    assert data["execution_time_ms"] == 100
    assert data["retriever_used"] == "vector_cypher"
    assert data["retriever_context"] == ["Crime: Burglary (ID: 123)"]
    mock_pipeline.return_value.run.assert_called_once_with("How many crimes are recorded?")


def test_query_endpoint_accepts_optional_cypher(client):
    with patch("app.main.get_graphrag_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = True
        pipeline.run.return_value = {
            "question": "burglary",
            "answer": "Found similar burglary incidents.",
            "cypher": None,
            "results": [],
            "graph_data": {"nodes": [], "edges": []},
            "attempts": 1,
            "execution_time_ms": 55,
            "retriever_used": "vector",
            "retriever_context": [],
        }
        mock.return_value = pipeline

        response = client.post("/api/query", json={"question": "burglary"})

    assert response.status_code == 200
    assert response.json()["cypher"] is None


def test_query_endpoint_empty_question(client):
    response = client.post("/api/query", json={"question": ""})

    assert response.status_code == 422


def test_query_endpoint_missing_question(client):
    response = client.post("/api/query", json={})

    assert response.status_code == 422


def test_query_endpoint_pipeline_error(client):
    with patch("app.main.get_graphrag_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = True
        pipeline.run.side_effect = Exception("Pipeline error")
        mock.return_value = pipeline

        response = client.post("/api/query", json={"question": "Test question"})

    assert response.status_code == 500
    assert "Pipeline error" in response.json()["detail"]


def test_query_endpoint_with_error_in_results(client):
    with patch("app.main.get_graphrag_pipeline") as mock:
        pipeline = Mock()
        pipeline._initialized = True
        pipeline.run.return_value = {
            "question": "Test question?",
            "answer": "Unable to process query",
            "cypher": "",
            "results": [],
            "graph_data": {"nodes": [], "edges": []},
            "attempts": 1,
            "execution_time_ms": 250,
            "error": "Retriever error",
            "retriever_used": "text2cypher",
            "retriever_context": [],
        }
        mock.return_value = pipeline

        response = client.post("/api/query", json={"question": "Test question"})

    assert response.status_code == 200
    data = response.json()
    assert data["error"] == "Retriever error"
    assert data["retriever_used"] == "text2cypher"


def test_schema_endpoint_success(client, mock_schema_introspector):
    response = client.get("/api/schema")

    assert response.status_code == 200
    data = response.json()
    assert "Person" in data["schema"]
    assert "Crime.type" in data["property_values"]
    mock_schema_introspector.return_value.get_schema_text.assert_called_once()
    mock_schema_introspector.return_value.get_property_values.assert_called_once()


def test_examples_endpoint_success(client, mock_few_shot_loader):
    response = client.get("/api/examples")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["examples"][0]["question"] == "How many crimes?"
    mock_few_shot_loader.return_value.get_examples.assert_called_once()


def test_case_studies_endpoint_success(client, mock_case_study_loader):
    response = client.get("/api/case-studies")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["case_studies"][0]["id"] == "case-1"
    mock_case_study_loader.return_value.get_case_studies.assert_called_once()
