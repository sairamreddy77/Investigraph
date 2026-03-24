# backend/app/llm.py
from typing import Optional
from groq import Groq
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq LLM client wrapper"""

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
        """
        Generate chat completion using Groq LLaMA 3.3 70B

        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: Sampling temperature (0 for deterministic)

        Returns:
            Generated text completion
        """
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


# Global client instance
_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Get or create Groq client singleton"""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client


def generate_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0
) -> str:
    """
    Convenience function for generating completions

    Args:
        system_prompt: System instructions
        user_prompt: User query
        temperature: Sampling temperature

    Returns:
        Generated text
    """
    client = get_groq_client()
    return client.chat_completion(system_prompt, user_prompt, temperature)
