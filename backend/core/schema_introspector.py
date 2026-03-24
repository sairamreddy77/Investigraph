# backend/core/schema_introspector.py
from typing import Dict, List, Any, Optional
import logging

from app.database import get_neo4j_client

logger = logging.getLogger(__name__)


class SchemaIntrospector:
    """Introspects Neo4j schema and caches results"""

    def __init__(self):
        self.client = get_neo4j_client()
        self._schema_cache: Optional[str] = None

    def introspect(self) -> str:
        """
        Fetch complete schema from Neo4j and format for LLM prompt

        Returns:
            Formatted schema text with nodes, relationships, property values
        """
        if self._schema_cache is not None:
            return self._schema_cache

        logger.info("Introspecting Neo4j schema...")

        nodes = self._fetch_node_labels()
        relationships = self._fetch_relationships()
        property_values = self._fetch_property_values()

        schema_text = self._format_schema(nodes, relationships, property_values)
        self._schema_cache = schema_text

        logger.info("Schema introspection complete")
        return schema_text

    def _fetch_node_labels(self) -> Dict[str, List[str]]:
        """Fetch all node labels with their properties"""
        query = """
        CALL db.labels() YIELD label
        CALL apoc.meta.nodeTypeProperties() YIELD nodeType, propertyName
        WHERE nodeType = ':' + label
        RETURN label, collect(propertyName) AS properties
        """

        # Fallback if APOC not available
        fallback_query = """
        MATCH (n)
        WITH DISTINCT labels(n)[0] AS label, keys(n) AS props
        RETURN label, props AS properties
        LIMIT 100
        """

        try:
            results = self.client.query(query)
        except Exception:
            logger.warning("APOC not available, using fallback query")
            results = self.client.query(fallback_query)

        nodes = {}
        for record in results:
            label = record.get("label")
            properties = record.get("properties", [])
            if label and label not in ["", None]:
                nodes[label] = list(set(properties)) if properties else []

        return nodes

    def _fetch_relationships(self) -> List[Dict[str, str]]:
        """Fetch all relationship types with start/end nodes"""
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        MATCH ()-[r]-()
        WHERE type(r) = relationshipType
        WITH relationshipType,
             labels(startNode(r))[0] AS startLabel,
             labels(endNode(r))[0] AS endLabel
        RETURN DISTINCT relationshipType AS type,
               startLabel AS start,
               endLabel AS end
        LIMIT 100
        """

        results = self.client.query(query)

        relationships = []
        for record in results:
            rel_type = record.get("type")
            start = record.get("start")
            end = record.get("end")
            if all([rel_type, start, end]):
                relationships.append({
                    "type": rel_type,
                    "start": start,
                    "end": end
                })

        return relationships

    def _fetch_property_values(self) -> Dict[str, List[str]]:
        """Fetch categorical property values for filtering"""
        property_values = {}

        # Crime types
        query = "MATCH (c:Crime) RETURN DISTINCT c.type AS val ORDER BY val LIMIT 50"
        try:
            results = self.client.query(query)
            values = [r["val"] for r in results if r["val"]]
            if values:
                property_values["Crime.type"] = values
        except Exception as e:
            logger.warning(f"Failed to fetch Crime.type values: {e}")

        # Crime outcomes
        query = "MATCH (c:Crime) RETURN DISTINCT c.last_outcome AS val ORDER BY val LIMIT 50"
        try:
            results = self.client.query(query)
            values = [r["val"] for r in results if r["val"]]
            if values:
                property_values["Crime.last_outcome"] = values
        except Exception as e:
            logger.warning(f"Failed to fetch Crime.last_outcome values: {e}")

        # Officer ranks
        query = "MATCH (o:Officer) RETURN DISTINCT o.rank AS val ORDER BY val LIMIT 50"
        try:
            results = self.client.query(query)
            values = [r["val"] for r in results if r["val"]]
            if values:
                property_values["Officer.rank"] = values
        except Exception as e:
            logger.warning(f"Failed to fetch Officer.rank values: {e}")

        # Vehicle makes
        query = "MATCH (v:Vehicle) RETURN DISTINCT v.make AS val ORDER BY val LIMIT 50"
        try:
            results = self.client.query(query)
            values = [r["val"] for r in results if r["val"]]
            if values:
                property_values["Vehicle.make"] = values
        except Exception as e:
            logger.warning(f"Failed to fetch Vehicle.make values: {e}")

        return property_values

    def _format_schema(
        self,
        nodes: Dict[str, List[str]],
        relationships: List[Dict[str, str]],
        property_values: Dict[str, List[str]]
    ) -> str:
        """Format schema into text for LLM prompt"""
        lines = []

        # Nodes section
        lines.append("NODES:")
        for label, properties in sorted(nodes.items()):
            props_str = ", ".join([f"{p}: string" for p in properties])
            lines.append(f"  {label}({props_str})")
        lines.append("")

        # Relationships section
        lines.append("RELATIONSHIPS:")
        for rel in relationships:
            lines.append(f"  ({rel['start']})-[:{rel['type']}]->({rel['end']})")
        lines.append("")

        # Property values section
        lines.append("PROPERTY VALUES:")
        for prop, values in sorted(property_values.items()):
            values_str = ", ".join([f'"{v}"' for v in values[:20]])  # Limit to 20
            lines.append(f"  {prop}: [{values_str}]")
        lines.append("")

        # Data limitations section
        lines.append("DATA LIMITATIONS:")
        lines.append("  • Person.age: Not available (field is empty)")
        lines.append("  • Crime.note and Crime.charge: Rarely populated (99% empty)")
        lines.append("  • PARTY_TO relationships: Sparse (only 55 records for 28,762 crimes)")
        lines.append("  • Object data: Minimal (7 records)")

        return "\n".join(lines)

    def get_schema_text(self) -> str:
        """Get formatted schema text (public API)"""
        return self.introspect()

    def get_property_values(self) -> Dict[str, List[str]]:
        """Get property values (public API)"""
        # Trigger introspection if not cached
        if self._schema_cache is None:
            self.introspect()
        return self._fetch_property_values()


# Global singleton
_schema_introspector: Optional[SchemaIntrospector] = None


def get_schema_introspector() -> SchemaIntrospector:
    """Get or create schema introspector singleton"""
    global _schema_introspector
    if _schema_introspector is None:
        _schema_introspector = SchemaIntrospector()
    return _schema_introspector
