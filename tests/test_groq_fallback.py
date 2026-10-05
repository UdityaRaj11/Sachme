import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.claims import Claim, ClaimType
from app.models.evidence import Evidence, EvidenceType, SourceTier
from app.services.ai.provider import (
    GeminiAIProvider,
    GroqAIProvider,
    HeuristicAIProvider,
    get_ai_provider,
)

@pytest.mark.asyncio
async def test_groq_provider_claim_extraction_mocked():
    """Verifies that GroqAIProvider parses JSON claim extraction correctly."""
    provider = GroqAIProvider(api_key="gsk_test_mock_key", model_name="llama-3.3-70b-versatile")
    
    mock_json = """{
      "claims": [
        {
          "claim_id": "c_groq_1",
          "claim_text": "Government announced a new solar energy initiative.",
          "claim_type": "factual",
          "entities": [{"name": "Government", "category": "ORG"}],
          "dates_or_time_references": ["2026"],
          "locations": ["India"],
          "verification_questions": ["Did the government announce a solar initiative?"],
          "importance_score": 0.9,
          "is_verifiable": true
        }
      ]
    }"""
    
    with patch.object(provider, "_generate_json", new=AsyncMock(return_value=mock_json)):
        claims = await provider.extract_claims("Government announced a new solar energy initiative in 2026.")
        assert len(claims) == 1
        assert claims[0].claim_id == "c_groq_1"
        assert claims[0].claim_text == "Government announced a new solar energy initiative."
        assert claims[0].claim_type == ClaimType.FACTUAL


@pytest.mark.asyncio
async def test_gemini_falls_back_to_groq_on_error():
    """
    Verifies that when Gemini encounters an error (such as a 429 quota limit or network timeout),
    it transparently falls back to GroqAIProvider.
    """
    groq_provider = GroqAIProvider(api_key="gsk_test_mock_key")
    gemini_provider = GeminiAIProvider(
        api_key="mock_gemini_key",
        fallback_provider=groq_provider,
    )

    # Groq mock response
    groq_response = {
        "verdict": "SUPPORTED",
        "evidence_evaluations": [],
        "reasoning": "Substantiated by primary government notification.",
        "verdict_title": "Verified by Official Records",
        "evidence_bullet_points": ["✅ Confirmed by ministry announcement."],
        "why_explanation": "Official records substantiate the claim.",
    }

    claim = Claim(
        claim_id="c_test_1",
        claim_text="Ministry launched clean fuel transition scheme.",
        claim_type=ClaimType.FACTUAL,
        entities=[],
        dates_or_time_references=[],
        locations=[],
        verification_questions=[],
        importance_score=0.9,
        is_verifiable=True,
    )

    # Simulate Gemini failing with a 429 Resource Exhausted / Rate Limit error
    with patch.object(
        gemini_provider,
        "_generate_json",
        new=AsyncMock(side_effect=Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded")),
    ):
        with patch.object(
            groq_provider,
            "verify_claim_against_evidence",
            new=AsyncMock(return_value=groq_response),
        ) as mock_groq_verify:
            result = await gemini_provider.verify_claim_against_evidence(claim, [])
            
            # Assert Groq was called as fallback
            assert mock_groq_verify.called
            assert result["verdict"] == "SUPPORTED"
            assert result["verdict_title"] == "Verified by Official Records"


@pytest.mark.asyncio
async def test_groq_falls_back_to_heuristic_when_it_fails():
    """
    Verifies that if Groq also encounters an error, it safely cascades
    to the offline HeuristicAIProvider.
    """
    heuristic_provider = HeuristicAIProvider()
    groq_provider = GroqAIProvider(
        api_key="gsk_test_mock_key",
        fallback_provider=heuristic_provider,
    )

    claim = Claim(
        claim_id="c_test_2",
        claim_text="Government announced free electricity for all citizens.",
        claim_type=ClaimType.FACTUAL,
        entities=[],
        dates_or_time_references=[],
        locations=[],
        verification_questions=[],
        importance_score=0.9,
        is_verifiable=True,
    )

    evidence = [
        Evidence(
            evidence_id="ev_1",
            finding="PIB Fact Check: Viral message claiming free electricity scheme is fake and a scam.",
            type=EvidenceType.CONTRADICTING,
            source="PIB Fact Check",
            url="https://pib.gov.in/fact-check",
            credibility_score=95,
            tier=SourceTier.TIER_1_PRIMARY,
        )
    ]

    # Groq fails with an API error
    with patch.object(
        groq_provider,
        "_generate_json",
        new=AsyncMock(side_effect=Exception("Groq API 503 Service Unavailable")),
    ):
        result = await groq_provider.verify_claim_against_evidence(claim, evidence)
        # Should gracefully return heuristic verification
        assert result["verdict"] == "CONTRADICTED"
        assert "Disproven" in result["verdict_title"] or "Misinformation" in result["verdict_title"]


def test_get_ai_provider_wiring():
    """Verifies factory configuration for multi-tier provider hierarchies."""
    # 1. When AI_PROVIDER is groq
    with patch("app.services.ai.provider.settings.AI_PROVIDER", "groq"):
        with patch("app.services.ai.provider.settings.GROQ_API_KEY", "gsk_dummy_key"):
            prov = get_ai_provider()
            assert isinstance(prov, GroqAIProvider)
            assert isinstance(prov.fallback_provider, HeuristicAIProvider)

    # 2. When AI_PROVIDER is gemini and GROQ_API_KEY is present
    with patch("app.services.ai.provider.settings.AI_PROVIDER", "gemini"):
        with patch("app.services.ai.provider.settings.GEMINI_API_KEY", "dummy_gemini_key"):
            with patch("app.services.ai.provider.settings.GROQ_API_KEY", "gsk_dummy_key"):
                prov = get_ai_provider()
                assert isinstance(prov, GeminiAIProvider)
                assert isinstance(prov.fallback_provider, GroqAIProvider)
                assert isinstance(prov.fallback_provider.fallback_provider, HeuristicAIProvider)
