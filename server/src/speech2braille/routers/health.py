"""Health check router."""

from fastapi import APIRouter, Request

from speech2braille.models.health import HealthResponse
from speech2braille.services.asr_service import ASRService
from speech2braille.services.braille_service import BrailleService

router = APIRouter(tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Health check endpoint with ASR status."""
    asr_service: ASRService = request.app.state.asr_service
    braille_service: BrailleService = request.app.state.braille_service

    return HealthResponse(
        status="ok",
        message="Brailler API is running",
        liblouis_version=braille_service.get_version(),
        asr_status=asr_service.get_status(),
        asr_model=asr_service.get_model_name(),
        asr_device=asr_service.device if asr_service.is_loaded else None,
    )
