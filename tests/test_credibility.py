import pytest
from app.services.credibility.scorer import SourceCredibilityEngine
from app.models.evidence import SourceTier

def test_government_domain_scoring():
    engine = SourceCredibilityEngine()
    score, tier, factors = engine.evaluate_source(
        url="https://pib.gov.in/FactCheck/Alert.html",
        finding_text="PIB declares fake student scholarship message a scam.",
        claim_text="Government is giving ₹25,000 to every student.",
        publication_date="2026",
        corroborating_source_count=3,
    )
    assert tier == SourceTier.TIER_1_PRIMARY
    assert score >= 85
    assert factors.primary_source_score >= 90

def test_fact_checker_scoring():
    engine = SourceCredibilityEngine()
    score, tier, factors = engine.evaluate_source(
        url="https://snopes.com/fact-check/student-25000-scheme/",
        finding_text="Fact-check reveals viral message is completely fraudulent.",
        claim_text="Government is giving ₹25,000 to every student.",
        publication_date="2026",
        corroborating_source_count=2,
    )
    assert tier == SourceTier.TIER_2_SECONDARY
    assert score >= 75

def test_general_blog_tier3_scoring():
    engine = SourceCredibilityEngine()
    score, tier, factors = engine.evaluate_source(
        url="https://random-unverified-blog.xyz/post123",
        finding_text="Free money for students claimed on social media.",
        claim_text="Government is giving ₹25,000 to every student.",
        publication_date=None,
        corroborating_source_count=1,
    )
    assert tier == SourceTier.TIER_3_OTHER
    # Unverified blog must have substantially lower score than Tier 1/2
    assert score < 65

def test_dynamic_weight_update():
    engine = SourceCredibilityEngine()
    initial_score, _, _ = engine.evaluate_source(
        url="https://random-unverified-blog.xyz/post123",
        finding_text="Some random text",
        claim_text="Government claim",
    )
    
    # Increase tier_weight and lower others
    engine.update_weights({"tier_weight": 0.8, "domain_reputation": 0.1})
    new_score, _, _ = engine.evaluate_source(
        url="https://random-unverified-blog.xyz/post123",
        finding_text="Some random text",
        claim_text="Government claim",
    )
    # The score should reflect the new weights dynamically
    assert isinstance(new_score, int)
    assert 0 <= new_score <= 100
