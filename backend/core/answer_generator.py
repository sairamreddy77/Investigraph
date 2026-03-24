# backend/core/answer_generator.py
import logging
from typing import Optional, List, Dict, Any

from app.llm import get_groq_client

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Generates natural language answers from Cypher query results"""

    def __init__(self):
        self.llm = get_groq_client()

    def generate(
        self,
        question: str,
        cypher: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a natural language answer from query results

        Args:
            question: Original natural language question
            cypher: The Cypher query that was executed
            results: Query results as list of dictionaries

        Returns:
            Natural language answer string
        """
        logger.info(f"Generating answer for question: {question}")

        # Handle empty results
        if not results:
            return self._generate_empty_result_answer(question)

        # Build prompt and generate answer
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(question, cypher, results)

        answer = self.llm.chat_completion(system_prompt, user_prompt)

        logger.info(f"Generated answer: {answer[:100]}...")
        return answer

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for answer generation

        Returns:
            System prompt string
        """
        return """You are a crime investigation analyst interpreting database query results.

Your job is to:
- Give a clear, direct answer to the user's question
- Format lists and tables when there are multiple results
- Be concise - analysts need quick answers
- Do not mention Cypher, database internals, or technical details unless specifically asked
- If the data shows interesting patterns, briefly mention them

Rules:
- Start with a direct answer to the question
- Use bullet points or tables for multiple results
- Keep responses under 200 words unless there's a lot of data to present
- Be factual and precise - this is crime investigation data"""

    def _build_user_prompt(
        self,
        question: str,
        cypher: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Build the user prompt with question, query, and results

        Args:
            question: Original question
            cypher: Executed Cypher query
            results: Query results

        Returns:
            User prompt string
        """
        # Format results for readability
        formatted_results = self._format_results(results)

        return f"""Question: {question}

Query Used:
{cypher}

Results:
{formatted_results}

Please provide a clear, concise answer to the question based on these results."""

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results into a readable string representation

        Args:
            results: Query results

        Returns:
            Formatted results string
        """
        if not results:
            return "No results found"

        # If single result with single value (e.g., count)
        if len(results) == 1 and len(results[0]) == 1:
            key = list(results[0].keys())[0]
            value = results[0][key]
            return f"{key}: {value}"

        # For multiple results or multiple columns, format as table
        formatted = []
        for i, row in enumerate(results[:50], 1):  # Limit to 50 rows
            row_str = ", ".join(f"{k}: {v}" for k, v in row.items())
            formatted.append(f"{i}. {row_str}")

        result_text = "\n".join(formatted)

        # Add note if results were truncated
        if len(results) > 50:
            result_text += f"\n... ({len(results) - 50} more results not shown)"

        return result_text

    def _generate_empty_result_answer(self, question: str) -> str:
        """
        Generate a helpful response for empty results

        Args:
            question: Original question

        Returns:
            Empty result response string
        """
        return (
            f"No results were found for your question: '{question}'. "
            "This could mean:\n"
            "- The data you're looking for doesn't exist in the database\n"
            "- The search criteria might be too specific\n"
            "- Try rephrasing your question or using broader search terms"
        )


# Global singleton
_answer_generator: Optional[AnswerGenerator] = None


def get_answer_generator() -> AnswerGenerator:
    """Get or create answer generator singleton"""
    global _answer_generator
    if _answer_generator is None:
        _answer_generator = AnswerGenerator()
    return _answer_generator
