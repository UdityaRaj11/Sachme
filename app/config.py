import os
from pathlib import Path
from typing import Dict, Any, List
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App General Settings
    APP_NAME: str = "TruthFirewall - AI Information Firewall"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API & Security
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "truth-firewall-super-secret-key-change-in-prod"
    ALLOWED_ORIGINS: List[str] = ["*"]
    MAX_URL_LENGTH: int = 2048
    REQUEST_TIMEOUT_SECONDS: float = 30.0
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # AI Provider Settings
    # Supports 'gemini', 'openai', or 'heuristic'
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Search / Evidence Retrieval Settings
    # Supports 'duckduckgo', 'tavily', 'serpapi', or 'mock'
    SEARCH_PROVIDER: str = "duckduckgo"
    TAVILY_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    SEARCH_MAX_RESULTS_PER_CLAIM: int = 5
    
    # Cache Settings
    CACHE_TTL_SECONDS: int = 3600 # 1 hour
    MAX_CACHE_SIZE: int = 1000
    
    # Credibility Config File
    CONFIG_FILE_PATH: str = str(BASE_DIR / "config" / "credibility_weights.yaml")

settings = Settings()

def load_credibility_config() -> Dict[str, Any]:
    """Loads credibility scoring configuration and domain registries from YAML."""
    path = Path(settings.CONFIG_FILE_PATH)
    if not path.is_file():
        return {
            "weights": {
                "tier_weight": 0.35,
                "domain_reputation": 0.25,
                "relevance": 0.15,
                "primary_source_bonus": 0.10,
                "recency": 0.08,
                "corroboration": 0.07,
            },
            "tier_base_scores": {
                "tier_1_official": 90,
                "tier_2_high_credibility": 75,
                "tier_3_general": 45,
            },
            "government_tlds": [".gov", ".nic.in", ".gov.in", ".mil", ".gov.uk"],
            "academic_tlds": [".edu", ".ac.in", ".ac.uk"],
            "known_authoritative_domains": {},
            "known_fact_checkers": {},
            "known_reputable_news": {},
            "unreliable_or_satire_domains": {},
        }
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
