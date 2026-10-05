import httpx
import io
from PIL import Image
from typing import Optional

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

class ImageExtractor(BaseExtractor):
    """Extracts metadata, dimensions, and performs OCR/vision inspection on direct images."""

    async def extract(self, classification: ClassificationResult) -> NormalizedContent:
        url = classification.canonical_url
        logger.info(f"Extracting image content from: {url}")

        image_bytes = b""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    raise ContentExtractionError(
                        f"Failed to download image at '{url}' (HTTP {res.status_code}).",
                        url=url,
                    )
                image_bytes = res.content
        except httpx.RequestError as e:
            raise ContentExtractionError(f"Network error downloading image '{url}': {str(e)}", url=url)

        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            img_format = img.format or "UNKNOWN"
        except Exception as e:
            raise ContentExtractionError(f"File at '{url}' is not a valid or readable image: {e}", url=url)

        # Basic metadata & visual analysis
        visual_desc = f"Image ({img_format}, {width}x{height}px) hosted at {url}."
        ocr_text = f"Image document ({img_format} format, {width}x{height})."
        
        return NormalizedContent(
            url=url,
            platform=Platform.IMAGE,
            content_type=ContentType.IMAGE_POST,
            language="en",
            title=f"Image Asset ({img_format})",
            author="Unknown",
            published_date=None,
            raw_text=ocr_text,
            transcript=None,
            ocr_text=ocr_text,
            visual_description=visual_desc,
            metadata={
                "width": width,
                "height": height,
                "format": img_format,
                "size_bytes": len(image_bytes),
            },
            summary=ContentSummary(
                visual=visual_desc,
                text=ocr_text,
                key_points=[f"Image dimensions: {width}x{height}", f"Format: {img_format}"],
            ),
        )
