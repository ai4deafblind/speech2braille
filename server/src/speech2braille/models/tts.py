"""TTS-related Pydantic models."""

from pydantic import BaseModel, Field


class BrailleToSpeechRequest(BaseModel):
    """Request model for braille-to-speech synthesis."""

    braille: str = Field(..., description="Braille text to convert to speech", min_length=1)
    table: str = Field(..., description="Braille table filename for back-translation")
    voice_id: str | None = Field(None, description="Voice model ID (uses default if not specified)")
    length_scale: float | None = Field(None, description="Speech speed override (1.0 = normal)")
    noise_scale: float | None = Field(None, description="Audio variation override")
    noise_w: float | None = Field(None, description="Phoneme duration variation override")


class VoiceInfo(BaseModel):
    """Information about an available TTS voice."""

    voice_id: str = Field(..., description="Voice model identifier")
    language: str = Field(..., description="Language code (e.g., en_US)")
    quality: str = Field(..., description="Voice quality level (e.g., medium)")
