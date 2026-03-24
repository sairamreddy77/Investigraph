from typing import List, Dict, Optional
import yaml
import os
import logging

logger = logging.getLogger(__name__)


class FewShotLoader:
    """Loads and formats few-shot examples for LLM prompts"""

    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            # Default path relative to this file
            base_dir = os.path.dirname(os.path.dirname(__file__))
            file_path = os.path.join(base_dir, "data", "few_shot_examples.yaml")
        self.file_path = file_path
        self._examples_cache: Optional[List[Dict[str, str]]] = None

    def load_examples(self) -> List[Dict[str, str]]:
        """Load examples from YAML file"""
        if self._examples_cache is not None:
            return self._examples_cache

        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self._examples_cache = data.get('examples', [])
        logger.info(f"Loaded {len(self._examples_cache)} few-shot examples")
        return self._examples_cache

    def format_for_prompt(self) -> str:
        """Format examples for LLM prompt"""
        examples = self.load_examples()

        formatted = []
        for i, ex in enumerate(examples, 1):
            formatted.append(f"Example {i}:")
            formatted.append(f"Question: {ex['question']}")
            formatted.append(f"Cypher: {ex['cypher']}")
            formatted.append("")

        return "\n".join(formatted)

    def get_examples(self) -> List[Dict[str, str]]:
        """Get examples (public API)"""
        return self.load_examples()

    def load(self) -> None:
        """Load and cache examples (called during initialization)"""
        self.load_examples()


# Global singleton
_few_shot_loader: Optional[FewShotLoader] = None


def get_few_shot_loader() -> FewShotLoader:
    """Get or create few-shot loader singleton"""
    global _few_shot_loader
    if _few_shot_loader is None:
        _few_shot_loader = FewShotLoader()
    return _few_shot_loader
