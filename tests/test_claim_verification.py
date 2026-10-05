import pytest
from app.models.claims import Claim, ClaimType
from app.models.evidence import Evidence, EvidenceType, SourceTier
from app.models.verification import VerdictType
from app.services.verification.engine import VerificationEngine
from app.services.ai.provider import HeuristicAIProvider

@pytest.mark.asyncio
async def test_verify_claim_contradicted_by_evidence():
    ai = HeuristicAIProvider()
    engine = VerificationEngine(ai)

    claim = Claim(
        claim_id="c_1",
        claim_text="Government is giving ₹25,000 to every student.",
        claim_type=ClaimType.FACTUAL,
        entities=[],
        dates_or_time_references=[],
        locations=[],
        verification_questions=["Is government giving ₹25,000?"],
        importance_score=0.95,
        is_verifiable=True,
    )

    evidence = [
        Evidence(
            evidence_id="ev_1",
            finding="PIB Fact Check: The viral claim that Central Government gives ₹25,000 to students is FAKE and a scam.",
            type=EvidenceType.CONTRADICTING,
            source="PIB Fact Check",
            url="https://pib.gov.in/FactCheck/FakeStudentScheme2026.html",
            credibility_score=94,
            tier=SourceTier.TIER_1_PRIMARY,
        ),
        Evidence(
            evidence_id="ev_2",
            finding="Fact check: No such ₹25,000 scholarship announced by Ministry. The viral registration link is fraudulent.",
            type=EvidenceType.CONTRADICTING,
            source="Alt News",
            url="https://altnews.in/fact-check-scholarship-fraud/",
            credibility_score=90,
            tier=SourceTier.TIER_2_SECONDARY,
        )
    ]

    verified, ui = await engine.verify_claim(claim, evidence)

    assert verified.verdict == VerdictType.CONTRADICTED
    assert verified.confidence >= 80
    assert len(verified.evidence) == 2
    assert "EVIDENCE:" in verified.explanation
    assert "REASONING:" in verified.explanation
    assert "VERDICT:" in verified.explanation
    assert "Disproven" in ui.verdict_title or "misinformation" in ui.verdict_title.lower()

@pytest.mark.asyncio
async def test_verify_opinion_claim():
    ai = HeuristicAIProvider()
    engine = VerificationEngine(ai)

    opinion_claim = Claim(
        claim_id="c_2",
        claim_text="The prime minister is the most charismatic leader in modern history.",
        claim_type=ClaimType.OPINION,
        verification_questions=[],
        importance_score=0.4,
        is_verifiable=False,
    )

    verified, ui = await engine.verify_claim(opinion_claim, [])
    assert verified.verdict == VerdictType.OPINION
    assert verified.confidence == 95
    assert "opinion" in verified.explanation.lower()
