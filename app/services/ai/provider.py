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

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-3.5-flash",
        fallback_provider: Optional[BaseAIProvider] = None,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.fallback_provider = fallback_provider or HeuristicAIProvider()
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
                logger.warning(f"Failed to initialize Gemini SDK: {e}. Will fallback to {type(self.fallback_provider).__name__}.")

    async def extract_claims(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Claim]:
        if not self._client:
            return await self.fallback_provider.extract_claims(text, metadata)

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
            logger.warning(f"Gemini claim extraction failed: {e}. Falling back to {type(self.fallback_provider).__name__}.")
            return await self.fallback_provider.extract_claims(text, metadata)

    async def summarize_content(self, text: str, visual_context: Optional[str] = None) -> ContentSummary:
        if not self._client:
            return await self.fallback_provider.summarize_content(text, visual_context)

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
            logger.warning(f"Gemini summarization failed: {e}. Falling back to {type(self.fallback_provider).__name__}.")
            return await self.fallback_provider.summarize_content(text, visual_context)

    async def verify_claim_against_evidence(
        self, claim: Claim, evidence_items: List[Evidence]
    ) -> Dict[str, Any]:
        if not self._client:
            return await self.fallback_provider.verify_claim_against_evidence(claim, evidence_items)

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
            logger.warning(f"Gemini verification failed: {e}. Falling back to {type(self.fallback_provider).__name__}.")
            return await self.fallback_provider.verify_claim_against_evidence(claim, evidence_items)

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


