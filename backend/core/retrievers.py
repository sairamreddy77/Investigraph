# backend/core/retrievers.py
"""
GraphRAG retrievers for POLE crime investigation knowledge graph.

Provides three retrieval strategies:
1. Text2CypherRetriever - structured queries via LLM-generated Cypher (with retry)
2. VectorRetriever - semantic search on node embeddings
3. VectorCypherRetriever - vector search + graph traversal for enriched context
"""
from typing import Optional, List
import logging
import re

from neo4j import Driver
from neo4j_graphrag.retrievers import (
    Text2CypherRetriever,
    VectorRetriever,
    VectorCypherRetriever,
)
from neo4j_graphrag.llm import LLMInterface
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.types import RetrieverResultItem

from core.schema_introspector import get_schema_introspector
from core.few_shot_loader import get_few_shot_loader
from core.prompts import (
    get_text2cypher_custom_prompt,
    format_text2cypher_examples,
)

logger = logging.getLogger(__name__)

MAX_CYPHER_RETRIES = 3


# ──── Text2Cypher with Retry Wrapper ────────────────────

class Text2CypherRetrieverWithRetry:
    """
    Wraps neo4j-graphrag's Text2CypherRetriever with self-healing retry logic.
    Preserves the retry behavior from the original query_executor.py.
    """

    def __init__(
        self,
        driver: Driver,
        llm: LLMInterface,
        neo4j_schema: str,
        examples: List[str],
        neo4j_database: str = "pole",
        custom_prompt: str = "",
    ):
        self.driver = driver
        self.llm = llm
        self.neo4j_schema = neo4j_schema
        self.examples = examples
        self.neo4j_database = neo4j_database
        self.custom_prompt = custom_prompt

    def _build_retriever(self, extra_instructions: str = "") -> Text2CypherRetriever:
        """Build a fresh Text2CypherRetriever (optionally with error context)"""
        prompt = self.custom_prompt
        if extra_instructions:
            prompt += f"\n\n═══ ERROR CONTEXT ═══\n{extra_instructions}\nPlease fix the query based on the error above.\n"

        return Text2CypherRetriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_schema=prompt + "\n\n" + self.neo4j_schema,
            examples=self.examples,
            neo4j_database=self.neo4j_database,
        )

    def search(self, query_text: str, **kwargs) -> "RetrieverResult":
        """
        Search with retry logic on Cypher errors.

        Attempts up to MAX_CYPHER_RETRIES times:
        - On syntax error: feeds error context back to LLM for self-correction
        - On empty results: relaxes prompt for broader search
        """
        last_error = None

        for attempt in range(1, MAX_CYPHER_RETRIES + 1):
            try:
                logger.info(f"Text2Cypher attempt {attempt}/{MAX_CYPHER_RETRIES}")

                if attempt == 1:
                    retriever = self._build_retriever()
                else:
                    retriever = self._build_retriever(extra_instructions=last_error)

                result = retriever.search(query_text=query_text, **kwargs)

                # Check for empty results
                if not result.items:
                    last_error = (
                        "Previous query returned 0 results. Try:\n"
                        "- Relaxing WHERE filters (remove date, age)\n"
                        "- Using CONTAINS instead of exact matches\n"
                        "- Checking relationship direction\n"
                        "- PARTY_TO relationships are sparse (only 55 records)\n"
                    )
                    if attempt < MAX_CYPHER_RETRIES:
                        logger.warning("Text2Cypher returned empty, retrying...")
                        continue

                logger.info(f"Text2Cypher succeeded with {len(result.items)} results")
                return result

            except Exception as e:
                last_error = f"Query failed with error: {str(e)}"
                logger.error(f"Text2Cypher attempt {attempt} failed: {e}")
                if attempt >= MAX_CYPHER_RETRIES:
                    raise

        raise RuntimeError("Text2Cypher max retries exceeded")

    def convert_to_tool(self, name: str, description: str):
        """Convert to tool for ToolsRetriever compatibility"""
        retriever = self._build_retriever()
        tool = retriever.convert_to_tool(name=name, description=description)
        # Patch the search to use our retry-enabled version
        # Note: ToolsRetriever calls the underlying retriever directly
        # so we override the search method on the base retriever
        retriever.search = self.search
        return tool


# ──── Factory Functions ─────────────────────────────────

