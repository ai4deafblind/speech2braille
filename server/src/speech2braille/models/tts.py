"""TTS-related Pydantic models."""

from enum import Enum

from pydantic import BaseModel, Field


class TTSPreset(str, Enum):
    """Pre-configured TTS settings for common use cases."""

    NATURAL = "natural"
    CLEAR = "clear"
    FAST = "fast"
    SLOW = "slow"
    LOUD = "loud"


class BrailleToSpeechRequest(BaseModel):
    """Request model for braille-to-speech synthesis."""

    braille: str = Field(..., description="Braille text to convert to speech", min_length=1)
    table: str = Field(..., description="Braille table filename for back-translation")
    voice_id: str | None = Field(None, description="Voice model ID (uses default if not specified)")
    # Existing parameters with validation
    length_scale: float | None = Field(None, ge=0.5, le=2.0, description="Speech speed (0.5=half, 1.0=normal, 2.0=double)")
    noise_scale: float | None = Field(None, ge=0.0, le=1.5, description="Speech variation (lower=robotic, higher=expressive)")
    noise_w: float | None = Field(None, ge=0.0, le=1.5, description="Phoneme duration variation")
    # New parameters
    volume: float | None = Field(None, ge=0.0, le=2.0, description="Volume (0.0=mute, 1.0=normal, 2.0=double)")
    normalize_audio: bool | None = Field(None, description="Normalize audio to consistent volume")
    preset: TTSPreset | None = Field(None, description="Use preset configuration")


class VoiceInfo(BaseModel):
    """Information about an available TTS voice."""

    voice_id: str = Field(..., description="Voice model identifier")
    language: str = Field(..., description="Language code (e.g., en_US)")
    quality: str = Field(..., description="Voice quality level (e.g., medium)")
