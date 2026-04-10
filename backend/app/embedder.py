# backend/app/embedder.py
"""SentenceTransformer embedder singleton for GraphRAG vector search"""
from typing import Optional
import logging

from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from app.config import get_settings

logger = logging.getLogger(__name__)

# Global singleton
_embedder: Optional[SentenceTransformerEmbeddings] = None


def get_embedder() -> SentenceTransformerEmbeddings:
    """Get or create SentenceTransformer embedder singleton"""
    global _embedder
    if _embedder is None:
        settings = get_settings()
        logger.info(f"Initializing SentenceTransformer embedder: {settings.EMBEDDING_MODEL}")
        _embedder = SentenceTransformerEmbeddings(
            model=settings.EMBEDDING_MODEL
        )
        logger.info("Embedder initialized")
    return _embedder
