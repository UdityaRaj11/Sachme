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
        Extracts claims from content.
        Returns:
            Tuple of (verifiable_factual_claims, non_verifiable_or_opinion_claims)
        """
        full_text = content.raw_text or content.transcript or content.ocr_text or ""
        if not full_text.strip():
            logger.warning("No text to extract claims from.")
            return [], []

        logger.info(f"Extracting claims from {content.url} ({len(full_text)} characters)...")
        all_claims = await self.ai.extract_claims(
            text=full_text,
            metadata={
                "title": content.title,
                "author": content.author,
                "platform": content.platform.value,
            }
        )

        verifiable_claims: List[Claim] = []
        non_verifiable_claims: List[Claim] = []

        for claim in all_claims:
            if claim.claim_type == ClaimType.FACTUAL and claim.is_verifiable:
                verifiable_claims.append(claim)
            else:
                non_verifiable_claims.append(claim)

        logger.info(
            f"Extracted {len(all_claims)} total claims: "
            f"{len(verifiable_claims)} factual/verifiable, "
            f"{len(non_verifiable_claims)} opinions/predictions/satire."
        )

        return verifiable_claims, non_verifiable_claims
