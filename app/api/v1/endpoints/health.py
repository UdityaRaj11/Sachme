from fastapi import APIRouter
from app.config import settings
from app.core.cache import cache
import time

router = APIRouter()
START_TIME = time.time()

@router.get("/health", summary="Service Health and Status")
async def health_check():
    """Returns real-time health metrics, active AI provider, and cache stats."""
    cache_entries = await cache.size()
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "ai_provider": settings.AI_PROVIDER,
        "search_provider": settings.SEARCH_PROVIDER,
        "cache": {
            "active_entries": cache_entries,
            "max_size": settings.MAX_CACHE_SIZE,
            "ttl_seconds": settings.CACHE_TTL_SECONDS,
        }
    }
