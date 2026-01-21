"""Transcription-related Pydantic models."""

from pydantic import BaseModel, Field


class WordTimestamp(BaseModel):
    """Word-level timestamp information."""

    word: str = Field(..., description="The word text")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    probability: float = Field(..., description="Word confidence probability")


class SegmentTimestamp(BaseModel):
    """Segment-level information with word timestamps."""

    id: int = Field(..., description="Segment ID")
    start: float = Field(..., description="Segment start time in seconds")
    end: float = Field(..., description="Segment end time in seconds")
    text: str = Field(..., description="Segment text")
    words: list[WordTimestamp] | None = Field(None, description="Word-level timestamps")
    avg_logprob: float = Field(..., description="Average log probability")
    no_speech_prob: float = Field(..., description="No speech probability")


class TranscriptionResponse(BaseModel):
    """Response model for speech transcription."""

    text: str = Field(..., description="Transcribed text")
    language: str | None = Field(None, description="Detected or specified language")
    duration: float | None = Field(None, description="Audio duration in seconds")
    segments: list[SegmentTimestamp] | None = Field(None, description="Segment timestamps with words")
    success: bool = Field(..., description="Whether transcription succeeded")


class SpeechToBrailleResponse(BaseModel):
    """Response for combined speech-to-text-to-braille pipeline."""

    transcribed_text: str = Field(..., description="Transcribed speech")
    braille: str = Field(..., description="Braille output")
    language: str | None = Field(None, description="Detected language")
    table_used: str = Field(..., description="Braille table used")
    audio_duration: float | None = Field(None, description="Audio duration")
    segments: list[SegmentTimestamp] | None = Field(None, description="Segment timestamps")
    success: bool = Field(..., description="Success status")
