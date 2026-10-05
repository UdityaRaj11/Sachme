from fastapi import APIRouter, HTTPException, Request, status
from app.models.api import VerifyRequest, VerifyResponse, JobStatusResponse
from app.services.pipeline import pipeline
from app.core.exceptions import JobNotFoundError, RateLimitExceededError
from app.core.rate_limiter import rate_limiter

router = APIRouter()

@router.post(
    "/verify",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit URL or text for asynchronous verification",
    response_description="Returns queued job metadata with job_id for polling progress",
)
async def submit_verification(request: VerifyRequest, req: Request):
    """
    Submits a URL or direct text for background AI verification.
    Returns 202 Accepted with a unique job ID to poll for status.
    """
    client_ip = req.client.host if req.client else "unknown"
    rate_limiter.check(client_ip)

    if not request.url and not request.direct_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'url' or 'direct_text' must be provided in request body."
        )

    job_id = pipeline.create_job(request)
    return {
        "status": "queued",
        "job_id": job_id,
        "poll_url": f"/api/v1/jobs/{job_id}",
        "message": "Verification job initiated. Poll poll_url to retrieve live progress and final result."
    }


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Poll verification job status",
)
async def get_job_status(job_id: str):
    """Retrieves current processing stage, progress percentage, or completed results for a job."""
    job_info = pipeline.get_job(job_id)
    if not job_info:
        raise JobNotFoundError(job_id)
    return job_info


@router.post(
    "/verify/sync",
    response_model=VerifyResponse,
    summary="Synchronous URL/text verification",
)
async def verify_synchronous(request: VerifyRequest, req: Request):
    """
    Performs full verification synchronously and waits for all stages to complete
    before returning the structured JSON result.
    """
    client_ip = req.client.host if req.client else "unknown"
    rate_limiter.check(client_ip)

    if not request.url and not request.direct_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'url' or 'direct_text' must be provided in request body."
        )

    return await pipeline.run_sync(request)
