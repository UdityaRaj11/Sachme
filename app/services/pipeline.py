import uuid
import asyncio
from datetime import datetime
from typing import Dict, Optional, List, Tuple

from app.models.api import (
    VerifyRequest,
    VerifyResponse,
    JobStatus,
    JobStatusResponse,
    ContentSection,
    ContentSummarySection,
)
from app.models.content import (
    ClassificationResult,
    NormalizedContent,
    Platform,
    ExtractionStrategy,
)
from app.models.claims import Claim
from app.models.verification import VerifiedClaim, UserFacingUI
from app.core.exceptions import (
    TruthFirewallException,
    UnsupportedContentError,
    ContentExtractionError,
)
from app.core.logging import logger
from app.core.cache import cache

from app.services.classifier.url_classifier import URLClassifier
from app.services.extraction.webpage import WebpageExtractor
from app.services.extraction.youtube import YouTubeExtractor
from app.services.extraction.social import SocialMediaExtractor
from app.services.extraction.image import ImageExtractor
from app.services.extraction.text import DirectTextExtractor
from app.services.ai.provider import get_ai_provider
from app.services.summarization.summarizer import ContentSummarizer
from app.services.claims.extractor import ClaimExtractor
from app.services.evidence.retriever import EvidenceRetriever
from app.services.verification.engine import VerificationEngine

class VerificationJob:
    def __init__(self, job_id: str, request: VerifyRequest):
        self.job_id = job_id
        self.request = request
        self.status = JobStatus.QUEUED
        self.progress = 0
        self.current_step = "Job queued"
        self.result: Optional[VerifyResponse] = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.completed_at: Optional[str] = None


