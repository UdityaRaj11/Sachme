from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.verification import VerifiedClaim, VerdictType, UserFacingUI

class JobStatus(str, Enum):
    QUEUED = "queued"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    SUMMARIZING = "summarizing"
    EXTRACTING_CLAIMS = "extracting_claims"
    RETRIEVING_EVIDENCE = "retrieving_evidence"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class VerifyRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://twitter.com/example/status/1234567890",
                "direct_text": None,
                "language_preference": "en"
            }
        }
    )

    url: Optional[str] = Field(
        default=None,
        description="Public URL to webpage, YouTube video/short, Instagram reel/post, X/Twitter post, or image"
    )
    direct_text: Optional[str] = Field(
        default=None,
        description="Direct plain text to verify if not providing a URL"
    )
    language_preference: str = Field(default="en", description="Target language for output analysis")


class ContentSummarySection(BaseModel):
    visual: Optional[str] = None
    text: str
    key_points: List[str] = Field(default_factory=list)


class ContentSection(BaseModel):
    url: str
    platform: str
    content_type: str
    language: str
    summary: ContentSummarySection


class VerifyResponse(BaseModel):
    """Exact schema matching Section 10 specification + Section 11 user-facing UI."""
    status: str = "success"
    content: ContentSection
    claims: List[VerifiedClaim]
    overall_verdict: str
    overall_confidence: int
    user_interface: Optional[UserFacingUI] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress_percentage: int = Field(ge=0, le=100)
    current_step: str
    result: Optional[VerifyResponse] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class CredibilityWeightsUpdate(BaseModel):
    tier_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    domain_reputation: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    relevance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    primary_source_bonus: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    recency: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    corroboration: Optional[float] = Field(default=None, ge=0.0, le=1.0)
