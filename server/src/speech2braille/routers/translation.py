"""Braille translation router."""

from fastapi import APIRouter, HTTPException, Request

from speech2braille.models.braille import (
    BackTranslationRequest,
    BackTranslationResponse,
    TranslationRequest,
    TranslationResponse,
)
from speech2braille.services.braille_service import BrailleService

router = APIRouter(prefix="/api", tags=["translation"])


@router.post("/translate", response_model=TranslationResponse)
async def translate_to_braille(request: Request, body: TranslationRequest) -> TranslationResponse:
    """Translate text to braille using the specified table.

    Returns Unicode braille characters that can be displayed or sent to a braille display.
    """
    braille_service: BrailleService = request.app.state.braille_service

    try:
        braille = braille_service.translate(body.text, body.table)
        return TranslationResponse(
            original_text=body.text,
            braille=braille,
            table_used=body.table,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Translation failed: {str(e)}")


@router.post("/back-translate", response_model=BackTranslationResponse)
async def back_translate_from_braille(request: Request, body: BackTranslationRequest) -> BackTranslationResponse:
    """Back-translate braille to text using the specified table.

    Useful for processing input from braille keyboards.
    """
    braille_service: BrailleService = request.app.state.braille_service

    try:
        text = braille_service.back_translate(body.braille, body.table)
        return BackTranslationResponse(
            original_braille=body.braille,
            text=text,
            table_used=body.table,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Back-translation failed: {str(e)}")


@router.get("/test-translation", response_model=TranslationResponse)
async def test_translation(request: Request) -> TranslationResponse:
    """Test endpoint with a sample translation using English UEB Grade 2.

    Useful for verifying the system is working without client setup.
    """
    braille_service: BrailleService = request.app.state.braille_service

    test_text = "Hello, world! This is a test of the braille translation system."
    test_table = "en-ueb-g2.ctb"

    try:
        braille = braille_service.translate(test_text, test_table)
        return TranslationResponse(
            original_text=test_text,
            braille=braille,
            table_used=test_table,
            success=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test translation failed: {str(e)}. Is liblouis installed with tables?",
        )
