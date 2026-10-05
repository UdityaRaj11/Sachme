import pytest
from app.services.classifier.url_classifier import URLClassifier
from app.models.content import Platform, ContentType, MediaType, ExtractionStrategy
from app.core.exceptions import UnsupportedContentError, InvalidUrlError

def test_classify_webpage():
    res = URLClassifier.classify("https://www.thehindu.com/news/national/article12345.ece")
    assert res.platform == Platform.WEBPAGE
    assert res.content_type == ContentType.ARTICLE
    assert res.extraction_strategy == ExtractionStrategy.WEBPAGE_EXTRACTOR
    assert res.is_supported is True

def test_classify_youtube_video():
    res = URLClassifier.classify("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert res.platform == Platform.YOUTUBE
    assert res.content_type == ContentType.VIDEO
    assert res.target_id == "dQw4w9WgXcQ"
    assert res.extraction_strategy == ExtractionStrategy.YOUTUBE_EXTRACTOR

def test_classify_youtube_shorts():
    res = URLClassifier.classify("https://www.youtube.com/shorts/abc123xyz")
    assert res.platform == Platform.YOUTUBE_SHORTS
    assert res.content_type == ContentType.SHORT
    assert res.target_id == "abc123xyz"

def test_classify_twitter_post():
    res = URLClassifier.classify("https://twitter.com/user/status/17890123456789")
    assert res.platform == Platform.TWITTER_X
    assert res.content_type == ContentType.POST
    assert res.target_id == "17890123456789"
    assert res.extraction_strategy == ExtractionStrategy.SOCIAL_EXTRACTOR

def test_classify_instagram_reel():
    res = URLClassifier.classify("https://www.instagram.com/reel/C7-xyz123/")
    assert res.platform == Platform.INSTAGRAM
    assert res.content_type == ContentType.REEL
    assert res.target_id == "C7-xyz123"

def test_classify_direct_image():
    res = URLClassifier.classify("https://example.com/evidence_photo.jpg")
    assert res.platform == Platform.IMAGE
    assert res.content_type == ContentType.IMAGE_POST
    assert res.media_type == MediaType.IMAGE

def test_classify_direct_text():
    res = URLClassifier.classify(direct_text="Breaking: Government announces new scholarship policy.")
    assert res.platform == Platform.TEXT_DIRECT
    assert res.content_type == ContentType.TEXT

def test_unsupported_executable_or_format():
    with pytest.raises(UnsupportedContentError):
        URLClassifier.classify("https://example.com/malware_payload.exe")

def test_ssrf_disallowed_local_url():
    with pytest.raises(InvalidUrlError):
        URLClassifier.classify("http://localhost:8000/internal-admin")
