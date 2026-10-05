import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

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

class SocialMediaExtractor(BaseExtractor):
    """Extracts public post and reel content from X/Twitter and Instagram."""

    async def extract(self, classification: ClassificationResult) -> NormalizedContent:
        url = classification.canonical_url
        logger.info(f"Extracting social post from {classification.platform}: {url}")

        if classification.platform == Platform.TWITTER_X:
            return await self._extract_twitter(classification)
        elif classification.platform == Platform.INSTAGRAM:
            return await self._extract_instagram(classification)
        else:
            raise ContentExtractionError(
                f"Platform '{classification.platform}' is not currently configured for direct social extraction.",
                url=url,
            )

    async def _extract_twitter(self, classification: ClassificationResult) -> NormalizedContent:
        url = classification.canonical_url
        tweet_id = classification.target_id
        
        # Twitter's publish oEmbed API is open and public
        oembed_url = f"https://publish.twitter.com/oembed?url={url}"
        author = "Twitter User"
        text_content = ""

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(oembed_url)
                if res.status_code == 200:
                    data = res.json()
                    author = data.get("author_name", author)
                    html = data.get("html", "")
                    soup = BeautifulSoup(html, "html.parser")
                    # Tweet body is in blockquote
                    bq = soup.find("blockquote")
                    if bq:
                        p = bq.find("p")
                        text_content = p.get_text(separator=" ", strip=True) if p else bq.get_text(separator=" ", strip=True)
        except Exception as e:
            logger.warning(f"Failed to fetch Twitter oEmbed for {url}: {e}")

        if not text_content:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        og_desc = soup.find("meta", property="og:description")
                        if og_desc and "content" in og_desc.attrs:
                            text_content = og_desc["content"]
            except Exception:
                pass

        if not text_content:
            raise ContentExtractionError(
                f"Could not extract tweet text from '{url}'. The post may be deleted, suspended, or from a private account.",
                url=url,
            )

        return NormalizedContent(
            url=url,
            platform=Platform.TWITTER_X,
            content_type=ContentType.POST,
            language="en",
            title=f"Post by {author}",
            author=author,
            published_date=None,
            raw_text=text_content,
            transcript=None,
            ocr_text=None,
            visual_description=None,
            metadata={"tweet_id": tweet_id},
            summary=ContentSummary(
                visual=None,
                text=text_content,
                key_points=[text_content[:150]],
            ),
        )

    async def _extract_instagram(self, classification: ClassificationResult) -> NormalizedContent:
        url = classification.canonical_url
        target_id = classification.target_id
        is_reel = (classification.content_type == ContentType.REEL)
        caption = ""
        author = "Instagram Creator"
        poster_frame_url = None

        # Fetch public OpenGraph tags (simulating social crawler headers)
        headers = {
            "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    # 1. Caption extraction
                    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
                    if og_desc and "content" in og_desc.attrs:
                        raw_caption = og_desc["content"]
                        # Instagram descriptions often look like: '12K likes, 400 comments - author on date: "actual caption..."'
                        if ':"' in raw_caption:
                            caption = raw_caption.split(':"', 1)[1].rstrip('"')
                        else:
                            caption = raw_caption

                    # 2. Author extraction
                    og_title = soup.find("meta", property="og:title")
                    if og_title and "content" in og_title.attrs:
                        raw_title = og_title["content"]
                        if "on Instagram" in raw_title:
                            author = raw_title.split("on Instagram")[0].strip()
                        else:
                            author = raw_title

                    # 3. Poster frame keyframe
                    og_image = soup.find("meta", property="og:image")
                    if og_image and "content" in og_image.attrs:
                        poster_frame_url = og_image["content"]
        except Exception as e:
            logger.warning(f"Failed to fetch Instagram preview for {url}: {e}")

        # Epistemic Rule: If Instagram's login wall prevents accessing the reel caption or content,
        # fail gracefully with an explicit error rather than hallucinating caption or audio.
        if not caption:
            raise ContentExtractionError(
                f"Instagram {'Reel' if is_reel else 'Post'} at '{url}' cannot be extracted without an active authenticated session, or the account is private.",
                url=url,
            )

        format_label = "Instagram Reel (video)" if is_reel else "Instagram Post"
        visual_desc = (
            f"Visual keyframe analysis for {format_label} by {author}. "
            f"Keyframe image available at {poster_frame_url}."
            if poster_frame_url else f"Visual context for {format_label} (ID: {target_id})."
        )

        return NormalizedContent(
            url=url,
            platform=Platform.INSTAGRAM,
            content_type=classification.content_type,
            language="en",
            title=f"{format_label} by {author}",
            author=author,
            published_date=None,
            raw_text=f"[{format_label}]\nAuthor: {author}\nCaption: {caption}",
            transcript=None,
            ocr_text=None,
            visual_description=visual_desc,
            metadata={
                "target_id": target_id,
                "is_reel": is_reel,
                "poster_frame_url": poster_frame_url,
            },
            summary=ContentSummary(
                visual=visual_desc,
                text=caption,
                key_points=[
                    f"Creator: {author}",
                    f"Format: {format_label}",
                    f"Caption excerpt: {caption[:120]}..."
                ],
            ),
        )
