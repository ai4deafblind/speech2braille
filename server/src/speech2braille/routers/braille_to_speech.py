"""Braille-to-speech router."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from speech2braille.models.tts import BrailleToSpeechRequest, VoiceInfo
from speech2braille.services.braille_service import BrailleService
from speech2braille.services.tts_service import TTSService

router = APIRouter(prefix="/api", tags=["braille-to-speech"])


@router.post("/braille-to-speech")
async def braille_to_speech(request: Request, body: BrailleToSpeechRequest) -> Response:
    """Convert braille text to speech audio.

    Back-translates braille to text, then synthesizes speech.
    Returns WAV audio with metadata in custom headers.
    """
    braille_service: BrailleService = request.app.state.braille_service
    tts_service: TTSService = request.app.state.tts_service

    # Back-translate braille to text
    try:
        text = braille_service.back_translate(body.braille, body.table)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Back-translation failed: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Back-translation produced empty text")

    # Synthesize speech
    try:
        wav_bytes = tts_service.synthesize(
            text=text,
            voice_id=body.voice_id,
            length_scale=body.length_scale,
            noise_scale=body.noise_scale,
            noise_w=body.noise_w,
            volume=body.volume,
            normalize_audio=body.normalize_audio,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    voice_id = body.voice_id or tts_service.tts_config.default_voice_id

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "X-Back-Translated-Text": text,
            "X-Voice-Id": voice_id,
            "X-Table-Used": body.table,
            "Access-Control-Expose-Headers": "X-Back-Translated-Text, X-Voice-Id, X-Table-Used",
        },
    )


@router.get("/voices", response_model=list[VoiceInfo])
async def list_voices(request: Request) -> list[VoiceInfo]:
    """List available TTS voices."""
    tts_service: TTSService = request.app.state.tts_service

    return [VoiceInfo(**info) for info in tts_service.get_voice_info()]
