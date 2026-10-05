from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class SourceTier(str, Enum):
    TIER_1_PRIMARY = "tier_1_primary"       # Government, official notifications, regulatory bodies, peer-reviewed science
    TIER_2_SECONDARY = "tier_2_secondary"   # Established news, academic institutions, accredited fact-checkers
    TIER_3_OTHER = "tier_3_other"           # General websites, blogs, forums, UGC


class EvidenceType(str, Enum):
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    CONTEXTUAL = "contextual"


class CredibilityFactors(BaseModel):
    """Detailed breakdown of factors contributing to source credibility score."""
    tier_score: float = Field(ge=0, le=100)
    domain_reputation_score: float = Field(ge=0, le=100)
    relevance_score: float = Field(ge=0, le=100)
    primary_source_score: float = Field(ge=0, le=100)
    recency_score: float = Field(ge=0, le=100)
    corroboration_score: float = Field(ge=0, le=100)
    raw_details: Dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    """Individual evidence item retrieved and evaluated for a claim."""
    evidence_id: str
    finding: str = Field(description="Direct factual excerpt or summary of evidence from source")
    type: EvidenceType
    source: str = Field(description="Publisher, organization or domain name")
    url: str = Field(description="Source URL preserving provenance")
    credibility_score: int = Field(ge=0, le=100, description="Overall source credibility score (0-100)")
    tier: SourceTier = SourceTier.TIER_3_OTHER
    credibility_factors: Optional[CredibilityFactors] = None
    publication_date: Optional[str] = None
    stance_confidence: float = Field(default=0.85, ge=0.0, le=1.0)
