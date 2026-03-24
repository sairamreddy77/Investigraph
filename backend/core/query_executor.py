# backend/core/query_executor.py
from typing import Dict, List, Any, Optional
import logging
from neo4j.exceptions import CypherSyntaxError, ClientError

from app.database import get_neo4j_client
from core.cypher_generator import get_cypher_generator

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class QueryExecutor:
    """Executes Cypher queries with retry logic"""

    def __init__(self):
        self.neo4j_client = get_neo4j_client()
        self.cypher_generator = get_cypher_generator()

    def execute(self, cypher: str, question: str) -> Dict[str, Any]:
        """
        Execute Cypher query with retry on errors

        Args:
            cypher: Initial Cypher query
            question: Original user question (for retry context)

        Returns:
            Dict with results, cypher, attempts, and optional error
        """
        for attempt in range(1, MAX_RETRIES + 1):
            logger.info(f"Attempt {attempt}/{MAX_RETRIES}: Executing query")

            try:
                # Execute query
                results = self.neo4j_client.query(cypher)

                # Success with results
                if results:
                    logger.info(f"Query succeeded with {len(results)} results")
                    return {
                        "results": results,
                        "cypher": cypher,
                        "attempts": attempt,
                        "graph_data": self._extract_graph_data(results)
                    }

                # Empty results - reformulate if retries left
                if attempt < MAX_RETRIES:
                    logger.warning("Query returned 0 results, reformulating...")
                    error_context = self._build_empty_results_context(cypher)
                    cypher = self.cypher_generator.generate(question, error_context)
                else:
                    logger.warning("No results after max retries")
                    return {
                        "results": [],
                        "cypher": cypher,
                        "attempts": attempt,
                        "error": "No results found after 3 attempts",
                        "graph_data": {"nodes": [], "edges": []}
                    }

            except (CypherSyntaxError, ClientError) as e:
                # Syntax/client error - self-correct if retries left
                logger.error(f"Query error: {e}")

                if attempt < MAX_RETRIES:
                    error_context = self._build_syntax_error_context(cypher, str(e))
                    cypher = self.cypher_generator.generate(question, error_context)
                else:
                    return {
                        "results": [],
                        "cypher": cypher,
                        "attempts": attempt,
                        "error": f"Syntax error: {str(e)}",
                        "graph_data": {"nodes": [], "edges": []}
                    }

            except Exception as e:
                # Other errors (connection, etc) - non-retryable
                logger.error(f"Execution error: {e}")
                return {
                    "results": [],
                    "cypher": cypher,
                    "attempts": attempt,
                    "error": f"Execution error: {str(e)}",
                    "graph_data": {"nodes": [], "edges": []}
                }

        # Should never reach here
        return {
            "results": [],
            "cypher": cypher,
            "attempts": MAX_RETRIES,
            "error": "Max retries exceeded",
            "graph_data": {"nodes": [], "edges": []}
        }

    def _build_empty_results_context(self, cypher: str) -> str:
        """Build error context for empty results"""
        return f"""Previous query returned 0 results:
{cypher}

Suggestions:
- Try relaxing WHERE filters (remove date constraints, age filters)
- Use CONTAINS instead of exact matches
- Check relationship direction matches schema
- Verify property names match schema exactly
- Consider that PARTY_TO relationships are sparse (only 55 records)
"""

    def _build_syntax_error_context(self, cypher: str, error: str) -> str:
        """Build error context for syntax errors"""
        return f"""Previous query failed with syntax error:
Error: {error}
Failed Query:
{cypher}

Please fix the syntax error and generate a corrected query.
Common issues:
- Invalid node labels or relationship types
- Incorrect Cypher syntax
- Missing or extra parentheses/brackets
"""

    def _extract_graph_data(self, results: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Extract nodes and edges from results for graph visualization

        Args:
            results: Query results

        Returns:
            Dict with 'nodes' and 'edges' lists
        """
        nodes = []
        edges = []
        seen_nodes = set()

        for record in results:
            for key, value in record.items():
                # Check if value is a node
                if isinstance(value, dict) and "labels" in str(type(value)):
                    node_id = value.get("id", value.get("elementId", key))
                    if node_id not in seen_nodes:
                        nodes.append({
                            "id": str(node_id),
                            "label": value.get("labels", ["Unknown"])[0] if "labels" in str(type(value)) else "Node",
                            "properties": {k: v for k, v in value.items() if k not in ["id", "elementId"]}
                        })
                        seen_nodes.add(node_id)

        # Note: Edge extraction requires relationship objects in results
        # This is a simplified version - full implementation would parse relationships

        return {
            "nodes": nodes[:100],  # Limit to 100 nodes for performance
            "edges": edges[:100]
        }


# Global singleton
_query_executor: Optional['QueryExecutor'] = None


def get_query_executor() -> QueryExecutor:
    """Get or create query executor singleton"""
    global _query_executor
    if _query_executor is None:
        _query_executor = QueryExecutor()
    return _query_executor
