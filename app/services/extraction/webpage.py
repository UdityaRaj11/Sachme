import httpx
from bs4 import BeautifulSoup
import trafilatura
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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

class WebpageExtractor(BaseExtractor):
    """Extracts article content and metadata from public websites and news portals."""

    async def extract(self, classification: ClassificationResult) -> NormalizedContent:
        url = classification.canonical_url
        logger.info(f"Extracting webpage content from: {url}")

        html_content = ""
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=HEADERS) as client:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    raise ContentExtractionError(
                        f"Failed to fetch webpage at '{url}' (HTTP {resp.status_code}).",
                        url=url,
                        status_code=resp.status_code,
                    )
                html_content = resp.text
        except httpx.RequestError as e:
            logger.error(f"Network error fetching webpage {url}: {e}")
            raise ContentExtractionError(
                f"Network error connecting to destination '{url}': {str(e)}",
                url=url,
            )

        # 1. Trafilatura main body extraction (removes ads, headers, nav, footers)
        extracted_text = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=True,
        )

        # 2. Extract metadata via trafilatura and BeautifulSoup fallback
        meta_info = trafilatura.extract_metadata(html_content)
        soup = BeautifulSoup(html_content, "html.parser")

        title = None
        author = None
        published_date = None

        if meta_info:
            title = meta_info.title
            author = meta_info.author
            published_date = meta_info.date

        if not title:
            # Fallback to OpenGraph / title tag
            og_title = soup.find("meta", property="og:title")
            title = og_title["content"] if og_title and "content" in og_title.attrs else (soup.title.string if soup.title else "Untitled Article")

        if not author:
            og_author = soup.find("meta", property="author") or soup.find("meta", attrs={"name": "author"})
            if og_author and "content" in og_author.attrs:
                author = og_author["content"]

        if not published_date:
            og_time = soup.find("meta", property="article:published_time")
            if og_time and "content" in og_time.attrs:
                published_date = og_time["content"]

        # If trafilatura returned empty (e.g. dynamic client-rendered page), fallback to main tag
        if not extracted_text:
            main_tag = soup.find("main") or soup.find("article") or soup.find("body")
            if main_tag:
                # Remove script and style elements
                for element in main_tag(["script", "style", "nav", "footer", "header", "aside"]):
                    element.extract()
                extracted_text = main_tag.get_text(separator="\n", strip=True)

        if not extracted_text or len(extracted_text.strip()) < 20:
            raise ContentExtractionError(
                f"Could not extract meaningful article or text content from '{url}'. The site may be behind a paywall, login screen, or require JavaScript rendering.",
                url=url,
            )

        summary_preview = extracted_text[:300].replace("\n", " ") + "..."

        return NormalizedContent(
            url=url,
            platform=Platform.WEBPAGE,
            content_type=ContentType.ARTICLE,
            language="en",
            title=title,
            author=author,
            published_date=published_date,
            raw_text=extracted_text,
            transcript=None,
            ocr_text=None,
            visual_description=None,
            metadata={
                "domain": classification.canonical_url.split("/")[2],
                "char_count": len(extracted_text),
            },
            summary=ContentSummary(
                visual=None,
                text=summary_preview,
                key_points=[p.strip() for p in extracted_text.split("\n\n")[:3] if len(p.strip()) > 30],
            ),
        )
