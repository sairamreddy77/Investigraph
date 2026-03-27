from typing import List, Dict, Optional
import yaml
import os
import logging

logger = logging.getLogger(__name__)


class CaseStudyLoader:
    """Loads and formats investigation case studies"""

    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            file_path = os.path.join(base_dir, "data", "case_studies.yaml")
        self.file_path = file_path
        self._cache: Optional[List[Dict]] = None

    def load(self) -> List[Dict]:
        """Load case studies from YAML file"""
        if self._cache is not None:
            return self._cache

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self._cache = data.get('case_studies', [])
            logger.info(f"Loaded {len(self._cache)} case studies")
        except Exception as e:
            logger.error(f"Failed to load case studies: {e}")
            self._cache = []

        return self._cache

    def get_case_studies(self) -> List[Dict]:
        """Public API to get case studies"""
        return self.load()

    def get_by_id(self, case_study_id: str) -> Optional[Dict]:
        """Get a specific case study by ID"""
        case_studies = self.load()
        for cs in case_studies:
            if cs.get('id') == case_study_id:
                return cs
        return None

    def get_by_category(self, category: str) -> List[Dict]:
        """Get case studies by category"""
        case_studies = self.load()
        return [cs for cs in case_studies if cs.get('category', '').lower() == category.lower()]


# Global singleton
_case_study_loader: Optional[CaseStudyLoader] = None


def get_case_study_loader() -> CaseStudyLoader:
    """Get or create case study loader singleton"""
    global _case_study_loader
    if _case_study_loader is None:
        _case_study_loader = CaseStudyLoader()
    return _case_study_loader
