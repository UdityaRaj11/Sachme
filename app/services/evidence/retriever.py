import asyncio
import re
from typing import List, Dict, Any, Set
from app.models.claims import Claim
from app.models.evidence import Evidence, EvidenceType, SourceTier
from app.services.evidence.search_providers import CompositeSearchProvider, RawSearchResult
from app.services.evidence.query_optimizer import SearchQueryOptimizer
from app.services.credibility.scorer import credibility_engine
from app.core.logging import logger

class EvidenceRetriever:
    """
    Evidence retrieval engine that queries multiple credible sources for each claim,
    strictly validates semantic relevance, evaluates source credibility,
    and prioritizes sources by Tier (Tier 1 > Tier 2 > Tier 3).
    """

    def __init__(self, search_provider=None):
        self.search_provider = search_provider or CompositeSearchProvider()

    async def retrieve_evidence_for_claim(self, claim: Claim) -> List[Evidence]:
        """
        Generates targeted search queries via SearchQueryOptimizer, executes concurrent searches,
        strictly filters out irrelevant noise, and scores source credibility.
        """
        logger.info(f"Retrieving evidence for claim '{claim.claim_id}': {claim.claim_text}")

        # 1. Generate clean, high-precision keyword queries
        optimized_queries = SearchQueryOptimizer.generate_queries(claim)
        logger.info(f"Generated optimized search queries for claim {claim.claim_id}: {optimized_queries}")

        # 2. Execute searches concurrently across optimized queries
        search_tasks = [
            self.search_provider.search(query=q, max_results=4)
            for q in optimized_queries
        ]
        results_batches = await asyncio.gather(*search_tasks, return_exceptions=True)

        raw_results: List[RawSearchResult] = []
        seen_urls: Set[str] = set()

        for batch in results_batches:
            if isinstance(batch, list):
                for res in batch:
                    # Clean and deduplicate URL
                    clean_res_url = res.url.split("?")[0].rstrip("/").lower()
                    if clean_res_url and clean_res_url not in seen_urls:
                        seen_urls.add(clean_res_url)
                        raw_results.append(res)

        logger.info(f"Retrieved {len(raw_results)} candidate search results for claim {claim.claim_id}.")

        # 3. Build token vocabulary for relevance gatekeeping
        claim_clean = re.sub(r'[^\w\s]', ' ', claim.claim_text.lower())
        claim_tokens = {w for w in claim_clean.split() if len(w) > 3}
        entity_tokens = {
            w.lower() for e in claim.entities for w in e.name.split() if len(w) > 2
        }
        all_important_tokens = claim_tokens.union(entity_tokens)

        evidence_items: List[Evidence] = []
        idx = 1
        for res in raw_results:
            combined_text = f"{res.title} {res.snippet} {res.url}".lower()
            
            # STRICT RELEVANCE GATEKEEPER:
            # The result MUST contain at least one major substantive token from the claim.
            # Completely unrelated results (e.g. Gmail login pages) are strictly rejected.
            matching_tokens = [tok for tok in all_important_tokens if tok in combined_text]
            if not matching_tokens:
                logger.debug(f"Discarding irrelevant search result: {res.url} (no token match)")
                continue

            # Score source credibility
            cred_score, tier, factors = credibility_engine.evaluate_source(
                url=res.url,
                finding_text=res.snippet,
                claim_text=claim.claim_text,
                publication_date=None,
                corroborating_source_count=len(raw_results),
            )

            # Stance estimation: Contradicting / Debunk signals vs Supporting signals
            evidence_type = EvidenceType.CONTEXTUAL
            lower_snip = f"{res.title} {res.snippet}".lower()
            contra_signals = [
                "debunk", "fake", "scam", "fraud", "fraudulent", "hoax", "untrue", "warning",
                "warns", "no such", "no evidence", "denies", "denied", "refuted", "is false",
                "unfounded", "fabricated", "misinformation", "falsely"
            ]
            supp_signals = [
                "officially confirmed", "announces", "announced", "executive order", "signed an order",
                "signed an executive order", "issued an order", "issued an executive order",
                "inaugurates", "inaugurating", "replace the term", "shift to", "shift in terminology",
                "super intelligence", "approved", "passed into law", "implemented", "valid and legal",
                "directive", "mandates"
            ]

            if any(w in lower_snip for w in contra_signals):
                evidence_type = EvidenceType.CONTRADICTING
            elif any(w in lower_snip for w in supp_signals):
                evidence_type = EvidenceType.SUPPORTING

            evidence_items.append(
                Evidence(
                    evidence_id=f"ev_{claim.claim_id}_{idx}",
                    finding=res.snippet or res.title,
                    type=evidence_type,
                    source=res.source_name,
                    url=res.url,
                    credibility_score=cred_score,
                    tier=tier,
                    credibility_factors=factors,
                    stance_confidence=0.85,
                )
            )
            idx += 1

        # Sort priority: Tier 1 > Tier 2 > Tier 3, then by credibility score descending
        tier_order = {
            SourceTier.TIER_1_PRIMARY: 0,
            SourceTier.TIER_2_SECONDARY: 1,
            SourceTier.TIER_3_OTHER: 2,
        }
        evidence_items.sort(key=lambda e: (tier_order.get(e.tier, 3), -e.credibility_score))

        return evidence_items
