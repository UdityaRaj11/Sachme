import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    TruthFirewallException,
    UnsupportedContentError,
    InvalidUrlError,
    ContentExtractionError,
    JobNotFoundError,
    RateLimitExceededError,
)
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-ready backend API for TruthFirewall: An AI-powered information firewall "
        "that verifies online and social media content in seconds by turning claims into "
        "evidence-backed, explainable answers."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing & Telemetry Middleware
@app.middleware("http")
async def add_process_time_and_log(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(process_time)
        logger.info(
            f"{request.method} {request.url.path} completed in {process_time}ms (Status: {response.status_code})"
        )
        return response
    except Exception as e:
        process_time = round((time.time() - start_time) * 1000, 2)
        logger.exception(f"Unhandled exception processing {request.method} {request.url.path}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error_type": "internal_server_error",
                "message": "An unexpected internal server error occurred while processing the request.",
                "details": {"duration_ms": process_time},
            },
        )

# Exception Handlers
@app.exception_handler(UnsupportedContentError)
async def unsupported_content_handler(request: Request, exc: UnsupportedContentError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_type": "unsupported_content",
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(InvalidUrlError)
async def invalid_url_handler(request: Request, exc: InvalidUrlError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "error_type": "invalid_url",
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(ContentExtractionError)
async def content_extraction_handler(request: Request, exc: ContentExtractionError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "status": "error",
            "error_type": "content_extraction_failed",
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(JobNotFoundError)
async def job_not_found_handler(request: Request, exc: JobNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "status": "error",
            "error_type": "job_not_found",
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "status": "error",
            "error_type": "rate_limit_exceeded",
            "message": exc.message,
        },
    )

@app.exception_handler(TruthFirewallException)
async def general_firewall_handler(request: Request, exc: TruthFirewallException):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_type": "truth_firewall_error",
            "message": exc.message,
            "details": exc.details,
        },
    )

# Include v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", summary="Root Endpoint")
def read_root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }
