import asyncio
from typing import List, Dict, Any, Tuple
from app.models.claims import Claim, ClaimType
from app.models.evidence import Evidence, EvidenceType
from app.models.verification import (
    VerdictType,
    VerifiedClaim,
    ClaimEvidenceItem,
    UserFacingUI,
)
from app.services.ai.provider import BaseAIProvider
from app.services.verification.confidence import ConfidenceEngine
from app.services.verification.explanation import ExplanationGenerator
from app.core.logging import logger

class VerificationEngine:
    """
    Evaluates individual factual claims against retrieved evidence,
    synthesizes consensus/conflict, calculates confidence, and produces
    structured verdicts.
    """

    def __init__(self, ai_provider: BaseAIProvider):
        self.ai = ai_provider

    async def verify_claim(self, claim: Claim, evidence_items: List[Evidence]) -> Tuple[VerifiedClaim, UserFacingUI]:
        """Verifies a single factual claim against its evidence corpus."""
        logger.info(f"Verifying claim {claim.claim_id}: '{claim.claim_text}' with {len(evidence_items)} evidence sources.")

        # If it's a non-factual claim, immediately return OPINION
        if claim.claim_type != ClaimType.FACTUAL:
            verified = VerifiedClaim(
                claim_id=claim.claim_id,
                claim=claim.claim_text,
                verdict=VerdictType.OPINION,
                confidence=95,
                evidence=[],
                explanation="This statement expresses a personal opinion, prediction, or subjective viewpoint and cannot be verified empirically.",
            )
            ui = UserFacingUI(
                badge_label="💬 Opinion / Subjective",
                claim_detected=claim.claim_text,
                evidence_points=["ℹ️ Statement represents subjective viewpoint rather than empirical assertion."],
                verdict_title="Opinion / Non-Factual Statement",
                confidence_display="95%",
                why_explanation="Subjective opinions, speculations, and value judgements cannot be fact-checked against empirical records.",
                evidence_sources=[],
            )
            return verified, ui

        # 1. Ask AI provider to analyze evidence stance and synthesis
        ai_eval = await self.ai.verify_claim_against_evidence(claim, evidence_items)
        raw_verdict_str = ai_eval.get("verdict", "UNVERIFIABLE").upper()

        try:
            verdict = VerdictType(raw_verdict_str)
        except ValueError:
            verdict = VerdictType.UNVERIFIABLE

        # 2. Count stance agreements
        supporting_count = sum(1 for e in evidence_items if e.type == EvidenceType.SUPPORTING)
        contradicting_count = sum(1 for e in evidence_items if e.type == EvidenceType.CONTRADICTING)

        # 3. Calculate 0-100 Confidence
        confidence_score, breakdown = ConfidenceEngine.calculate_confidence(
            claim=claim,
            evidence_items=evidence_items,
            verdict=verdict,
            supporting_count=supporting_count,
            contradicting_count=contradicting_count,
        )

        # 4. Generate human-readable explanation
        reasoning = ai_eval.get("reasoning", "")
        why_text = ai_eval.get("why_explanation", "")
        explanation = ExplanationGenerator.generate_explanation(
            claim=claim,
            verdict=verdict,
            evidence_items=evidence_items,
            ai_reasoning=reasoning,
            ai_why=why_text,
        )

        # 5. Format evidence items for final JSON schema
        formatted_evidence: List[ClaimEvidenceItem] = [
            ClaimEvidenceItem(
                finding=e.finding,
                type=e.type.value,
                source=e.source,
                url=e.url,
                credibility_score=e.credibility_score,
            )
            for e in evidence_items[:5]
        ]

        verified = VerifiedClaim(
            claim_id=claim.claim_id,
            claim=claim.claim_text,
            verdict=verdict,
            confidence=confidence_score,
            evidence=formatted_evidence,
            explanation=explanation,
        )

        # 6. Format user-facing UI
        bullet_points = ai_eval.get("evidence_bullet_points", [])
        ui = ExplanationGenerator.build_user_facing_ui(
            claim=claim,
            verdict=verdict,
            confidence=confidence_score,
            evidence_items=evidence_items,
            bullet_points=bullet_points,
            why_text=why_text,
        )

        return verified, ui

    @staticmethod
    def aggregate_overall_verdict(verified_claims: List[VerifiedClaim]) -> Tuple[str, int]:
        """
        Synthesizes an overall verdict and confidence across all analyzed claims.
        """
        if not verified_claims:
            return "UNVERIFIABLE", 50

        # Check for harmful/disproven claims first
        has_contradicted = any(c.verdict == VerdictType.CONTRADICTED for c in verified_claims)
        has_misleading = any(c.verdict == VerdictType.MISLEADING for c in verified_claims)
        all_supported = all(c.verdict == VerdictType.SUPPORTED for c in verified_claims)
        all_opinions = all(c.verdict == VerdictType.OPINION for c in verified_claims)

        if has_contradicted:
            overall = "CONTRADICTED"
        elif has_misleading:
            overall = "MISLEADING"
        elif all_supported:
            overall = "SUPPORTED"
        elif all_opinions:
            overall = "OPINION"
        else:
            overall = "UNVERIFIABLE"

        # Calculate average confidence
        avg_conf = int(sum(c.confidence for c in verified_claims) / len(verified_claims))
        return overall, avg_conf