class VerificationPipeline:
    """
    End-to-End Orchestrator executing the complete verification lifecycle.
    """

    def __init__(self):
        self.ai_provider = get_ai_provider()
        self.summarizer = ContentSummarizer(self.ai_provider)
        self.claim_extractor = ClaimExtractor(self.ai_provider)
        self.evidence_retriever = EvidenceRetriever()
        self.verification_engine = VerificationEngine(self.ai_provider)
        self.jobs: Dict[str, VerificationJob] = {}

    def create_job(self, request: VerifyRequest) -> str:
        job_id = str(uuid.uuid4())
        job = VerificationJob(job_id, request)
        self.jobs[job_id] = job
        # Schedule async background task
        asyncio.create_task(self._execute_job_pipeline(job))
        return job_id

    def get_job(self, job_id: str) -> Optional[JobStatusResponse]:
        job = self.jobs.get(job_id)
        if not job:
            return None
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            progress_percentage=job.progress,
            current_step=job.current_step,
            result=job.result,
            error=job.error,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )

    async def run_sync(self, request: VerifyRequest) -> VerifyResponse:
        """Executes verification synchronously for immediate responses."""
        return await self._run_pipeline(request)

    async def _execute_job_pipeline(self, job: VerificationJob):
        try:
            res = await self._run_pipeline(job.request, job)
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.current_step = "Verification completed"
            job.result = res
            job.completed_at = datetime.utcnow().isoformat() + "Z"
        except TruthFirewallException as e:
            logger.error(f"Job {job.job_id} failed with error: {e.message}")
            job.status = JobStatus.FAILED
            job.error = e.message
            job.current_step = "Failed"
            job.completed_at = datetime.utcnow().isoformat() + "Z"
        except Exception as e:
            logger.exception(f"Unexpected error processing job {job.job_id}: {e}")
            job.status = JobStatus.FAILED
            job.error = f"Internal processing error: {str(e)}"
            job.current_step = "Failed"
            job.completed_at = datetime.utcnow().isoformat() + "Z"

    async def _run_pipeline(
        self, request: VerifyRequest, job: Optional[VerificationJob] = None
    ) -> VerifyResponse:
        cache_key = f"verify:{request.url or request.direct_text}"

        # 0. Check Cache
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached verification result for: {cache_key}")
            return cached_result

        # Helper to update job status
        def _update(status: JobStatus, progress: int, step: str):
            if job:
                job.status = status
                job.progress = progress
                job.current_step = step

        # Step 1: Classify URL / Content
        _update(JobStatus.CLASSIFYING, 10, "Classifying content type and platform...")
        classification = URLClassifier.classify(url=request.url, direct_text=request.direct_text)
        logger.info(f"Content classified as: {classification.platform} / {classification.content_type}")

        # Step 2: Content Extraction
        _update(JobStatus.EXTRACTING, 25, f"Extracting content using {classification.extraction_strategy}...")
        extracted_content = await self._extract_content(classification, request.direct_text)

        # Step 3: Summarize Content
        _update(JobStatus.SUMMARIZING, 40, "Generating multimodal summary...")
        summary = await self.summarizer.summarize(extracted_content)
        extracted_content.summary = summary

        # Step 4: Extract Factual Claims
        _update(JobStatus.EXTRACTING_CLAIMS, 55, "Extracting verifiable factual claims...")
        factual_claims, non_factual_claims = await self.claim_extractor.extract_claims(extracted_content)

        verified_claims: List[VerifiedClaim] = []
        user_facing_uis: List[UserFacingUI] = []

        # If no factual claims found, handle opinions or empty content
        if not factual_claims:
            if non_factual_claims:
                # Process the non-factual claims as OPINION
                for op in non_factual_claims:
                    v_op, ui_op = await self.verification_engine.verify_claim(op, [])
                    verified_claims.append(v_op)
                    user_facing_uis.append(ui_op)
            else:
                # Fallback claim
                empty_claim = Claim(
                    claim_id="c_0",
                    claim_text=extracted_content.summary.text,
                    claim_type=ClaimType.OPINION,
                    verification_questions=[],
                    importance_score=0.5,
                    is_verifiable=False,
                )
                v_empty, ui_empty = await self.verification_engine.verify_claim(empty_claim, [])
                verified_claims.append(v_empty)
                user_facing_uis.append(ui_empty)
        else:
            # Step 5 & 6: Retrieve Evidence & Cross-Check Each Claim
            total_claims = len(factual_claims)
            for i, claim in enumerate(factual_claims):
                _update(
                    JobStatus.RETRIEVING_EVIDENCE,
                    60 + int((i / total_claims) * 20),
                    f"Retrieving external evidence for claim {i+1} of {total_claims}...",
                )
                evidence_items = await self.evidence_retriever.retrieve_evidence_for_claim(claim)

                _update(
                    JobStatus.VERIFYING,
                    80 + int((i / total_claims) * 15),
                    f"Cross-checking claim {i+1} against gathered evidence...",
                )
                verified_claim, ui_data = await self.verification_engine.verify_claim(claim, evidence_items)
                verified_claims.append(verified_claim)
                user_facing_uis.append(ui_data)

        # Step 7: Synthesize Overall Verdict and Confidence
        overall_verdict, overall_confidence = VerificationEngine.aggregate_overall_verdict(verified_claims)

        # Primary UI data presentation
        primary_ui = user_facing_uis[0] if user_facing_uis else None

        response = VerifyResponse(
            status="success",
            content=ContentSection(
                url=extracted_content.url,
                platform=extracted_content.platform.value,
                content_type=extracted_content.content_type.value,
                language=extracted_content.language,
                summary=ContentSummarySection(
                    visual=extracted_content.summary.visual,
                    text=extracted_content.summary.text,
                    key_points=extracted_content.summary.key_points,
                ),
            ),
            claims=verified_claims,
            overall_verdict=overall_verdict,
            overall_confidence=overall_confidence,
            user_interface=primary_ui,
        )

        # Cache final response for 1 hour
        await cache.set(cache_key, response, ttl=3600)
        return response

    async def _extract_content(
        self, classification: ClassificationResult, direct_text: Optional[str] = None
    ) -> NormalizedContent:
        strategy = classification.extraction_strategy

        if strategy == ExtractionStrategy.WEBPAGE_EXTRACTOR:
            return await WebpageExtractor().extract(classification)
        elif strategy == ExtractionStrategy.YOUTUBE_EXTRACTOR:
            return await YouTubeExtractor().extract(classification)
        elif strategy == ExtractionStrategy.SOCIAL_EXTRACTOR:
            return await SocialMediaExtractor().extract(classification)
        elif strategy == ExtractionStrategy.IMAGE_EXTRACTOR:
            return await ImageExtractor().extract(classification)
        elif strategy == ExtractionStrategy.TEXT_EXTRACTOR:
            return await DirectTextExtractor(raw_text=direct_text or "").extract(classification)
        else:
            raise UnsupportedContentError(
                message=f"No extraction pipeline available for strategy '{strategy}'.",
                platform=classification.platform.value,
                url=classification.canonical_url,
            )

pipeline = VerificationPipeline()
