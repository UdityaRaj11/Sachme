from fastapi import APIRouter
from app.api.v1.endpoints import verify, health, config_routes

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Metrics"])
api_router.include_router(verify.router, tags=["Verification Pipeline"])
api_router.include_router(config_routes.router, tags=["Configuration & Weights"])
