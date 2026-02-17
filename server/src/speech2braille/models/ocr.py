"""OCR Pydantic models."""

from pydantic import BaseModel


class OCRLine(BaseModel):
    """A single recognized text line from OCR."""

    text: str
    confidence: float
    bbox: list[list[int]]


class OCRResponse(BaseModel):
    """OCR-only response."""

    lines: list[OCRLine]
    full_text: str
    language: str
    success: bool


class OCRToBrailleResponse(BaseModel):
    """Full OCR-to-Braille pipeline response."""

    lines: list[OCRLine]
    full_text: str
    braille: str
    language: str
    table_used: str
    success: bool
