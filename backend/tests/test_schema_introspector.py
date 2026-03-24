# backend/tests/test_schema_introspector.py
import pytest
from unittest.mock import Mock, patch


def test_schema_introspector_fetches_node_labels(mock_settings, mock_neo4j_driver):
    with patch("core.schema_introspector.get_neo4j_client") as mock_get_client:
        mock_client = Mock()
        mock_client.query.side_effect = [
            [  # nodes
                {"label": "Person", "properties": ["name", "surname", "age"]},
                {"label": "Crime", "properties": ["type", "date", "last_outcome"]},
            ],
            [  # relationships
                {"type": "PARTY_TO", "start": "Person", "end": "Crime"},
            ],
            [], [], [], [],  # 4 property-value queries
        ]
        mock_get_client.return_value = mock_client

        from core.schema_introspector import SchemaIntrospector
        schema = SchemaIntrospector().introspect()

        assert "Person" in schema
        assert "Crime" in schema
        assert "name" in schema


def test_schema_introspector_fetches_relationships(mock_settings, mock_neo4j_driver):
    """Test introspector fetches relationship types"""
    with patch('core.schema_introspector.get_neo4j_client') as mock_get_client:
        mock_client = Mock()
        mock_client.query.side_effect = [
            [{"labels": ["Person"], "properties": ["name"]}],  # Nodes
            [{"type": "PARTY_TO", "start": "Person", "end": "Crime"}]  # Relationships
        ]
        mock_get_client.return_value = mock_client

        from core.schema_introspector import SchemaIntrospector

        introspector = SchemaIntrospector()
        schema = introspector.introspect()

        assert "PARTY_TO" in schema
        assert "(Person)-[:PARTY_TO]->(Crime)" in schema


def test_schema_introspector_caches_result(mock_settings):
    with patch("core.schema_introspector.get_neo4j_client") as mock_get_client:
        mock_client = Mock()
        mock_client.query.side_effect = [
            [{"label": "Person", "properties": ["name"]}],  # nodes
            [],  # relationships
            [], [], [], [],  # property-value queries
        ]
        mock_get_client.return_value = mock_client

        from core.schema_introspector import SchemaIntrospector
        introspector = SchemaIntrospector()

        schema1 = introspector.introspect()
        first_count = mock_client.query.call_count
        schema2 = introspector.introspect()

        assert mock_client.query.call_count == first_count
        assert schema1 == schema2