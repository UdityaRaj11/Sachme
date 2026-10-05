from typing import Optional
from app.services.extraction.base import BaseExtractor
from app.models.content import (
    ClassificationResult,
    NormalizedContent,
    ContentSummary,
    Platform,
    ContentType,
)

class DirectTextExtractor(BaseExtractor):
    """Processes directly submitted text payloads without requiring a URL."""

    def __init__(self, raw_text: str):
        self.raw_text = raw_text

    async def extract(self, classification: ClassificationResult) -> NormalizedContent:
        text = self.raw_text.strip()
        preview = text[:250].replace("\n", " ") + "..." if len(text) > 250 else text

        return NormalizedContent(
            url="text://direct-input",
            platform=Platform.TEXT_DIRECT,
            content_type=ContentType.TEXT,
            language="en",
            title="Direct User Text Submission",
            author="User",
            published_date=None,
            raw_text=text,
            transcript=None,
            ocr_text=None,
            visual_description=None,
            metadata={"character_length": len(text)},
            summary=ContentSummary(
                visual=None,
                text=preview,
                key_points=[line.strip() for line in text.split("\n") if len(line.strip()) > 15][:3],
            ),
        )
