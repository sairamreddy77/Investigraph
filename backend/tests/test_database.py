import importlib
from unittest.mock import Mock, patch
import pytest


@pytest.fixture(autouse=True)
def reset_singletons():
    database_module = importlib.import_module("app.database")
    database_module.Neo4jClient._instance = None
    database_module._neo4j_client = None
    yield
    database_module.Neo4jClient._instance = None
    database_module._neo4j_client = None


def test_neo4j_client_connects(mock_settings):
    """Test Neo4j client establishes connection"""
    database_module = importlib.import_module("app.database")

    with patch.object(database_module, "GraphDatabase") as mock_graphdb:
        mock_driver = Mock()
        mock_graphdb.driver.return_value = mock_driver

        client = database_module.Neo4jClient()
        client.connect()

        mock_graphdb.driver.assert_called_once()
        mock_driver.verify_connectivity.assert_called_once()
        assert client.driver is not None


def test_neo4j_client_query_executes(mock_settings, mock_neo4j_driver):
    """Test query execution returns results"""
    database_module = importlib.import_module("app.database")

    with patch.object(database_module, "GraphDatabase") as mock_graphdb:
        mock_graphdb.driver.return_value = mock_neo4j_driver

        mock_result = Mock()
        mock_result.data.return_value = [{"name": "John", "age": 30}]
        mock_neo4j_driver.session.return_value.__enter__.return_value.run.return_value = mock_result

        client = database_module.Neo4jClient()
        client.connect()
        results = client.query("MATCH (n) RETURN n LIMIT 1")

        assert len(results) == 1
        assert results[0]["name"] == "John"


def test_neo4j_client_closes_connection(mock_settings, mock_neo4j_driver):
    """Test client closes connection properly"""
    database_module = importlib.import_module("app.database")

    with patch.object(database_module, "GraphDatabase") as mock_graphdb:
        mock_graphdb.driver.return_value = mock_neo4j_driver

        client = database_module.Neo4jClient()
        client.connect()
        client.close()

        mock_neo4j_driver.close.assert_called_once()