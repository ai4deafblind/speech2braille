"""Health check router."""

from fastapi import APIRouter, Request

from speech2braille.models.health import HealthResponse
from speech2braille.services.asr_service import ASRService
from speech2braille.services.braille_service import BrailleService
from speech2braille.services.ocr_service import OCRService
from speech2braille.services.tts_service import TTSService

router = APIRouter(tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Health check endpoint with ASR and TTS status."""
    asr_service: ASRService = request.app.state.asr_service
    braille_service: BrailleService = request.app.state.braille_service
    tts_service: TTSService = request.app.state.tts_service
    ocr_service: OCRService = request.app.state.ocr_service

    return HealthResponse(
        status="ok",
        message="Brailler API is running",
        liblouis_version=braille_service.get_version(),
        asr_status=asr_service.get_status(),
        asr_model=asr_service.get_model_name(),
        asr_device=asr_service.device if asr_service.is_loaded else None,
        tts_status=tts_service.get_status(),
        tts_voices=tts_service.get_voice_ids() if tts_service.is_loaded else None,
        ocr_status=ocr_service.get_status(),
        ocr_languages=ocr_service.get_loaded_languages() if ocr_service.is_loaded else None,
    )
