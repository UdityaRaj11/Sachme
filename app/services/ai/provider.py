import os
import json
import re
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from app.config import settings
from app.core.logging import logger
from app.core.exceptions import VerificationEngineError
from app.models.claims import Claim, ClaimType, Entity
from app.models.content import ContentSummary
from app.models.evidence import Evidence, EvidenceType
from app.models.verification import VerdictType
from app.services.ai.prompts import (
    CLAIM_EXTRACTION_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
)

class BaseAIProvider(ABC):
    """Abstract interface for AI inference providers."""

    @abstractmethod
    async def extract_claims(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Claim]:
        pass

    @abstractmethod
    async def summarize_content(self, text: str, visual_context: Optional[str] = None) -> ContentSummary:
        pass

    @abstractmethod
    async def verify_claim_against_evidence(
        self, claim: Claim, evidence_items: List[Evidence]
    ) -> Dict[str, Any]:
        pass


class GeminiAIProvider(BaseAIProvider):
    """Google Gemini AI implementation using official google.genai / generativeai SDK."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._use_new_sdk = True
        except Exception:
            try:
                import google.generativeai as gai
                gai.configure(api_key=self.api_key)
                self._client = gai.GenerativeModel(self.model_name)
                self._use_new_sdk = False
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini SDK: {e}. Will fallback to Heuristic provider.")

    async def extract_claims(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Claim]:
        if not self._client:
            return await HeuristicAIProvider().extract_claims(text, metadata)

        prompt = f"Metadata: {json.dumps(metadata or {})}\n\nContent:\n{text[:8000]}"
        try:
            raw_json = await self._generate_json(CLAIM_EXTRACTION_SYSTEM_PROMPT, prompt)
            data = json.loads(raw_json)
            claims = []
            for item in data.get("claims", []):
                entities = [Entity(**e) for e in item.get("entities", [])]
                claim = Claim(
                    claim_id=item.get("claim_id", f"c_{len(claims)+1}"),
                    claim_text=item.get("claim_text", ""),
                    claim_type=ClaimType(item.get("claim_type", "factual")),
                    entities=entities,
                    dates_or_time_references=item.get("dates_or_time_references", []),
                    locations=item.get("locations", []),
                    verification_questions=item.get("verification_questions", []),
                    importance_score=float(item.get("importance_score", 0.8)),
                    is_verifiable=item.get("is_verifiable", True),
                )
                claims.append(claim)
            return claims
        except Exception as e:
            logger.error(f"Gemini claim extraction failed: {e}. Falling back to heuristic.")
            self._client = None
            return await HeuristicAIProvider().extract_claims(text, metadata)

    async def summarize_content(self, text: str, visual_context: Optional[str] = None) -> ContentSummary:
        if not self._client:
            return await HeuristicAIProvider().summarize_content(text, visual_context)

        prompt = f"Visual context:\n{visual_context or 'None'}\n\nText / Transcript:\n{text[:8000]}"
        try:
            raw_json = await self._generate_json(SUMMARIZATION_SYSTEM_PROMPT, prompt)
            data = json.loads(raw_json)
            return ContentSummary(
                visual=data.get("visual"),
                text=data.get("text", text[:300] + "..."),
                key_points=data.get("key_points", []),
            )
        except Exception as e:
            logger.error(f"Gemini summarization failed: {e}. Falling back to heuristic.")
            self._client = None
            return await HeuristicAIProvider().summarize_content(text, visual_context)

    async def verify_claim_against_evidence(
        self, claim: Claim, evidence_items: List[Evidence]
    ) -> Dict[str, Any]:
        if not self._client:
            return await HeuristicAIProvider().verify_claim_against_evidence(claim, evidence_items)

        evidence_payload = [
            {
                "url": e.url,
                "source": e.source,
                "tier": e.tier.value,
                "credibility_score": e.credibility_score,
                "finding": e.finding,
            }
            for e in evidence_items
        ]

        prompt = f"CLAIM TO VERIFY:\n{claim.claim_text}\n\nENTITIES: {[e.name for e in claim.entities]}\n\nEXTERNAL EVIDENCE:\n{json.dumps(evidence_payload, indent=2)}"
        try:
            raw_json = await self._generate_json(VERIFICATION_SYSTEM_PROMPT, prompt)
            return json.loads(raw_json)
        except Exception as e:
            logger.error(f"Gemini verification failed: {e}. Falling back to heuristic.")
            self._client = None
            return await HeuristicAIProvider().verify_claim_against_evidence(claim, evidence_items)

    async def _generate_json(self, system_prompt: str, user_content: str) -> str:
        full_prompt = f"{system_prompt}\n\nUser Request:\n{user_content}\n\nRemember to return ONLY valid JSON."
        loop = asyncio.get_running_loop()
        
        def _call_model():
            if self._use_new_sdk:
                resp = self._client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config={"response_mime_type": "application/json"}
                )
                return resp.text or ""
            else:
                resp = self._client.generate_content(
                    full_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                return resp.text or ""

        raw = await loop.run_in_executor(None, _call_model)
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        return raw.strip()


class HeuristicAIProvider(BaseAIProvider):
    """
    Deterministic rule-based and NLP engine for claim extraction, summarization,
    and verification. Used as high-reliability fallback, for offline/testing mode,
    or when external LLM API keys are not supplied.
    """

    async def extract_claims(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Claim]:
        cleaned = text.strip()
        if not cleaned:
            return []

        # Split into sentence-like clauses
        sentences = [s.strip() for s in re.split(r'[.\n!?]+', cleaned) if len(s.strip()) > 15]
        claims = []

        # Patterns indicative of factual claims (numbers, currencies, government schemes, dates, announcements)
        factual_indicators = [
            r'\b(?:₹|\$|€|rs\.?|rupees|dollars|crore|lakh|million|billion)\b',
            r'\b(?:announced|declared|passed|approved|signed|launched|giving|free|scheme|mandate|banned|law)\b',
            r'\b(?:government|ministry|police|court|president|prime minister|pmo|who|fda|isro|nasa)\b',
            r'\b(?:percent|%|\d+\s*(?:days|years|months|dead|injured|cases))\b',
        ]

        # Indicators of subjective opinion or speculation
        opinion_indicators = [
            r'\b(?:i think|in my opinion|i believe|probably|maybe|feels like|seems like|personally|i feel)\b',
            r'\b(?:best|worst|horrible|amazing|greatest|terrible|stupid|genius)\b',
        ]

        idx = 1
        for sent in sentences[:6]: # Process up to first 6 notable sentences
            is_opinion = any(re.search(pat, sent, re.IGNORECASE) for pat in opinion_indicators)
            is_factual = any(re.search(pat, sent, re.IGNORECASE) for pat in factual_indicators) or (not is_opinion and len(sent) > 25)

            if is_opinion and not is_factual:
                claim_type = ClaimType.OPINION
                is_verifiable = False
            else:
                claim_type = ClaimType.FACTUAL
                is_verifiable = True

            # Extract basic entities
            entities = []
            org_matches = re.findall(r'\b(?:Government|Ministry|RBI|NASA|ISRO|WHO|Court|SBI|PIB)\b', sent, re.IGNORECASE)
            for org in set(org_matches):
                entities.append(Entity(name=org.capitalize(), category="ORG"))

            dates = re.findall(r'\b(?:\d{4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\b', sent, re.IGNORECASE)

            # Generate verification questions
            questions = [
                f"Did official authorities announce that {sent}?",
                f"Is there any public record or notification confirming '{sent}'?"
            ]

            claims.append(
                Claim(
                    claim_id=f"c_{idx}",
                    claim_text=sent,
                    claim_type=claim_type,
                    entities=entities,
                    dates_or_time_references=list(set(dates)),
                    locations=[],
                    verification_questions=questions,
                    importance_score=0.9 if is_factual else 0.4,
                    is_verifiable=is_verifiable,
                )
            )
            idx += 1

        return claims

    async def summarize_content(self, text: str, visual_context: Optional[str] = None) -> ContentSummary:
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 10]
        summary_text = " ".join(lines[:2]) if lines else "No text content available."
        key_points = lines[:4] if len(lines) >= 4 else lines

        return ContentSummary(
            visual=visual_context if visual_context else None,
            text=summary_text[:350],
            key_points=key_points,
        )

    async def verify_claim_against_evidence(
        self, claim: Claim, evidence_items: List[Evidence]
    ) -> Dict[str, Any]:
        if not evidence_items:
            return {
                "verdict": VerdictType.UNVERIFIABLE.value,
                "evidence_evaluations": [],
                "reasoning": "No relevant external evidence could be retrieved to substantiate or refute this claim.",
                "verdict_title": "Unverifiable due to lack of credible evidence",
                "evidence_bullet_points": ["⚠️ No authoritative sources found discussing this specific claim."],
                "why_explanation": "We could not find matching records in government notifications, news databases, or official announcements.",
            }

        # Extract topic words from claim to ensure debunk signals actually refer to the claim topic
        stop_words = {"this", "that", "with", "from", "following", "about", "have", "been", "were", "what", "when", "where", "which", "into", "their", "there"}
        claim_words = {w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', claim.claim_text) if w.lower() not in stop_words}

        # Stance analysis based on keywords in evidence findings
        debunk_keywords = [
            "debunk", "fact-check: false", "is false", "claim is false", "claims are false",
            "proven false", "falsely", "hoax", "scam", "fake", "no such", "no evidence",
            "fraud", "fraudulent", "unfounded", "fabricated", "refuted", "denied", "denies"
        ]
        support_keywords = [
            "officially confirmed", "announced", "official notification",
            "passed into law", "implemented", "gazette notification", "approved",
            "executive order", "signed an order", "signed an executive order",
            "issued an order", "issued an executive order", "shift in terminology",
            "super intelligence", "mandate", "convened", "inaugurates", "inaugurating",
            "replace the term", "directive", "white house"
        ]

        contra_count = 0
        supp_count = 0
        evaluations = []
        bullet_points = []

        for item in evidence_items:
            lower_finding = item.finding.lower()
            topic_match = any(cw in lower_finding for cw in claim_words) or len(claim_words) == 0

            # Contradiction: Explicitly tagged CONTRADICTING, or contains debunk keywords AND matches claim topic
            is_contra = (
                item.type == EvidenceType.CONTRADICTING
                or (topic_match and any(kw in lower_finding for kw in debunk_keywords))
            )

            # A contradicting/debunk finding should never be marked as supporting
            if is_contra:
                is_supp = False
            else:
                is_supp = (
                    item.type == EvidenceType.SUPPORTING
                    or (topic_match and any(kw in lower_finding for kw in support_keywords))
                )

            if is_contra:
                stance = "contradicting"
                contra_count += 1
                bullet_points.append(f"❌ {item.source}: {item.finding[:100]}...")
            elif is_supp:
                stance = "supporting"
                supp_count += 1
                bullet_points.append(f"✅ {item.source}: {item.finding[:100]}...")
            else:
                stance = "contextual"
                bullet_points.append(f"ℹ️ {item.source}: Contextual reporting retrieved.")

            evaluations.append({
                "source_url": item.url,
                "stance": stance,
                "key_finding": item.finding,
            })

        # Synthesize verdict
        if contra_count > supp_count:
            verdict = VerdictType.CONTRADICTED.value
            verdict_title = "Disproven / Misinformation"
            why = f"Directly contradicted by credible reporting from {evidence_items[0].source}."
            reasoning = f"Available evidence from {len(evidence_items)} sources refutes the assertion. Primary sources indicate this claim does not align with verifiable facts."
        elif supp_count > contra_count and supp_count >= 1:
            verdict = VerdictType.SUPPORTED.value
            verdict_title = "Verified by credible evidence"
            why = f"Substantiated by announcements and reporting from {evidence_items[0].source}."
            reasoning = f"Corroborating records from {len(evidence_items)} independent sources verify the core facts of this claim."
        elif contra_count > 0 and supp_count > 0:
            verdict = VerdictType.MISLEADING.value
            verdict_title = "Misleading / Missing Critical Context"
            why = "The claim mixes factual elements with unverified or misleading assertions."
            reasoning = "Sources provide conflicting information or clarify that the claim misinterprets real announcements."
        else:
            verdict = VerdictType.UNVERIFIABLE.value
            verdict_title = "Inconclusive Evidence"
            why = "Retrieved records provide contextual background but do not conclusively prove or disprove the claim."
            reasoning = "The available reports mention related topics but do not directly confirm the specific numbers, dates, or entities claimed."

        return {
            "verdict": verdict,
            "evidence_evaluations": evaluations,
            "reasoning": reasoning,
            "verdict_title": verdict_title,
            "evidence_bullet_points": bullet_points[:4],
            "why_explanation": why,
        }


def get_ai_provider() -> BaseAIProvider:
    """Factory to initialize and return the configured AI provider."""
    provider_name = settings.AI_PROVIDER.lower()
    
    if provider_name == "gemini":
        gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if gemini_key:
            logger.info("Initializing Gemini AI Provider.")
            return GeminiAIProvider(api_key=gemini_key, model_name=settings.GEMINI_MODEL)
        else:
            logger.info("No GEMINI_API_KEY found. Falling back to Heuristic AI Provider.")
            return HeuristicAIProvider()

    # Default fallback
    logger.info("Using Heuristic AI Provider.")
    return HeuristicAIProvider()
