# backend/core/pipeline.py
from typing import Dict, Any
import time
import logging

from core.cypher_generator import get_cypher_generator
from core.query_executor import get_query_executor
from core.answer_generator import get_answer_generator
from core.schema_introspector import get_schema_introspector
from core.few_shot_loader import get_few_shot_loader

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates 3-step NL-to-Cypher pipeline"""

    def __init__(self):
        self.cypher_generator = get_cypher_generator()
        self.query_executor = get_query_executor()
        self.answer_generator = get_answer_generator()
        self.schema_introspector = get_schema_introspector()
        self.few_shot_loader = get_few_shot_loader()
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize pipeline by caching schema and examples
        Should be called once at application startup
        """
        if self._initialized:
            return

        logger.info("Initializing pipeline...")

        # Trigger schema introspection (cached)
        self.schema_introspector.introspect()

        # Load few-shot examples (cached)
        self.few_shot_loader.load()

        self._initialized = True
        logger.info("Pipeline initialization complete")

    def run(self, question: str) -> Dict[str, Any]:
        """
        Run complete NL-to-Cypher pipeline

        Args:
            question: Natural language question

        Returns:
            Dict with answer, cypher, results, and metadata
        """
        start_time = time.time()

        logger.info(f"Running pipeline for question: {question}")

        try:
            # Step 1: Generate Cypher
            cypher = self.cypher_generator.generate(question)

            # Step 2: Execute with retry
            execution_result = self.query_executor.execute(cypher, question)

            # Step 3: Generate answer
            if execution_result.get("error"):
                # Query failed - use error as answer
                answer = f"Unable to process query: {execution_result['error']}"
            else:
                answer = self.answer_generator.generate(
                    question=question,
                    cypher=execution_result["cypher"],
                    results=execution_result["results"]
                )

            # Build response
            elapsed_ms = int((time.time() - start_time) * 1000)

            response = {
                "question": question,
                "answer": answer,
                "cypher": execution_result["cypher"],
                "results": execution_result["results"],
                "graph_data": execution_result.get("graph_data", {"nodes": [], "edges": []}),
                "attempts": execution_result["attempts"],
                "execution_time_ms": elapsed_ms
            }

            if execution_result.get("error"):
                response["error"] = execution_result["error"]

            logger.info(f"Pipeline completed in {elapsed_ms}ms")
            return response

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "question": question,
                "answer": f"An error occurred: {str(e)}",
                "cypher": "",
                "results": [],
                "graph_data": {"nodes": [], "edges": []},
                "attempts": 1,
                "execution_time_ms": elapsed_ms,
                "error": str(e)
            }


# Global singleton
_pipeline = None


def get_pipeline() -> Pipeline:
    """Get or create pipeline singleton"""
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline
