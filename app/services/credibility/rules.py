import tldextract
from urllib.parse import urlparse
from typing import Tuple, Dict, Any, List
from app.models.evidence import SourceTier
from app.config import load_credibility_config

class DomainClassifier:
    """Classifies web domains into Source Tiers and calculates baseline domain authority."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_credibility_config()
        self.gov_tlds: List[str] = self.config.get("government_tlds", [".gov", ".gov.in", ".nic.in", ".mil", ".gov.uk"])
        self.edu_tlds: List[str] = self.config.get("academic_tlds", [".edu", ".ac.in", ".ac.uk"])
        self.authoritative_domains: Dict[str, int] = self.config.get("known_authoritative_domains", {})
        self.fact_checkers: Dict[str, int] = self.config.get("known_fact_checkers", {})
        self.reputable_news: Dict[str, int] = self.config.get("known_reputable_news", {})
        self.unreliable_domains: Dict[str, int] = self.config.get("unreliable_or_satire_domains", {})

    def update_config(self, new_config: Dict[str, Any]):
        """Dynamically update domain rules from new configuration."""
        self.config = new_config
        self.gov_tlds = self.config.get("government_tlds", self.gov_tlds)
        self.edu_tlds = self.config.get("academic_tlds", self.edu_tlds)
        self.authoritative_domains = self.config.get("known_authoritative_domains", self.authoritative_domains)
        self.fact_checkers = self.config.get("known_fact_checkers", self.fact_checkers)
        self.reputable_news = self.config.get("known_reputable_news", self.reputable_news)
        self.unreliable_domains = self.config.get("unreliable_or_satire_domains", self.unreliable_domains)

    def classify_url(self, url: str) -> Tuple[SourceTier, float, bool]:
        """
        Analyzes a URL.
        Returns:
            Tuple of (SourceTier, domain_reputation_score, is_primary_source)
        """
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            ext = tldextract.extract(url)
            registered_domain = getattr(ext, "top_domain_under_public_suffix", None) or ext.registered_domain
            registered_domain = registered_domain.lower() if registered_domain else ""
            suffix = f".{ext.suffix}".lower()
        except Exception:
            return SourceTier.TIER_3_OTHER, 40.0, False

        # 1. Check direct matches in authoritative / official registry (Tier 1)
        if registered_domain in self.authoritative_domains or netloc in self.authoritative_domains:
            score = float(self.authoritative_domains.get(registered_domain) or self.authoritative_domains.get(netloc, 95))
            return SourceTier.TIER_1_PRIMARY, score, True

        # 2. Check Government TLDs (Tier 1)
        for gov_tld in self.gov_tlds:
            if suffix.endswith(gov_tld) or netloc.endswith(gov_tld):
                # High authority government source, primary
                return SourceTier.TIER_1_PRIMARY, 92.0, True

        # 3. Check Academic TLDs (.edu, .ac.uk) (Tier 2 / Primary Scientific)
        for edu_tld in self.edu_tlds:
            if suffix.endswith(edu_tld) or netloc.endswith(edu_tld):
                return SourceTier.TIER_2_SECONDARY, 88.0, True

        # 4. Check Fact-Checking organizations (Tier 2)
        if registered_domain in self.fact_checkers or netloc in self.fact_checkers:
            score = float(self.fact_checkers.get(registered_domain) or self.fact_checkers.get(netloc, 90))
            return SourceTier.TIER_2_SECONDARY, score, False

        # 5. Check Established News agencies (Tier 2)
        if registered_domain in self.reputable_news or netloc in self.reputable_news:
            score = float(self.reputable_news.get(registered_domain) or self.reputable_news.get(netloc, 85))
            return SourceTier.TIER_2_SECONDARY, score, False

        # 6. Check Known Unreliable / Satire / Propaganda domains (Tier 3)
        if registered_domain in self.unreliable_domains or netloc in self.unreliable_domains:
            score = float(self.unreliable_domains.get(registered_domain) or self.unreliable_domains.get(netloc, 10))
            return SourceTier.TIER_3_OTHER, score, False

        # 7. General Web default (Tier 3)
        return SourceTier.TIER_3_OTHER, 50.0, False
