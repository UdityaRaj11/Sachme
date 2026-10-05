from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ClaimType(str, Enum):
    FACTUAL = "factual"
    OPINION = "opinion"
    PREDICTION = "prediction"
    SATIRE_SPECULATION = "satire_speculation"


class Entity(BaseModel):
    name: str
    category: str = Field(description="e.g. PERSON, ORG, GPE, LAW, PRODUCT, EVENT")


class Claim(BaseModel):
    """Factual or non-factual claim extracted from normalized content."""
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    entities: List[Entity] = Field(default_factory=list)
    dates_or_time_references: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    verification_questions: List[str] = Field(
        default_factory=list,
        description="Targeted investigative questions to verify or falsify this claim"
    )
    importance_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Relevance and importance score of the claim in the overall content"
    )
    is_verifiable: bool = True
