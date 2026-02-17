"""Health check Pydantic models."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    message: str
    liblouis_version: str
    asr_status: str
    asr_model: str | None = None
    asr_device: str | None = None
    tts_status: str | None = None
    tts_voices: list[str] | None = None
    ocr_status: str | None = None
    ocr_languages: list[str] | None = None
