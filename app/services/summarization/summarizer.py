from typing import Optional
from app.models.content import NormalizedContent, ContentSummary
from app.services.ai.provider import BaseAIProvider
from app.core.logging import logger

class ContentSummarizer:
    """Summarizes extracted multimodal content across visual, spoken, and text modalities."""

    def __init__(self, ai_provider: BaseAIProvider):
        self.ai = ai_provider

    async def summarize(self, content: NormalizedContent) -> ContentSummary:
        combined_text = content.raw_text or content.transcript or content.ocr_text or ""
        visual_info = content.visual_description

        if not combined_text and not visual_info:
            return ContentSummary(
                visual=None,
                text="No extractable text or visual elements were present in the content.",
                key_points=[],
            )

        logger.info(f"Generating summary for content: {content.url}")
        summary = await self.ai.summarize_content(text=combined_text, visual_context=visual_info)
        return summary
