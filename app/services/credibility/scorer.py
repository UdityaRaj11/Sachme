from typing import Dict, Any, Optional
from datetime import datetime
from app.config import load_credibility_config
from app.models.evidence import SourceTier, CredibilityFactors
from app.services.credibility.rules import DomainClassifier

class SourceCredibilityEngine:
    """
    Configurable source credibility scoring engine.
    Computes a normalized 0-100 credibility score using configurable weights.
    
    CRITICAL PRINCIPLE:
    Source credibility indicates the reliability and epistemic rigor of the source,
    NOT whether a specific claim is automatically true. A Tier 1 government website
    is highly credible as an official record, but claims must still be cross-examined.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_credibility_config()
        self.domain_classifier = DomainClassifier(self.config)
        self._load_weights()

    def _load_weights(self):
        weights = self.config.get("weights", {})
        self.w_tier = float(weights.get("tier_weight", 0.35))
        self.w_reputation = float(weights.get("domain_reputation", 0.25))
        self.w_relevance = float(weights.get("relevance", 0.15))
        self.w_primary = float(weights.get("primary_source_bonus", 0.10))
        self.w_recency = float(weights.get("recency", 0.08))
        self.w_corroboration = float(weights.get("corroboration", 0.07))

        self.tier_base_scores = self.config.get("tier_base_scores", {
            "tier_1_official": 90.0,
            "tier_2_high_credibility": 75.0,
            "tier_3_general": 45.0,
        })

    def update_weights(self, new_weights: Dict[str, float]):
        """Allows updating scoring weights dynamically without redeployment."""
        current_weights = self.config.get("weights", {})
        for k, v in new_weights.items():
            if v is not None:
                current_weights[k] = v
        self.config["weights"] = current_weights
        self._load_weights()

    def evaluate_source(
        self,
        url: str,
        finding_text: str,
        claim_text: str,
        publication_date: Optional[str] = None,
        corroborating_source_count: int = 1,
    ) -> tuple[int, SourceTier, CredibilityFactors]:
        """
        Evaluates a source URL and evidence finding against a claim.
        Returns:
            Tuple of (final_credibility_score_0_to_100, SourceTier, CredibilityFactors)
        """
        # 1. Classify domain & tier
        tier, domain_reputation, is_primary = self.domain_classifier.classify_url(url)

        # Baseline tier score
        if tier == SourceTier.TIER_1_PRIMARY:
            tier_score = float(self.tier_base_scores.get("tier_1_official", 90.0))
        elif tier == SourceTier.TIER_2_SECONDARY:
            tier_score = float(self.tier_base_scores.get("tier_2_high_credibility", 75.0))
        else:
            tier_score = float(self.tier_base_scores.get("tier_3_general", 45.0))

        # 2. Relevance calculation (lexical and key token overlap)
        claim_tokens = set(claim_text.lower().split())
        finding_tokens = set(finding_text.lower().split())
        overlap = claim_tokens.intersection(finding_tokens)
        relevance_ratio = min(1.0, (len(overlap) / max(1, len(claim_tokens) * 0.5)))
        relevance_score = max(40.0, relevance_ratio * 100.0)

        # 3. Primary vs Secondary Source score
        primary_source_score = 95.0 if is_primary else 70.0

        # 4. Recency score
        recency_score = self._compute_recency_score(publication_date)

        # 5. Corroboration score (boosted if multiple independent sources verify)
        if corroborating_source_count >= 3:
            corroboration_score = 95.0
        elif corroborating_source_count == 2:
            corroboration_score = 80.0
        else:
            corroboration_score = 65.0

        # Weighted calculation
        total_weight = (
            self.w_tier
            + self.w_reputation
            + self.w_relevance
            + self.w_primary
            + self.w_recency
            + self.w_corroboration
        )
        if total_weight <= 0:
            total_weight = 1.0

        weighted_sum = (
            (tier_score * self.w_tier)
            + (domain_reputation * self.w_reputation)
            + (relevance_score * self.w_relevance)
            + (primary_source_score * self.w_primary)
            + (recency_score * self.w_recency)
            + (corroboration_score * self.w_corroboration)
        )

        final_score = int(round(weighted_sum / total_weight))
        final_score = max(0, min(100, final_score))

        factors = CredibilityFactors(
            tier_score=tier_score,
            domain_reputation_score=domain_reputation,
            relevance_score=relevance_score,
            primary_source_score=primary_source_score,
            recency_score=recency_score,
            corroboration_score=corroboration_score,
            raw_details={
                "url": url,
                "is_primary": is_primary,
                "tier": tier.value,
                "corroborating_count": corroborating_source_count,
            }
        )

        return final_score, tier, factors

    def _compute_recency_score(self, date_str: Optional[str]) -> float:
        """Calculates temporal freshness score (0-100)."""
        if not date_str:
            return 75.0 # Neutral default for evergreen/undated sources

        try:
            # Simple parse attempts
            year_match = [int(s) for s in date_str.split() if s.isdigit() and len(s) == 4]
            if year_match:
                year = year_match[0]
                current_year = datetime.now().year
                diff = current_year - year
                if diff <= 1:
                    return 95.0
                elif diff <= 3:
                    return 85.0
                elif diff <= 5:
                    return 70.0
                else:
                    return 55.0
        except Exception:
            pass

        return 75.0

# Singleton credibility engine instance
credibility_engine = SourceCredibilityEngine()
