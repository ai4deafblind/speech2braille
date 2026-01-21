"""Speech transcription router."""

import contextlib
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from speech2braille.models.transcription import SpeechToBrailleResponse, TranscriptionResponse
from speech2braille.services.asr_service import ASRService
from speech2braille.services.braille_service import BrailleService

router = APIRouter(prefix="/api", tags=["speech"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_speech(
    request: Request,
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, OGG, etc.)"),
    language: str | None = None,
    task: str = "transcribe",
    word_timestamps: bool = False,
) -> TranscriptionResponse:
    """Transcribe speech from an audio file using faster-whisper.

    Accepts various audio formats and returns transcribed text.
    The model auto-detects language if not specified.

    Args:
        audio: Audio file upload
        language: Optional language code (e.g., 'en', 'es')
        task: 'transcribe' (in original language) or 'translate' (to English)
        word_timestamps: Include word-level timestamps in response
    """
    asr_service: ASRService = request.app.state.asr_service

    if not asr_service.is_loaded:
        if asr_service.is_loading:
            raise HTTPException(503, "ASR model is loading...")
        elif asr_service.error:
            raise HTTPException(500, f"ASR model failed: {asr_service.error}")
        else:
            raise HTTPException(503, "ASR model not loaded")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename or "audio.wav").suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await asr_service.transcribe(
            tmp_path,
            language=language,
            task=task,
            word_timestamps=word_timestamps,
        )
        return TranscriptionResponse(**result)

    except RuntimeError as e:
        raise HTTPException(500, str(e))

    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)


@router.post("/speech-to-braille", response_model=SpeechToBrailleResponse)
async def speech_to_braille(
    request: Request,
    audio: UploadFile = File(..., description="Audio file"),
    braille_table: str = "en-ueb-g2.ctb",
    language: str | None = None,
    task: str = "transcribe",
    word_timestamps: bool = False,
) -> SpeechToBrailleResponse:
    """Complete pipeline: Speech -> Text -> Braille

    Transcribes audio and immediately translates to braille.
    This is the main endpoint for the deafblind communication device.

    Args:
        audio: Audio file with speech
        braille_table: Braille table to use (default: English UEB Grade 2)
        language: Optional speech language code
        task: 'transcribe' or 'translate'
        word_timestamps: Include word-level timestamps in response
    """
    asr_service: ASRService = request.app.state.asr_service
    braille_service: BrailleService = request.app.state.braille_service

    if not asr_service.is_loaded:
        if asr_service.is_loading:
            raise HTTPException(503, "ASR model is loading...")
        elif asr_service.error:
            raise HTTPException(500, f"ASR model failed: {asr_service.error}")
        else:
            raise HTTPException(503, "ASR model not loaded")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename or "audio.wav").suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Step 1: Transcribe speech
        transcription_result = await asr_service.transcribe(
            tmp_path,
            language=language,
            task=task,
            word_timestamps=word_timestamps,
        )
        transcribed_text = transcription_result["text"]

        # Step 2: Translate to braille
        try:
            braille = braille_service.translate(transcribed_text, braille_table)

            return SpeechToBrailleResponse(
                transcribed_text=transcribed_text,
                braille=braille,
                language=transcription_result.get("language"),
                table_used=braille_table,
                audio_duration=transcription_result.get("duration"),
                segments=transcription_result.get("segments"),
                success=True,
            )

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Braille translation failed: {str(e)}")

    except RuntimeError as e:
        raise HTTPException(500, str(e))

    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
