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
