# backend/core/graphrag_pipeline.py
"""
GraphRAG Pipeline - Orchestrates multi-retriever RAG for POLE crime investigation.

Replaces the legacy NL-to-Cypher pipeline with:
1. ToolsRetriever - LLM selects best retriever per query
2. GraphRAG - Generates answers from retrieved context
3. Graph data extraction - Preserves visualization support
"""
from typing import Dict, Any, Optional, List
import time
import logging

from neo4j import GraphDatabase, Driver
from neo4j.graph import Node, Relationship, Path

from neo4j_graphrag.generation import GraphRAG, RagTemplate
from neo4j_graphrag.llm import LLMInterface

from app.config import get_settings
from app.llm import get_groq_llm
from app.embedder import get_embedder
from core.retrievers import (
    build_text2cypher_retriever,
    build_vector_retriever,
    build_vector_cypher_retriever,
)
from core.prompts import get_rag_answer_template

logger = logging.getLogger(__name__)


class GraphRAGPipeline:
    """Orchestrates GraphRAG retrieval and answer generation"""

    def __init__(self):
        self.settings = get_settings()
        self._driver: Optional[Driver] = None
        self._llm: Optional[LLMInterface] = None
        self._text2cypher = None
        self._vector_retriever = None
        self._vector_cypher_retriever = None
        self._rag_instances: Dict[str, GraphRAG] = {}
        self._initialized = False

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USERNAME, self.settings.NEO4J_PASSWORD)
            )
        return self._driver

    @property
    def llm(self) -> LLMInterface:
        if self._llm is None:
            self._llm = get_groq_llm()
        return self._llm

    def initialize(self) -> None:
        """Initialize pipeline - build all retrievers and RAG instances"""
        if self._initialized:
            return

        logger.info("Initializing GraphRAG pipeline...")

        # Build retrievers
        embedder = get_embedder()

        self._text2cypher = build_text2cypher_retriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_database=self.settings.NEO4J_DATABASE,
        )

        self._vector_retriever = build_vector_retriever(
            driver=self.driver,
            embedder=embedder,
            index_name=self.settings.VECTOR_INDEX_NAME,
            neo4j_database=self.settings.NEO4J_DATABASE,
        )

        self._vector_cypher_retriever = build_vector_cypher_retriever(
            driver=self.driver,
            embedder=embedder,
            index_name=self.settings.VECTOR_INDEX_NAME,
            neo4j_database=self.settings.NEO4J_DATABASE,
        )

        # Build RAG template
        rag_template = RagTemplate(
            template=get_rag_answer_template(),
            expected_inputs=["query_text", "context"],
        )

        # Build RAG instances per retriever
        for name, retriever in [
            ("text2cypher", self._text2cypher),
            ("vector", self._vector_retriever),
            ("vector_cypher", self._vector_cypher_retriever),
        ]:
            # For text2cypher with retry wrapper, use _build_retriever for RAG
            if name == "text2cypher":
                base_retriever = retriever._build_retriever()
                self._rag_instances[name] = GraphRAG(
                    retriever=base_retriever,
                    llm=self.llm,
                    prompt_template=rag_template,
                )
            else:
                self._rag_instances[name] = GraphRAG(
                    retriever=retriever,
                    llm=self.llm,
                    prompt_template=rag_template,
                )

        self._initialized = True
        logger.info("GraphRAG pipeline initialized with 3 retrievers")

    def run(self, question: str) -> Dict[str, Any]:
        """
        Run GraphRAG pipeline with intelligent retriever selection.

        Strategy:
        1. Classify question type (structured vs semantic)
        2. Route to appropriate retriever
        3. If primary fails, fallback to alternative
        4. Generate answer from context

        Args:
            question: Natural language question

        Returns:
            Enriched response dict
        """
        start_time = time.time()
        logger.info(f"Running GraphRAG pipeline for: {question}")

        retriever_used = "unknown"
        retriever_context = []
        cypher = None
        results = []
        graph_data = {"nodes": [], "edges": []}
        error = None

        try:
            # Step 1: Classify and route
            retriever_name = self._classify_question(question)
            retriever_used = retriever_name
            logger.info(f"Selected retriever: {retriever_name}")

            # Step 2: Try primary retriever
            answer, cypher, results, graph_data, retriever_context = self._execute_retriever(
                retriever_name, question
            )

            # Step 3: Fallback if primary returns nothing useful
            if not answer or answer.strip() == "":
                fallback = self._get_fallback(retriever_name)
                if fallback:
                    logger.info(f"Primary retriever empty, falling back to: {fallback}")
                    retriever_used = f"{retriever_name} → {fallback}"
                    answer, cypher, results, graph_data, retriever_context = self._execute_retriever(
                        fallback, question
                    )

        except Exception as e:
            logger.error(f"GraphRAG pipeline error: {e}", exc_info=True)
            error = str(e)
            answer = f"Unable to process query: {str(e)}"

        elapsed_ms = int((time.time() - start_time) * 1000)

        response = {
            "question": question,
            "answer": answer or "No results found for your question.",
            "cypher": cypher or "",
            "results": results,
            "graph_data": graph_data,
            "attempts": 1,
            "execution_time_ms": elapsed_ms,
            "retriever_used": retriever_used,
            "retriever_context": retriever_context,
        }

        if error:
            response["error"] = error

        logger.info(f"GraphRAG pipeline completed in {elapsed_ms}ms (retriever: {retriever_used})")
        return response

    def _classify_question(self, question: str) -> str:
        """
        Classify question to select the best retriever.

        Heuristic-based routing:
        - Structured patterns (count, which, how many, list) → text2cypher
        - Semantic/exploratory (tell me about, describe, explain) → vector_cypher
        - Simple lookup (find, search) → vector
        """
        q = question.lower().strip()

        # Structured query patterns → Text2Cypher
        structured_patterns = [
            "how many", "count", "total",
            "which area", "which officer", "which person",
            "top ", "most ", "least ", "average",
            "repeat offender", "connected to each other",
            "network", "linked", "relationship between",
            "calls between", "phone", "communication",
            "investigated by", "party to",
        ]
        for pattern in structured_patterns:
            if pattern in q:
                return "text2cypher"

        # Semantic/exploratory patterns → VectorCypher (richest context)
        semantic_patterns = [
            "tell me about", "describe", "explain", "summarize",
            "what do you know", "overview", "insight",
            "similar to", "like", "related to",
            "what happened", "what kind",
        ]
        for pattern in semantic_patterns:
            if pattern in q:
                return "vector_cypher"

        # Questions starting with who/what/where/when → Text2Cypher
        if q.startswith(("who ", "where ", "when ")):
            return "text2cypher"

        # Short queries or keyword-like → vector search
        if len(q.split()) <= 4:
            return "vector"

        # Default to vector_cypher for best context
        return "vector_cypher"

    def _execute_retriever(
        self, retriever_name: str, question: str
    ) -> tuple:
        """Execute a specific retriever and return structured results."""
        answer = ""
        cypher = None
        results = []
        graph_data = {"nodes": [], "edges": []}
        context_items = []

        try:
            if retriever_name == "text2cypher":
                # Use retry wrapper for Text2Cypher (handles retries on
                # syntax errors and empty results).  The wrapper calls the
                # underlying Text2CypherRetriever.search() which already
                # generates Cypher via the LLM, runs it, and returns results.
                retriever_result = self._text2cypher.search(query_text=question)
                context_items = [item.content for item in retriever_result.items]

                # Try to extract Cypher from the result metadata
                for item in retriever_result.items:
                    if hasattr(item, 'metadata') and item.metadata:
                        cypher = item.metadata.get("cypher", cypher)

                # Generate answer from the already-retrieved context.
                # We use the LLM directly instead of GraphRAG.search() to
                # avoid a redundant second retriever call (Text2Cypher
                # doesn't accept top_k and would re-generate Cypher).
                if context_items:
                    from core.prompts import get_rag_answer_template
                    template = get_rag_answer_template()
                    context_str = "\n\n".join(context_items)
                    prompt = template.replace("{query_text}", question).replace("{context}", context_str)
                    llm_response = self.llm.invoke(prompt)
                    answer = llm_response.content

                # Build results from context
                results = [{"context": ctx} for ctx in context_items]

            else:
                # Vector or VectorCypher retriever
                rag = self._rag_instances.get(retriever_name)
                if rag:
                    rag_result = rag.search(
                        query_text=question,
                        retriever_config={"top_k": self.settings.GRAPHRAG_TOP_K},
                        return_context=True,
                    )
                    answer = rag_result.answer
                    if hasattr(rag_result, 'retriever_result') and rag_result.retriever_result:
                        context_items = [
                            item.content for item in rag_result.retriever_result.items
                        ]
                        results = [{"context": ctx} for ctx in context_items]

                        # Extract graph data from metadata
                        graph_data = self._extract_graph_data_from_context(
                            rag_result.retriever_result.items
                        )

        except Exception as e:
            logger.error(f"Retriever '{retriever_name}' failed: {e}", exc_info=True)
            raise

        return answer, cypher, results, graph_data, context_items

    def _get_fallback(self, primary: str) -> Optional[str]:
        """Get fallback retriever for a given primary."""
        fallbacks = {
            "text2cypher": "vector_cypher",
            "vector": "vector_cypher",
            "vector_cypher": "text2cypher",
        }
        return fallbacks.get(primary)

    def _extract_graph_data_from_context(self, items: list) -> Dict[str, list]:
        """
        Extract graph visualization data from retriever result items.

        For VectorCypherRetriever results, parse metadata to build
        nodes and edges for frontend visualization.
        """
        nodes_dict = {}
        edges = []

        for i, item in enumerate(items):
            if not hasattr(item, 'metadata') or not item.metadata:
                continue

            meta = item.metadata
            crime_id = meta.get("crime_id", f"crime_{i}")
            crime_type = meta.get("crime_type", "Crime")
            area = meta.get("area")

            # Add crime node
            node_id = str(crime_id)
            if node_id not in nodes_dict:
                nodes_dict[node_id] = {
                    "id": node_id,
                    "label": "Crime",
                    "properties": {
                        "id": crime_id,
                        "type": crime_type,
                    }
                }

            # Add area node if present
            if area:
                area_id = f"area_{area}"
                if area_id not in nodes_dict:
                    nodes_dict[area_id] = {
                        "id": area_id,
                        "label": "AREA",
                        "properties": {"areaCode": area}
                    }
                edges.append({
                    "source": node_id,
                    "target": area_id,
                    "relationship": "OCCURRED_IN",
                    "properties": {}
                })

        return {
            "nodes": list(nodes_dict.values())[:100],
            "edges": edges[:100],
        }

    def close(self):
        """Close Neo4j driver"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j driver closed")


# ──── Singleton ─────────────────────────────────────────

_graphrag_pipeline: Optional[GraphRAGPipeline] = None


def get_graphrag_pipeline() -> GraphRAGPipeline:
    """Get or create GraphRAG pipeline singleton"""
    global _graphrag_pipeline
    if _graphrag_pipeline is None:
        _graphrag_pipeline = GraphRAGPipeline()
    return _graphrag_pipeline
