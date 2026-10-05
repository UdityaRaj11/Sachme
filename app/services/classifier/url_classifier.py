import re
from urllib.parse import urlparse, parse_qs
from typing import Optional
from app.models.content import (
    Platform,
    ContentType,
    MediaType,
    ExtractionStrategy,
    ClassificationResult,
)
from app.core.exceptions import UnsupportedContentError, InvalidUrlError
from app.core.security import validate_and_sanitize_url

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")

class URLClassifier:
    """
    Classifies submitted URLs and requests into platforms, content types,
    media formats, and selects the optimal extraction pipeline.
    """

    @staticmethod
    def classify(url: Optional[str] = None, direct_text: Optional[str] = None) -> ClassificationResult:
        if direct_text and not url:
            return ClassificationResult(
                platform=Platform.TEXT_DIRECT,
                content_type=ContentType.TEXT,
                media_type=MediaType.TEXT,
                extraction_strategy=ExtractionStrategy.TEXT_EXTRACTOR,
                is_supported=True,
                canonical_url="text://direct-input",
            )

        if not url:
            raise InvalidUrlError("Either a valid 'url' or 'direct_text' must be provided.")

        clean_url = validate_and_sanitize_url(url)
        parsed = urlparse(clean_url)
        netloc = parsed.netloc.lower()
        orig_path = parsed.path
        lower_path = orig_path.lower()

        # Remove 'www.' prefix for pattern matching
        domain = netloc.replace("www.", "")

        # 1. YouTube Video or Short
        if domain in ("youtube.com", "m.youtube.com", "youtu.be"):
            return URLClassifier._classify_youtube(clean_url, domain, orig_path, parsed.query)

        # 2. X / Twitter
        if domain in ("twitter.com", "x.com", "mobile.twitter.com"):
            return URLClassifier._classify_twitter(clean_url, orig_path)

        # 3. Instagram
        if domain in ("instagram.com", "instagr.am"):
            return URLClassifier._classify_instagram(clean_url, orig_path)

        # 4. Direct Image URL
        if any(lower_path.endswith(ext) for ext in IMAGE_EXTENSIONS):
            return ClassificationResult(
                platform=Platform.IMAGE,
                content_type=ContentType.IMAGE_POST,
                media_type=MediaType.IMAGE,
                extraction_strategy=ExtractionStrategy.IMAGE_EXTRACTOR,
                is_supported=True,
                canonical_url=clean_url,
            )

        # 5. Unsupported streaming/binary/private protocols
        if domain in ("torproject.org", "darkweb.onion") or lower_path.endswith((".exe", ".zip", ".tar", ".bin", ".iso")):
            raise UnsupportedContentError(
                message=f"Unsupported format or protocol: The resource at '{clean_url}' is not a verifiable media or web document.",
                platform="unknown",
                url=clean_url,
            )

        # 6. Standard Webpage / Article
        if domain:
            return ClassificationResult(
                platform=Platform.WEBPAGE,
                content_type=ContentType.ARTICLE,
                media_type=MediaType.TEXT,
                extraction_strategy=ExtractionStrategy.WEBPAGE_EXTRACTOR,
                is_supported=True,
                canonical_url=clean_url,
            )

        raise UnsupportedContentError(
            message=f"Unable to classify or route destination for '{clean_url}'.",
            platform="unknown",
            url=clean_url,
        )

    @staticmethod
    def _classify_youtube(clean_url: str, domain: str, path: str, query: str) -> ClassificationResult:
        if "/shorts/" in path.lower():
            idx = path.lower().find("/shorts/") + len("/shorts/")
            short_id = path[idx:].split("/")[0].split("?")[0]
            return ClassificationResult(
                platform=Platform.YOUTUBE_SHORTS,
                content_type=ContentType.SHORT,
                media_type=MediaType.MIXED,
                extraction_strategy=ExtractionStrategy.YOUTUBE_EXTRACTOR,
                is_supported=True,
                canonical_url=f"https://www.youtube.com/shorts/{short_id}",
                target_id=short_id,
            )

        video_id = None
        if domain == "youtu.be":
            video_id = path.strip("/").split("/")[0].split("?")[0]
        else:
            qs = parse_qs(query)
            if "v" in qs and qs["v"]:
                video_id = qs["v"][0]
            elif "/embed/" in path.lower():
                idx = path.lower().find("/embed/") + len("/embed/")
                video_id = path[idx:].split("/")[0].split("?")[0]

        if not video_id:
            raise UnsupportedContentError(
                message="YouTube URL must point to a specific video or short, not a generic channel or search page.",
                platform="youtube",
                url=clean_url,
            )

        return ClassificationResult(
            platform=Platform.YOUTUBE,
            content_type=ContentType.VIDEO,
            media_type=MediaType.MIXED,
            extraction_strategy=ExtractionStrategy.YOUTUBE_EXTRACTOR,
            is_supported=True,
            canonical_url=f"https://www.youtube.com/watch?v={video_id}",
            target_id=video_id,
        )

    @staticmethod
    def _classify_twitter(clean_url: str, path: str) -> ClassificationResult:
        match = re.search(r"/status(?:es)?/(\d+)", path, re.IGNORECASE)
        if not match:
            raise UnsupportedContentError(
                message="X/Twitter URL must point to a specific post/tweet status, not a profile or feed.",
                platform="twitter_x",
                url=clean_url,
            )
        tweet_id = match.group(1)
        return ClassificationResult(
            platform=Platform.TWITTER_X,
            content_type=ContentType.POST,
            media_type=MediaType.MIXED,
            extraction_strategy=ExtractionStrategy.SOCIAL_EXTRACTOR,
            is_supported=True,
            canonical_url=f"https://x.com/i/status/{tweet_id}",
            target_id=tweet_id,
        )

    @staticmethod
    def _classify_instagram(clean_url: str, path: str) -> ClassificationResult:
        reel_match = re.search(r"/reel(?:s)?/([^/?#]+)", path, re.IGNORECASE)
        post_match = re.search(r"/p/([^/?#]+)", path, re.IGNORECASE)

        if reel_match:
            reel_id = reel_match.group(1)
            return ClassificationResult(
                platform=Platform.INSTAGRAM,
                content_type=ContentType.REEL,
                media_type=MediaType.MIXED,
                extraction_strategy=ExtractionStrategy.SOCIAL_EXTRACTOR,
                is_supported=True,
                canonical_url=f"https://www.instagram.com/reel/{reel_id}/",
                target_id=reel_id,
            )
        elif post_match:
            post_id = post_match.group(1)
            return ClassificationResult(
                platform=Platform.INSTAGRAM,
                content_type=ContentType.POST,
                media_type=MediaType.MIXED,
                extraction_strategy=ExtractionStrategy.SOCIAL_EXTRACTOR,
                is_supported=True,
                canonical_url=f"https://www.instagram.com/p/{post_id}/",
                target_id=post_id,
            )

        raise UnsupportedContentError(
            message="Instagram URL must point to a specific post or reel (e.g., /p/code/ or /reel/code/).",
            platform="instagram",
            url=clean_url,
        )
