from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.evidence import EvidenceType

class VerdictType(str, Enum):
    SUPPORTED = "SUPPORTED"
    MISLEADING = "MISLEADING"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIABLE = "UNVERIFIABLE"
    OPINION = "OPINION"


class ClaimEvidenceItem(BaseModel):
    """Evidence structure required by Section 10 specification."""
    finding: str
    type: str = Field(description="supporting | contradicting | contextual")
    source: str
    url: str
    credibility_score: int


class VerifiedClaim(BaseModel):
    """Verification result for a single claim according to Section 10 schema."""
    claim_id: str
    claim: str
    verdict: VerdictType
    confidence: int = Field(ge=0, le=100)
    evidence: List[ClaimEvidenceItem] = Field(default_factory=list)
    explanation: str


class ConfidenceBreakdown(BaseModel):
    """Detailed components used to calculate the 0-100 confidence score."""
    source_credibility_weight: float
    evidence_quantity_score: float
    source_agreement_score: float
    temporal_recency_score: float
    claim_specificity_score: float
    raw_confidence: float
    final_confidence: int


class UserFacingUI(BaseModel):
    """
    Structured data formatted specifically for rendering the user-facing UI
    matching Section 11:
    - Status badge (e.g., '🚨 Potentially misleading')
    - Claim detected
    - Evidence bullet points (e.g., '❌ No matching government announcement')
    - Verdict title (e.g., 'Very likely a scam/misinformation')
    - Confidence percentage (e.g., 94%)
    - Why? concise reasoning
    - Evidence source links
    """
    badge_label: str
    claim_detected: str
    evidence_points: List[str]
    verdict_title: str
    confidence_display: str
    why_explanation: str
    evidence_sources: List[Dict[str, str]]
