"""Braille-related Pydantic models."""

from pydantic import BaseModel, Field


class BrailleTable(BaseModel):
    """Represents a braille translation table."""

    filename: str = Field(..., description="Table filename (e.g., en-us-g2.ctb)")
    display_name: str = Field(..., description="Human-readable name")
    language: str = Field(..., description="Language code (ISO 639)")
    grade: str | None = Field(None, description="Braille grade (g1, g2, etc.)")


class TranslationRequest(BaseModel):
    """Request model for text-to-braille translation."""

    text: str = Field(..., description="Text to translate to braille", min_length=1)
    table: str = Field(..., description="Braille table filename to use")


class TranslationResponse(BaseModel):
    """Response model for braille translation."""

    original_text: str = Field(..., description="Original input text")
    braille: str = Field(..., description="Translated braille text (Unicode braille)")
    table_used: str = Field(..., description="Table filename used for translation")
    success: bool = Field(..., description="Whether translation succeeded")


class BackTranslationRequest(BaseModel):
    """Request model for braille-to-text back-translation."""

    braille: str = Field(..., description="Braille text to translate back", min_length=1)
    table: str = Field(..., description="Braille table filename to use")


class BackTranslationResponse(BaseModel):
    """Response model for back-translation."""

    original_braille: str = Field(..., description="Original braille input")
    text: str = Field(..., description="Back-translated text")
    table_used: str = Field(..., description="Table filename used")
    success: bool = Field(..., description="Whether back-translation succeeded")
