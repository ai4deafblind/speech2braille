"""OCR router for image-to-text and image-to-braille endpoints."""

import asyncio
import contextlib
import io
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from PIL import Image

from speech2braille.models.ocr import OCRResponse, OCRToBrailleResponse
from speech2braille.services.braille_service import BrailleService
from speech2braille.services.ocr_service import OCRService

router = APIRouter(prefix="/api", tags=["ocr"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}


def _resize_if_needed(content: bytes, max_dim: int) -> bytes:
    """Resize image if its largest dimension exceeds max_dim."""
    img = Image.open(io.BytesIO(content))
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format=img.format or "PNG")
        return buf.getvalue()
    return content


def _validate_image(image: UploadFile, max_size: int) -> None:
    """Validate uploaded image file."""
    filename = image.filename or "image.png"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported image format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


@router.post("/ocr", response_model=OCRResponse)
async def ocr_recognize(
    request: Request,
    image: UploadFile = File(..., description="Image file (PNG, JPG, BMP, TIFF, WebP)"),
    language: str | None = Query(default=None, description="OCR language code (e.g., 'en', 'fr', 'ch')"),
) -> OCRResponse:
    """Recognize text from an image using RapidOCR PP-OCRv5.

    Returns recognized text lines with confidence scores and bounding boxes.
    """
    ocr_service: OCRService = request.app.state.ocr_service

    if not ocr_service.is_loaded:
        if ocr_service.is_loading:
            raise HTTPException(503, "OCR model is loading...")
        elif ocr_service.error:
            raise HTTPException(500, f"OCR model failed: {ocr_service.error}")
        else:
            raise HTTPException(503, "OCR model not loaded")

    _validate_image(image, ocr_service.ocr_config.max_image_size)

    content = await image.read()
    if len(content) > ocr_service.ocr_config.max_image_size:
        raise HTTPException(413, f"Image too large. Maximum size: {ocr_service.ocr_config.max_image_size} bytes")

    content = _resize_if_needed(content, ocr_service.ocr_config.max_side_len)

    suffix = Path(image.filename or "image.png").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await asyncio.to_thread(ocr_service.recognize, tmp_path, language)
        return OCRResponse(**result)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)


@router.post("/ocr-to-braille", response_model=OCRToBrailleResponse)
async def ocr_to_braille(
    request: Request,
    image: UploadFile = File(..., description="Image file (PNG, JPG, BMP, TIFF, WebP)"),
    language: str | None = Query(default=None, description="OCR language code (e.g., 'en', 'fr', 'ch')"),
    braille_table: str = Query(default="en-ueb-g2.ctb", description="Braille translation table"),
) -> OCRToBrailleResponse:
    """Full pipeline: Image -> OCR -> Text -> Braille.

    Recognizes text from an image and translates it to braille.
    """
    ocr_service: OCRService = request.app.state.ocr_service
    braille_service: BrailleService = request.app.state.braille_service

    if not ocr_service.is_loaded:
        if ocr_service.is_loading:
            raise HTTPException(503, "OCR model is loading...")
        elif ocr_service.error:
            raise HTTPException(500, f"OCR model failed: {ocr_service.error}")
        else:
            raise HTTPException(503, "OCR model not loaded")

    _validate_image(image, ocr_service.ocr_config.max_image_size)

    content = await image.read()
    if len(content) > ocr_service.ocr_config.max_image_size:
        raise HTTPException(413, f"Image too large. Maximum size: {ocr_service.ocr_config.max_image_size} bytes")

    content = _resize_if_needed(content, ocr_service.ocr_config.max_side_len)

    suffix = Path(image.filename or "image.png").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Step 1: OCR
        ocr_result = await asyncio.to_thread(ocr_service.recognize, tmp_path, language)

        # Step 2: Translate to braille
        try:
            braille = braille_service.translate(ocr_result["full_text"], braille_table)
        except Exception as e:
            raise HTTPException(400, f"Braille translation failed: {e!s}")

        return OCRToBrailleResponse(
            lines=ocr_result["lines"],
            full_text=ocr_result["full_text"],
            braille=braille,
            language=ocr_result["language"],
            table_used=braille_table,
            success=True,
        )
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
