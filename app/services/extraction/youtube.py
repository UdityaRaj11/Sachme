import httpx
from typing import Optional, List, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from app.services.extraction.base import BaseExtractor
from app.models.content import (
    ClassificationResult,
    NormalizedContent,
    ContentSummary,
    Platform,
    ContentType,
)
from app.core.exceptions import ContentExtractionError
from app.core.logging import logger

class YouTubeExtractor(BaseExtractor):
    """
    Extracts metadata, spoken transcripts, and keyframe visual assets
    from YouTube videos and YouTube Shorts.
    """

    async def extract(self, classification: ClassificationResult) -> NormalizedContent:
        url = classification.canonical_url
        video_id = classification.target_id

        if not video_id:
            raise ContentExtractionError("Cannot extract YouTube content without a valid video ID.", url=url)

        is_short = (classification.platform == Platform.YOUTUBE_SHORTS)
        logger.info(f"Extracting {'YouTube Short' if is_short else 'YouTube Video'} info for ID: {video_id}")

        # 1. Fetch official YouTube oEmbed metadata (Title, Creator Channel, Author URL)
        title = "YouTube Short" if is_short else "YouTube Video"
        author = "Unknown Creator"
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(oembed_url)
                if res.status_code == 200:
                    data = res.json()
                    title = data.get("title", title)
                    author = data.get("author_name", author)
        except Exception as e:
            logger.warning(f"Could not retrieve oEmbed data for {video_id}: {e}")

        # 2. Extract spoken transcript / audio captions
        transcript_text = ""
        has_transcript = False
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=['en', 'hi', 'es', 'fr', 'auto']
            )
            pieces = [item['text'] for item in transcript_list]
            transcript_text = " ".join(pieces)
            has_transcript = True
        except (TranscriptsDisabled, NoTranscriptFound):
            logger.warning(f"No closed captions/transcripts found for YouTube video {video_id}.")
        except Exception as e:
            logger.warning(f"Transcript extraction error for {video_id}: {e}")

        # 3. Keyframe & thumbnail asset reference
        # YouTube provides high-resolution poster keyframes for videos and shorts at:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        # 4. Construct raw extracted text and visual framing
        format_label = "YouTube Short (vertical short-form video)" if is_short else "YouTube Video"
        if not has_transcript:
            raw_text = (
                f"[{format_label}]\nTitle: {title}\nChannel: {author}\n"
                f"[Note: Spoken audio captions/subtitles are not publicly provided for this video]."
            )
            summary_text = f"{format_label} titled '{title}' by channel '{author}'. Spoken captions unavailable; metadata extracted."
        else:
            raw_text = f"[{format_label}]\nTitle: {title}\nChannel: {author}\nSpoken Transcript:\n{transcript_text}"
            summary_text = f"Transcript summary of '{title}': {transcript_text[:250]}..."

        visual_desc = (
            f"Visual keyframe analysis for {format_label} '{title}' by channel '{author}'. "
            f"Keyframe frame asset available at {thumbnail_url}."
        )

        return NormalizedContent(
            url=url,
            platform=classification.platform,
            content_type=classification.content_type,
            language="en",
            title=title,
            author=author,
            published_date=None,
            raw_text=raw_text,
            transcript=transcript_text if has_transcript else None,
            ocr_text=None,
            visual_description=visual_desc,
            metadata={
                "video_id": video_id,
                "is_short": is_short,
                "has_transcript": has_transcript,
                "thumbnail_url": thumbnail_url,
                "word_count": len(transcript_text.split()) if has_transcript else 0,
            },
            summary=ContentSummary(
                visual=visual_desc,
                text=summary_text,
                key_points=[
                    f"Title: {title}",
                    f"Channel: {author}",
                    "Format: Short-form video" if is_short else "Format: Long-form video"
                ],
            ),
        )