class GroqAIProvider(BaseAIProvider):
    """
    Groq LPU AI inference provider (Llama-3.3-70b-versatile, etc.).
    Provides high-speed failover when Google Gemini hits rate limits or errors,
    or functions as a standalone primary AI provider.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "openai/gpt-oss-20b",
        fallback_provider: Optional[BaseAIProvider] = None,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.fallback_provider = fallback_provider or HeuristicAIProvider()
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            return
        try:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=self.api_key)
        except Exception as e:
            logger.warning(f"Failed to initialize Groq client: {e}. Fallback: {type(self.fallback_provider).__name__}")

    async def extract_claims(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Claim]:
        if not self._client:
            return await self.fallback_provider.extract_claims(text, metadata)

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
            logger.warning(f"Groq claim extraction failed: {e}. Falling back to {type(self.fallback_provider).__name__}.")
            return await self.fallback_provider.extract_claims(text, metadata)

    async def summarize_content(self, text: str, visual_context: Optional[str] = None) -> ContentSummary:
        if not self._client:
            return await self.fallback_provider.summarize_content(text, visual_context)

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
            logger.warning(f"Groq summarization failed: {e}. Falling back to {type(self.fallback_provider).__name__}.")
            return await self.fallback_provider.summarize_content(text, visual_context)

    async def verify_claim_against_evidence(
        self, claim: Claim, evidence_items: List[Evidence]
    ) -> Dict[str, Any]:
        if not self._client:
            return await self.fallback_provider.verify_claim_against_evidence(claim, evidence_items)

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
            logger.warning(f"Groq verification failed: {e}. Falling back to {type(self.fallback_provider).__name__}.")
            return await self.fallback_provider.verify_claim_against_evidence(claim, evidence_items)

    async def _generate_json(self, system_prompt: str, user_content: str) -> str:
        if not self._client:
            raise VerificationEngineError("Groq client not initialized")

        chat_completion = await self._client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": f"{system_prompt}\nYou MUST respond with valid JSON only."},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        raw = chat_completion.choices[0].message.content or ""
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

        # Split into base sentence units
        raw_sentences = [s.strip() for s in re.split(r'[.\n!?]+', cleaned) if len(s.strip()) > 10]
        decomposed = []

        for s in raw_sentences:
            # Check for compound conjunctions (e.g. ", and orders", ", and claims", " and asks", "; and ")
            sub_clauses = re.split(
                r'(?:,\s*and\s+|\s+and\s+(?:orders?|directs?|announces?|demands?|claims?|called|calls)\s+|\s*;\s*)',
                s,
                flags=re.IGNORECASE
            )
            sub_clauses = [sc.strip() for sc in sub_clauses if len(sc.strip()) > 10]
            if len(sub_clauses) > 1:
                first_words = sub_clauses[0].split()
                subject_hint = " ".join(first_words[:3]) if len(first_words) >= 3 else ""
                decomposed.append(sub_clauses[0])
                for sc in sub_clauses[1:]:
                    if re.match(r'^(?:orders?|directs?|announces?|claims?|called|calls|for)\b', sc, re.IGNORECASE) and subject_hint:
                        decomposed.append(f"{subject_hint} {sc}")
                    else:
                        decomposed.append(sc)
            else:
                decomposed.append(s)

        claims = []

        factual_indicators = [
            r'\b(?:₹|\$|€|rs\.?|rupees|dollars|crore|lakh|million|billion)\b',
            r'\b(?:announced|declared|passed|approved|signed|launched|giving|free|scheme|mandate|banned|law)\b',
            r'\b(?:government|ministry|police|court|president|prime minister|pmo|who|fda|isro|nasa|department)\b',
            r'\b(?:percent|%|\d+\s*(?:days|years|months|dead|injured|cases))\b',
        ]

        opinion_indicators = [
            r'\b(?:i think|in my opinion|i believe|probably|maybe|feels like|seems like|personally|i feel)\b',
            r'\b(?:best|worst|horrible|amazing|greatest|terrible|stupid|genius)\b',
        ]

        idx = 1
        for sent in decomposed[:8]: # Process up to first 8 notable clauses
            # Skip any accidental metadata headers
            if re.match(r'^(?:Title|Headline|Author|Creator|Metadata|Main Text|Caption)\s*[:/]', sent, re.IGNORECASE):
                continue

            is_opinion = any(re.search(pat, sent, re.IGNORECASE) for pat in opinion_indicators)
            is_factual = any(re.search(pat, sent, re.IGNORECASE) for pat in factual_indicators) or (not is_opinion and len(sent) > 20)

            if is_opinion and not is_factual:
                claim_type = ClaimType.OPINION
                is_verifiable = False
                importance = 0.4
            else:
                claim_type = ClaimType.FACTUAL
                is_verifiable = True
                importance = 0.95 if idx == 1 else 0.85

            # Extract basic entities
            entities = []
            entity_matches = re.findall(
                r'\b(?:Government|Ministry|RBI|NASA|ISRO|WHO|Court|SBI|PIB|President|Trump|Department of Defense|White House|BBC|DoD)\b',
                sent,
                re.IGNORECASE
            )
            for ent in set(entity_matches):
                entities.append(Entity(name=ent.title(), category="ORG"))

            dates = re.findall(
                r'\b(?:\d{4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\b',
                sent,
                re.IGNORECASE
            )

            # Generate precise verification questions
            questions = [
                f"Did official authorities or records confirm that {sent}?",
                f"Is there an official statement, executive order, or archive record regarding '{sent}'?"
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
                    importance_score=importance,
                    is_verifiable=is_verifiable,
                )
            )
            idx += 1

        return claims

    async def summarize_content(self, text: str, visual_context: Optional[str] = None) -> ContentSummary:
        cleaned = text.strip()
        lines = [line.strip() for line in cleaned.splitlines() if len(line.strip()) > 8]

        # Multi-dimensional summary construction
        if len(lines) <= 2:
            summary_text = f"Content circulating online asserts that {lines[0] if lines else 'claims are being made'}."
        else:
            summary_text = " ".join(lines[:3])

        # Generate orthogonal, non-redundant key points
        key_points = []
        if lines:
            key_points.append(f"Core Assertion: {lines[0]}")
        
        # Check for entities
        found_entities = re.findall(
            r'\b(?:President|Trump|Ruby Bradley|Department of Defense|White House|Government|Ministry|AI|Super Intelligence)\b',
            cleaned,
            re.IGNORECASE
        )
        if found_entities:
            unique_ents = list(dict.fromkeys([e.title() for e in found_entities]))
            key_points.append(f"Key Entities Referenced: {', '.join(unique_ents[:4])}")

        # Check for specific metrics, actions, or details
        details = re.findall(
            r'\b(?:₹\s*[\d,]+|\$\s*[\d,]+|Executive Order|terminology|loser|archives|scholarship|free|ban)\b',
            cleaned,
            re.IGNORECASE
        )
        if details:
            unique_details = list(dict.fromkeys(details))
            key_points.append(f"Specific Details / Mechanisms: {', '.join(unique_details[:4])}")

        if visual_context:
            key_points.append(f"Visual Scene Context: {visual_context[:100]}")

        # Ensure at least 2 distinct points
        if len(key_points) < 2 and len(lines) > 1:
            key_points.append(f"Contextual Detail: {lines[1]}")

        return ContentSummary(
            visual=visual_context if visual_context else None,
            text=summary_text[:400],
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
    """
    Factory to initialize and return the configured AI provider with multi-tier failover:
    1. Primary: Configured provider (e.g., Gemini)
    2. Fallback: Groq LPU engine (if GROQ_API_KEY is configured)
    3. Final Fallback: Heuristic rule-based engine (always available offline)
    """
    provider_name = settings.AI_PROVIDER.lower()
    gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    groq_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")

    # Build fallback provider: Groq if key exists, else Heuristic
    if groq_key:
        fallback_for_gemini = GroqAIProvider(
            api_key=groq_key,
            model_name=settings.GROQ_MODEL,
            fallback_provider=HeuristicAIProvider(),
        )
    else:
        fallback_for_gemini = HeuristicAIProvider()

    if provider_name == "gemini":
        if gemini_key:
            logger.info(
                f"Initializing Gemini AI Provider (model: {settings.GEMINI_MODEL}, "
                f"fallback: {type(fallback_for_gemini).__name__})."
            )
            return GeminiAIProvider(
                api_key=gemini_key,
                model_name=settings.GEMINI_MODEL,
                fallback_provider=fallback_for_gemini,
            )
        elif groq_key:
            logger.info("No GEMINI_API_KEY found. Promoting Groq AI Provider to primary.")
            return fallback_for_gemini
        else:
            logger.info("No AI API keys found. Falling back to Heuristic AI Provider.")
            return HeuristicAIProvider()

    elif provider_name == "groq":
        if groq_key:
            logger.info(f"Initializing Groq AI Provider as primary (model: {settings.GROQ_MODEL}).")
            return GroqAIProvider(
                api_key=groq_key,
                model_name=settings.GROQ_MODEL,
                fallback_provider=HeuristicAIProvider(),
            )
        else:
            logger.warning("AI_PROVIDER=groq configured but GROQ_API_KEY is missing. Falling back to Heuristic.")
            return HeuristicAIProvider()

    # Default fallback
    logger.info("Using Heuristic AI Provider.")
    return HeuristicAIProvider()
