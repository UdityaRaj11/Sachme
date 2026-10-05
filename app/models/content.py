from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Platform(str, Enum):
    YOUTUBE = "youtube"
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM = "instagram"
    TWITTER_X = "twitter_x"
    WEBPAGE = "webpage"
    IMAGE = "image"
    TEXT_DIRECT = "text_direct"
    OTHER_SOCIAL = "other_social"
    UNSUPPORTED = "unsupported"


class ContentType(str, Enum):
    ARTICLE = "article"
    VIDEO = "video"
    SHORT = "short"
    REEL = "reel"
    POST = "post"
    IMAGE_POST = "image_post"
    TEXT = "text"
    UNKNOWN = "unknown"


class MediaType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"


class ExtractionStrategy(str, Enum):
    WEBPAGE_EXTRACTOR = "webpage_extractor"
    YOUTUBE_EXTRACTOR = "youtube_extractor"
    SOCIAL_EXTRACTOR = "social_extractor"
    IMAGE_EXTRACTOR = "image_extractor"
    TEXT_EXTRACTOR = "text_extractor"
    UNSUPPORTED = "unsupported"


class ClassificationResult(BaseModel):
    """Result of classifying a submitted URL or input."""
    platform: Platform
    content_type: ContentType
    media_type: MediaType
    extraction_strategy: ExtractionStrategy
    is_supported: bool = True
    unsupported_reason: Optional[str] = None
    canonical_url: str
    target_id: Optional[str] = None # e.g. video_id or tweet_id


class ContentSummary(BaseModel):
    """Multi-perspective summary of extracted content."""
    visual: Optional[str] = Field(default=None, description="Visual summary of video frames or images")
    text: str = Field(description="Core text or spoken/transcript summary")
    key_points: List[str] = Field(default_factory=list, description="Key extracted factual takeaways")


class NormalizedContent(BaseModel):
    """
    Standardized internal representation of content across any platform.
    Distinguishes raw extracted facts from any inferred context.
    """
    url: str
    platform: Platform
    content_type: ContentType
    language: str = "en"
    title: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    raw_text: Optional[str] = None
    transcript: Optional[str] = None
    ocr_text: Optional[str] = None
    visual_description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    summary: ContentSummary
