from typing import List, Dict, Any
from app.models.claims import Claim
from app.models.evidence import Evidence, SourceTier
from app.models.verification import VerdictType, UserFacingUI, ClaimEvidenceItem

class ExplanationGenerator:
    """
    Generates human-readable explanations following the chain:
    EVIDENCE → REASONING → VERDICT.
    Also produces formatted UI view data matching Section 11 mockup.
    """

    @staticmethod
    def generate_explanation(
        claim: Claim,
        verdict: VerdictType,
        evidence_items: List[Evidence],
        ai_reasoning: str,
        ai_why: str,
    ) -> str:
        """
        Builds the explanation string adhering to:
        EVIDENCE -> REASONING -> VERDICT
        """
        if not evidence_items:
            return (
                f"EVIDENCE: A targeted search of government registries and authoritative news archives "
                f"yielded no supporting records for the claim '{claim.claim_text}'. "
                f"REASONING: Without credible empirical documentation or official announcements, "
                f"the assertion cannot be substantiated. "
                f"VERDICT: {verdict.value}."
            )

        top_evidence = evidence_items[:2]
        sources_summary = ", ".join(f"{e.source} (Credibility: {e.credibility_score}/100)" for e in top_evidence)

        explanation = (
            f"EVIDENCE: Cross-checked against {len(evidence_items)} independent sources including {sources_summary}. "
            f"Key finding: \"{top_evidence[0].finding}\". "
            f"REASONING: {ai_reasoning} "
            f"VERDICT: {verdict.value}."
        )
        return explanation

    @staticmethod
    def build_user_facing_ui(
        claim: Claim,
        verdict: VerdictType,
        confidence: int,
        evidence_items: List[Evidence],
        bullet_points: List[str],
        why_text: str,
    ) -> UserFacingUI:
        """Constructs UI display model matching Section 11 mock."""
        # 1. Badge label
        badge_map = {
            VerdictType.SUPPORTED: "✅ Verified Credible",
            VerdictType.MISLEADING: "🚨 Potentially Misleading",
            VerdictType.CONTRADICTED: "❌ False / Disproven",
            VerdictType.UNVERIFIABLE: "⚠️ Unverified / Inconclusive",
            VerdictType.OPINION: "💬 Opinion / Non-Factual",
        }
        badge = badge_map.get(verdict, "ℹ️ Fact Check Result")

        # 2. Verdict Title
        title_map = {
            VerdictType.SUPPORTED: "Substantiated by Authoritative Sources",
            VerdictType.MISLEADING: "Misleading Context / Selective Claims",
            VerdictType.CONTRADICTED: "Disproven / Very likely a scam or misinformation",
            VerdictType.UNVERIFIABLE: "Insufficient reliable evidence to confirm",
            VerdictType.OPINION: "Subjective viewpoint, not an empirical fact",
        }
        verdict_title = title_map.get(verdict, "Verification Complete")

        # 3. Evidence Sources List
        evidence_sources = [
            {"source": e.source, "url": e.url, "credibility": f"{e.credibility_score}/100"}
            for e in evidence_items[:4]
        ]

        # 4. Formatted bullet points
        points = bullet_points or [
            f"• Source {e.source}: {e.finding[:120]}..." for e in evidence_items[:3]
        ]

        return UserFacingUI(
            badge_label=badge,
            claim_detected=claim.claim_text,
            evidence_points=points,
            verdict_title=verdict_title,
            confidence_display=f"{confidence}%",
            why_explanation=why_text,
            evidence_sources=evidence_sources,
        )
