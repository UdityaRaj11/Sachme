from fastapi import APIRouter
from app.models.api import CredibilityWeightsUpdate
from app.services.credibility.scorer import credibility_engine

router = APIRouter()

@router.get(
    "/config/credibility-weights",
    summary="Get current source credibility weights and scoring rules",
)
async def get_credibility_weights():
    """Returns currently active source credibility scoring weights and tier base values."""
    return {
        "status": "success",
        "weights": credibility_engine.config.get("weights"),
        "tier_base_scores": credibility_engine.tier_base_scores,
    }


@router.post(
    "/config/credibility-weights",
    summary="Dynamically update source credibility weights",
)
async def update_credibility_weights(payload: CredibilityWeightsUpdate):
    """
    Updates credibility formula weights at runtime without modifying code or restarting the server.
    """
    updates = payload.model_dump(exclude_none=True)
    if updates:
        credibility_engine.update_weights(updates)

    return {
        "status": "success",
        "message": "Source credibility scoring weights updated successfully.",
        "active_weights": credibility_engine.config.get("weights"),
    }
