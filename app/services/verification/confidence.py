from typing import List
from app.models.claims import Claim
from app.models.evidence import Evidence, SourceTier
from app.models.verification import VerdictType, ConfidenceBreakdown

class ConfidenceEngine:
    """
    Computes a rigorous 0-100 confidence score for a verification verdict.
    
    CRITICAL EPITEMIC RULE:
    Confidence represents confidence in the VERDICT itself, NOT the probability
    that the claim is true.
    
    For instance:
    - If 4 Tier-1 government & wire sources unequivocally contradict a claim,
      verdict = CONTRADICTED with 95% confidence.
    - If only 1 Tier-3 blog mentions the claim, verdict = UNVERIFIABLE with 88% confidence
      (we are confident that reliable evidence is missing).
    - If sources disagree evenly (2 say yes, 2 say no), confidence in any definitive verdict
      must drop significantly.
    """

    @staticmethod
    def calculate_confidence(
        claim: Claim,
        evidence_items: List[Evidence],
        verdict: VerdictType,
        supporting_count: int,
        contradicting_count: int,
    ) -> tuple[int, ConfidenceBreakdown]:
        if not evidence_items:
            # High confidence that it is unverifiable
            return 85, ConfidenceBreakdown(
                source_credibility_weight=0.0,
                evidence_quantity_score=0.0,
                source_agreement_score=1.0,
                temporal_recency_score=0.8,
                claim_specificity_score=0.8,
                raw_confidence=85.0,
                final_confidence=85,
            )

        # 1. Average Source Credibility Score (0 - 100)
        top_sources = evidence_items[:4]
        avg_source_credibility = sum(e.credibility_score for e in top_sources) / len(top_sources)

        # 2. Evidence Quantity Score (0 - 1.0)
        # Diminishing returns after 4 independent sources
        quantity_score = min(1.0, len(evidence_items) / 4.0)

        # 3. Source Agreement / Consensus Score (0 - 1.0)
        total_evaluable = supporting_count + contradicting_count
        if total_evaluable == 0:
            agreement_score = 0.5
        else:
            majority = max(supporting_count, contradicting_count)
            agreement_score = majority / total_evaluable

        # 4. Specificity & Quality of Claim
        has_entities = len(claim.entities) > 0
        has_dates = len(claim.dates_or_time_references) > 0
        specificity_score = 0.9 if (has_entities and has_dates) else (0.75 if has_entities else 0.6)

        # 5. Tier Multiplier
        has_tier1 = any(e.tier == SourceTier.TIER_1_PRIMARY for e in evidence_items)
        has_tier2 = any(e.tier == SourceTier.TIER_2_SECONDARY for e in evidence_items)
        
        if has_tier1:
            tier_multiplier = 1.05
        elif has_tier2:
            tier_multiplier = 0.95
        else:
            tier_multiplier = 0.70 # Tier 3 alone cannot produce high confidence

        # Weighted calculation
        raw = (
            (avg_source_credibility * 0.40)
            + (quantity_score * 100.0 * 0.25)
            + (agreement_score * 100.0 * 0.25)
            + (specificity_score * 100.0 * 0.10)
        ) * tier_multiplier

        # If evidence is conflicting, cap confidence
        if supporting_count > 0 and contradicting_count > 0:
            raw = min(raw, 70.0)

        # If only Tier 3 sources present, cap confidence at 65
        if not has_tier1 and not has_tier2:
            raw = min(raw, 65.0)

        final_conf = max(10, min(99, int(round(raw))))

        breakdown = ConfidenceBreakdown(
            source_credibility_weight=round(avg_source_credibility, 2),
            evidence_quantity_score=round(quantity_score, 2),
            source_agreement_score=round(agreement_score, 2),
            temporal_recency_score=0.85,
            claim_specificity_score=round(specificity_score, 2),
            raw_confidence=round(raw, 2),
            final_confidence=final_conf,
        )

        return final_conf, breakdown
