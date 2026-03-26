# backend/core/cypher_generator.py
import logging
import re
from typing import Optional

from app.llm import get_groq_client
from core.schema_introspector import get_schema_introspector
from core.few_shot_loader import get_few_shot_loader

logger = logging.getLogger(__name__)


class CypherGenerator:
    """Generates Cypher queries from natural language questions"""

    def __init__(self):
        self.llm = get_groq_client()
        self.schema_introspector = get_schema_introspector()
        self.few_shot_loader = get_few_shot_loader()

    def generate(self, question: str, error_context: str = "") -> str:
        """
        Generate a Cypher query from a natural language question

        Args:
            question: Natural language question about the crime data
            error_context: Optional error context from a previous failed attempt

        Returns:
            Generated Cypher query as a string
        """
        logger.info(f"Generating Cypher for question: {question}")

        system_prompt = self._build_system_prompt(error_context)
        user_prompt = f"Question: {question}"

        cypher = self.llm.chat_completion(system_prompt, user_prompt)
        cypher = self._clean_cypher(cypher)

        logger.info(f"Generated Cypher: {cypher}")
        return cypher

    def _build_system_prompt(self, error_context: str = "") -> str:
        """
        Build the complete system prompt with schema, examples, and rules

        Args:
            error_context: Optional error message from previous attempt

        Returns:
            Complete system prompt for LLM
        """
        schema_text = self.schema_introspector.introspect()
        examples_text = self.few_shot_loader.format_for_prompt()

        prompt = f"""You are an expert Neo4j Cypher query generator for a POLE (Person, Object,
Location, Event) crime investigation knowledge graph.

═══ GRAPH SCHEMA ═══
{schema_text}

═══ EXAMPLE QUERIES ═══
{examples_text}

═══ RULES ═══
1. Use ONLY the node labels, relationships, and properties from the schema above.
2. Follow relationship directions EXACTLY as shown.
3. For string filtering, ALWAYS use: toLower(n.prop) CONTAINS 'value'
4. Use the EXACT property values from the "PROPERTY VALUES" section when possible.
5. Return ONLY the Cypher query. No explanations, no markdown fences.
6. Never generate MERGE, DELETE, SET, CREATE, DROP, or REMOVE statements.
7. For "who" questions → target Person nodes.
8. For count/most/least → use count(), ORDER BY, LIMIT.
9. When unsure about exact values, use CONTAINS for partial matching.
10. Always include meaningful RETURN aliases for readability.
11. Be aware of data limitations: Person.age is empty, Crime.note/charge are sparse.
12. Results will be automatically limited to 50 records for performance.
"""

        if error_context:
            prompt += f"\n═══ ERROR CONTEXT ═══\n{error_context}\n"
            prompt += "Please fix the query based on the error above.\n"

        return prompt

    def _clean_cypher(self, cypher: str) -> str:
        """
        Clean the generated Cypher by removing markdown fences and extra whitespace

        Args:
            cypher: Raw Cypher string from LLM

        Returns:
            Cleaned Cypher query
        """
        # Remove markdown code fences
        cypher = re.sub(r'^```(?:cypher)?\s*', '', cypher, flags=re.MULTILINE)
        cypher = re.sub(r'```\s*$', '', cypher, flags=re.MULTILINE)

        # Remove leading/trailing whitespace
        cypher = cypher.strip()

        # Add LIMIT 50 if not already present
        cypher = self._ensure_limit(cypher)

        return cypher

    def _ensure_limit(self, cypher: str) -> str:
        """
        Ensure query has LIMIT 50 to prevent excessive results

        Args:
            cypher: Cypher query

        Returns:
            Cypher query with LIMIT 50
        """
        # Check if LIMIT already exists (case-insensitive)
        if re.search(r'\bLIMIT\s+\d+', cypher, re.IGNORECASE):
            return cypher

        # Add LIMIT 50 at the end
        return f"{cypher}\nLIMIT 50"


# Global singleton
_cypher_generator: Optional[CypherGenerator] = None


def get_cypher_generator() -> CypherGenerator:
    """Get or create cypher generator singleton"""
    global _cypher_generator
    if _cypher_generator is None:
        _cypher_generator = CypherGenerator()
    return _cypher_generator
