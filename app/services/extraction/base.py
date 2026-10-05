from abc import ABC, abstractmethod
from typing import Optional
from app.models.content import ClassificationResult, NormalizedContent

class BaseExtractor(ABC):
    """Abstract interface for all content extraction pipelines."""

    @abstractmethod
    async def extract(self, classification: ClassificationResult) -> NormalizedContent:
        """
        Extracts content from target source and normalizes it into a standard NormalizedContent object.
        Must never invent missing content. Clearly distinguishes extracted facts from inferred context.
        """
        pass