def build_text2cypher_retriever(
    driver: Driver,
    llm: LLMInterface,
    neo4j_database: str = "pole",
) -> Text2CypherRetrieverWithRetry:
    """
    Build Text2CypherRetriever with schema, examples, and custom prompt.

    Uses:
    - SchemaIntrospector for live schema
    - FewShotLoader for all curated examples
    - Domain-specific POLE investigation prompt rules
    """
    schema_text = get_schema_introspector().introspect()
    raw_examples = get_few_shot_loader().get_examples()
    formatted_examples = format_text2cypher_examples(raw_examples)
    custom_prompt = get_text2cypher_custom_prompt()

    return Text2CypherRetrieverWithRetry(
        driver=driver,
        llm=llm,
        neo4j_schema=schema_text,
        examples=formatted_examples,
        neo4j_database=neo4j_database,
        custom_prompt=custom_prompt,
    )


def build_vector_retriever(
    driver: Driver,
    embedder: SentenceTransformerEmbeddings,
    index_name: str = "crime_vector_index",
    neo4j_database: str = "pole",
) -> VectorRetriever:
    """
    Build VectorRetriever for semantic search on Crime nodes.

    Crime nodes are the primary target for semantic search because
    they have the richest text content (type + last_outcome + note).
    """
    return VectorRetriever(
        driver=driver,
        index_name=index_name,
        embedder=embedder,
        neo4j_database=neo4j_database,
        return_properties=["id", "type", "date", "last_outcome", "note", "charge"],
    )


def build_vector_cypher_retriever(
    driver: Driver,
    embedder: SentenceTransformerEmbeddings,
    index_name: str = "crime_vector_index",
    neo4j_database: str = "pole",
) -> VectorCypherRetriever:
    """
    Build VectorCypherRetriever that enriches vector results with graph traversal.

    After finding semantically similar Crime nodes, traverses 1-2 hops to get:
    - People involved (PARTY_TO)
    - Location where it occurred (OCCURRED_AT)
    - Officer investigating (INVESTIGATED_BY)
    - Area information (LOCATION_IN_AREA)
    """
    retrieval_query = """
        WITH node AS crime, score
        OPTIONAL MATCH (p:Person)-[:PARTY_TO]->(crime)
        OPTIONAL MATCH (crime)-[:OCCURRED_AT]->(l:Location)
        OPTIONAL MATCH (l)-[:LOCATION_IN_AREA]->(a:AREA)
        OPTIONAL MATCH (crime)-[:INVESTIGATED_BY]->(o:Officer)
        RETURN crime.id AS crime_id,
               crime.type AS crime_type,
               crime.date AS crime_date,
               crime.last_outcome AS outcome,
               collect(DISTINCT p.name + ' ' + coalesce(p.surname, '')) AS people_involved,
               l.address AS location,
               l.postcode AS postcode,
               a.areaCode AS area,
               collect(DISTINCT o.name + ' (' + coalesce(o.rank, '') + ')') AS officers,
               score
    """

    def result_formatter(record) -> RetrieverResultItem:
        people = [p for p in record.get("people_involved", []) if p and p.strip()]
        officers = [o for o in record.get("officers", []) if o and o.strip()]

        content_parts = [
            f"Crime: {record.get('crime_type', 'Unknown')} (ID: {record.get('crime_id', 'N/A')})",
            f"Date: {record.get('crime_date', 'Unknown')}",
            f"Outcome: {record.get('outcome', 'Unknown')}",
        ]
        if record.get("location"):
            content_parts.append(f"Location: {record.get('location')}, {record.get('postcode', '')}")
        if record.get("area"):
            content_parts.append(f"Area: {record.get('area')}")
        if people:
            content_parts.append(f"People involved: {', '.join(people)}")
        if officers:
            content_parts.append(f"Investigating officers: {', '.join(officers)}")

        return RetrieverResultItem(
            content="\n".join(content_parts),
            metadata={
                "crime_id": record.get("crime_id"),
                "crime_type": record.get("crime_type"),
                "area": record.get("area"),
                "score": record.get("score"),
            },
        )

    return VectorCypherRetriever(
        driver=driver,
        index_name=index_name,
        retrieval_query=retrieval_query,
        result_formatter=result_formatter,
        embedder=embedder,
        neo4j_database=neo4j_database,
    )
