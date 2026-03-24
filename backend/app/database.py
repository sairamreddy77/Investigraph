# backend/app/database.py
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Singleton Neo4j database client"""

    _instance: Optional['Neo4jClient'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.driver = None
            cls._instance.settings = get_settings()
        return cls._instance

    def connect(self) -> None:
        """Establish connection to Neo4j database"""
        if self.driver is not None:
            return

        try:
            self.driver = GraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USERNAME, self.settings.NEO4J_PASSWORD)
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.settings.NEO4J_URI}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def query(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return results

        Args:
            cypher: Cypher query string
            parameters: Query parameters (optional)

        Returns:
            List of result records as dictionaries
        """
        if self.driver is None:
            raise RuntimeError("Neo4j client not connected. Call connect() first.")

        if parameters is None:
            parameters = {}

        with self.driver.session(database=self.settings.NEO4J_DATABASE) as session:
            result = session.run(cypher, parameters)
            return result.data()

    def close(self) -> None:
        """Close Neo4j connection"""
        if self.driver is not None:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")


# Global singleton instance
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client singleton"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
        _neo4j_client.connect()
    return _neo4j_client
