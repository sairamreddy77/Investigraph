# backend/app/llm.py
"""LLM client wrappers for both legacy pipeline and neo4j-graphrag"""
from typing import List, Optional, Union
from groq import Groq
import logging

from neo4j_graphrag.llm import LLMInterface, LLMResponse
from neo4j_graphrag.types import LLMMessage
from app.config import get_settings

logger = logging.getLogger(__name__)


class GroqLLM(LLMInterface):
    """Groq LLM implementing neo4j-graphrag's LLMInterface"""

    def __init__(self, model_name: str = "llama-3.3-70b-versatile", model_params: Optional[dict] = None):
        settings = get_settings()
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model_name = model_name
        self.model_params = model_params or {}

    def invoke(
        self,
        input: str,
        message_history: Optional[Union[List[LLMMessage], "MessageHistory"]] = None,
        system_instruction: Optional[str] = None,
    ) -> LLMResponse:
        """
        Synchronous LLM invocation implementing LLMInterface.

        Args:
            input: The full prompt string
            message_history: Optional prior messages for multi-turn context
            system_instruction: Optional system message override

        Returns:
            LLMResponse with generated content
        """
        try:
            temperature = self.model_params.get("temperature", 0)
            max_tokens = self.model_params.get("max_tokens", 4096)

            messages = []

            # Add system instruction if provided
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})

            # Add message history if provided
            if message_history:
                if hasattr(message_history, 'messages'):
                    # MessageHistory object
                    history_list = message_history.messages
                else:
                    history_list = message_history
                for msg in history_list:
                    if isinstance(msg, dict):
                        messages.append(msg)
                    else:
                        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

            # Add the current input
            messages.append({"role": "user", "content": input})

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            return LLMResponse(content=content)
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    async def ainvoke(
        self,
        input: str,
        message_history: Optional[Union[List[LLMMessage], "MessageHistory"]] = None,
        system_instruction: Optional[str] = None,
    ) -> LLMResponse:
        """Async invocation (delegates to sync for Groq SDK)"""
        return self.invoke(input, message_history=message_history, system_instruction=system_instruction)


# ──── Singletons ────────────────────────────────────────

_groq_llm: Optional[GroqLLM] = None


def get_groq_llm() -> GroqLLM:
    """Get or create GroqLLM singleton (neo4j-graphrag compatible)"""
    global _groq_llm
    if _groq_llm is None:
        _groq_llm = GroqLLM(
            model_name="llama-3.3-70b-versatile",
            model_params={"temperature": 0, "max_tokens": 4096}
        )
    return _groq_llm


# ──── Legacy GroqClient (kept for backward compat during migration) ────

class GroqClient:
    """Legacy Groq LLM client wrapper - used by old pipeline"""

    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Get or create legacy Groq client singleton"""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
