import pytest
from app.models.claims import Claim, ClaimType
from app.models.evidence import Evidence, EvidenceType, SourceTier
from app.models.verification import VerdictType
from app.services.verification.confidence import ConfidenceEngine

def test_high_confidence_with_tier1_agreement():
    claim = Claim(
        claim_id="c_1",
        claim_text="Government declared public holiday",
        claim_type=ClaimType.FACTUAL,
        entities=[],
        dates_or_time_references=["2026"],
        locations=[],
        verification_questions=[],
    )
    evidence = [
        Evidence(
            evidence_id="1",
            finding="Official gazette declares holiday",
            type=EvidenceType.SUPPORTING,
            source="Gazette",
            url="https://gov.in/gazette",
            credibility_score=95,
            tier=SourceTier.TIER_1_PRIMARY,
        ),
        Evidence(
            evidence_id="2",
            finding="Ministry announces official holiday",
            type=EvidenceType.SUPPORTING,
            source="Ministry",
            url="https://ministry.gov.in/notice",
            credibility_score=93,
            tier=SourceTier.TIER_1_PRIMARY,
        ),
    ]

    conf, breakdown = ConfidenceEngine.calculate_confidence(
        claim=claim,
        evidence_items=evidence,
        verdict=VerdictType.SUPPORTED,
        supporting_count=2,
        contradicting_count=0,
    )
    assert conf >= 85
    assert breakdown.source_agreement_score == 1.0

def test_confidence_reduction_on_conflicting_evidence():
    claim = Claim(
        claim_id="c_2",
        claim_text="Company acquired by rival",
        claim_type=ClaimType.FACTUAL,
        entities=[],
        dates_or_time_references=[],
        locations=[],
        verification_questions=[],
    )
    evidence = [
        Evidence(
            evidence_id="1",
            finding="Source A says deal confirmed",
            type=EvidenceType.SUPPORTING,
            source="Source A",
            url="https://news1.com",
            credibility_score=75,
            tier=SourceTier.TIER_2_SECONDARY,
        ),
        Evidence(
            evidence_id="2",
            finding="Source B says deal denied by spokesperson",
            type=EvidenceType.CONTRADICTING,
            source="Source B",
            url="https://news2.com",
            credibility_score=75,
            tier=SourceTier.TIER_2_SECONDARY,
        ),
    ]

    conf, breakdown = ConfidenceEngine.calculate_confidence(
        claim=claim,
        evidence_items=evidence,
        verdict=VerdictType.MISLEADING,
        supporting_count=1,
        contradicting_count=1,
    )
    # When evidence is conflicting, confidence must be capped (<= 70)
    assert conf <= 70

def test_confidence_cap_for_tier3_only():
    claim = Claim(
        claim_id="c_3",
        claim_text="Unverified rumor",
        claim_type=ClaimType.FACTUAL,
    )
    evidence = [
        Evidence(
            evidence_id="1",
            finding="Blog rumor",
            type=EvidenceType.SUPPORTING,
            source="Blog",
            url="https://randomblog.com/1",
            credibility_score=45,
            tier=SourceTier.TIER_3_OTHER,
        )
    ]
    conf, _ = ConfidenceEngine.calculate_confidence(
        claim=claim,
        evidence_items=evidence,
        verdict=VerdictType.SUPPORTED,
        supporting_count=1,
        contradicting_count=0,
    )
    # Tier 3 only must not exceed 65
    assert conf <= 65
