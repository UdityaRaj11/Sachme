from typing import Optional
from app.models.content import NormalizedContent, ContentSummary
from app.services.ai.provider import BaseAIProvider
from app.core.logging import logger

class ContentSummarizer:
    """Summarizes extracted multimodal content across visual, spoken, and text modalities."""

    def __init__(self, ai_provider: BaseAIProvider):
        self.ai = ai_provider

    async def summarize(self, content: NormalizedContent) -> ContentSummary:
        content_parts = []
        if content.raw_text:
            content_parts.append(content.raw_text)
        if content.transcript:
            content_parts.append(content.transcript)
        if content.ocr_text:
            content_parts.append(content.ocr_text)

        combined_text = "\n\n".join(content_parts).strip()
        if not combined_text and content.title:
            combined_text = content.title
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
