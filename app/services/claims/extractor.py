from typing import List, Tuple
from app.models.content import NormalizedContent
from app.models.claims import Claim, ClaimType
from app.services.ai.provider import BaseAIProvider
from app.core.logging import logger

class ClaimExtractor:
    """
    Extracts atomic claims from normalized content and separates factual,
    verifiable claims from opinions, predictions, and satire/speculation.
    """

    def __init__(self, ai_provider: BaseAIProvider):
        self.ai = ai_provider

    async def extract_claims(self, content: NormalizedContent) -> Tuple[List[Claim], List[Claim]]:
        """
        Extracts atomic claims from multimodal content.
        Returns:
            Tuple of (verifiable_factual_claims, non_verifiable_or_opinion_claims)
        """
        # Multimodal fusion: Aggregate body content (text, transcript, OCR overlays, visual scenes)
        content_parts = []
        if content.raw_text:
            content_parts.append(content.raw_text)
        if content.transcript:
            content_parts.append(content.transcript)
        if content.ocr_text:
            content_parts.append(content.ocr_text)
        if content.visual_description:
            content_parts.append(content.visual_description)

        full_context = "\n\n".join(content_parts).strip()
        if not full_context and content.title:
            full_context = content.title

        if not full_context:
            logger.warning("No extractable content found across all modalities.")
            return [], []

        logger.info(f"Extracting claims from {content.url} ({len(full_context)} characters across modalities)...")
        all_claims = await self.ai.extract_claims(
            text=full_context,
            metadata={
                "title": content.title,
                "author": content.author,
                "platform": content.platform.value,
                "published_date": content.published_date,
            }
        )

        verifiable_claims: List[Claim] = []
        non_verifiable_claims: List[Claim] = []

        for claim in all_claims:
            if claim.claim_type == ClaimType.FACTUAL and claim.is_verifiable:
                verifiable_claims.append(claim)
            else:
                non_verifiable_claims.append(claim)

        # Sort verifiable claims by importance score descending (core viral claims first)
        verifiable_claims.sort(key=lambda c: c.importance_score, reverse=True)

        logger.info(
            f"Extracted {len(all_claims)} total claims: "
            f"{len(verifiable_claims)} factual/verifiable, "
            f"{len(non_verifiable_claims)} opinions/predictions/satire."
        )

        return verifiable_claims, non_verifiable_claims
