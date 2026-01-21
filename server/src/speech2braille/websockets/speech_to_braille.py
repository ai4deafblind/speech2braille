"""WebSocket handler for real-time speech-to-braille streaming."""

import contextlib
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field

import numpy as np
import soundfile as sf
from fastapi import WebSocket, WebSocketDisconnect

from speech2braille.config import WebSocketConfig
from speech2braille.services.asr_service import ASRService
from speech2braille.services.braille_service import BrailleService

logger = logging.getLogger(__name__)


@dataclass
class StreamingSession:
    """Tracks state for a streaming speech-to-braille session."""

    # Audio buffering
    audio_buffer: list[np.ndarray] = field(default_factory=list)
    buffer_duration: float = 0.0
    is_recording: bool = False

    # Context carryover for better continuity
    last_transcription: str = ""  # Text from previous chunk for context prompt
    accumulated_text: str = ""  # Full session transcript
    accumulated_braille: str = ""  # Full session braille

    # Session config
    config: dict = field(default_factory=lambda: {
        "language": "en",
        "task": "transcribe",
        "braille_table": "",
        "word_timestamps": True,
    })

    def reset_buffer(self) -> None:
        """Reset the audio buffer while preserving context."""
        self.audio_buffer = []
        self.buffer_duration = 0.0

    def reset_session(self) -> None:
        """Reset entire session state for new recording."""
        self.audio_buffer = []
        self.buffer_duration = 0.0
        self.is_recording = False
        self.last_transcription = ""
        self.accumulated_text = ""
        self.accumulated_braille = ""


class SpeechToBrailleWebSocket:
    """Handler for real-time speech-to-braille WebSocket connections."""

    def __init__(
        self,
        asr_service: ASRService,
        braille_service: BrailleService,
        config: WebSocketConfig,
    ) -> None:
        self.asr_service = asr_service
        self.braille_service = braille_service
        self.config = config

    async def handle(self, websocket: WebSocket) -> None:
        """Handle a WebSocket connection for speech-to-braille streaming."""
        await websocket.accept()
        logger.info("WebSocket connected")

        try:
            if not self.asr_service.is_loaded:
                await websocket.send_json({"type": "error", "message": "ASR model not loaded"})
                await websocket.close()
                return

            await websocket.send_json({
                "type": "ready",
                "model": self.asr_service.get_model_name(),
                "device": self.asr_service.device,
            })

            # Initialize session with StreamingSession dataclass
            session = StreamingSession()
            session.config["braille_table"] = self.braille_service.default_table

            while True:
                data = await websocket.receive()

                # Config/command messages
                if "text" in data:
                    await self._handle_text_message(websocket, data["text"], session)

                # Audio chunks
                elif "bytes" in data:
                    await self._handle_audio_chunk(websocket, data["bytes"], session)

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def _handle_text_message(
        self,
        websocket: WebSocket,
        text: str,
        session: StreamingSession,
    ) -> None:
        """Handle a text message (config or command)."""
        try:
            message = json.loads(text)

            if message.get("type") == "config":
                new_config = message.get("config", {})
                # Validate language - it cannot be null or empty for whisper.cpp
                if "language" in new_config and not new_config["language"]:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Language is required and cannot be null or empty",
                    })
                    return
                session.config.update(new_config)
                await websocket.send_json({"type": "config_updated", "config": session.config})

            elif message.get("type") == "start_recording":
                # Reset session for new recording
                session.reset_session()
                session.is_recording = True
                await websocket.send_json({"type": "recording_started"})

            elif message.get("type") == "stop_recording":
                # Process any remaining audio
                if session.audio_buffer and session.buffer_duration >= self.config.min_duration:
                    await self._process_audio(websocket, session)

                # Send final accumulated result if we have content
                if session.accumulated_text:
                    await websocket.send_json({
                        "type": "final_result",
                        "transcribed_text": session.accumulated_text,
                        "braille": session.accumulated_braille,
                        "language": session.config.get("language"),
                        "table_used": session.config.get("braille_table"),
                        "success": True,
                    })

                session.reset_session()
                await websocket.send_json({"type": "recording_stopped"})

        except json.JSONDecodeError as e:
            await websocket.send_json({"type": "error", "message": f"Invalid JSON: {str(e)}"})
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def _handle_audio_chunk(
        self,
        websocket: WebSocket,
        audio_bytes: bytes,
        session: StreamingSession,
    ) -> None:
        """Handle an audio chunk."""
        try:
            audio_chunk = np.frombuffer(audio_bytes, dtype=np.float32)
            if len(audio_chunk) == 0:
                return

            session.audio_buffer.append(audio_chunk)
            session.buffer_duration = sum(len(c) for c in session.audio_buffer) / self.config.sample_rate

            if not session.is_recording:
                session.is_recording = True
                await websocket.send_json({"type": "speech_started"})

            # Process every chunk_duration seconds for real-time output
            if session.buffer_duration >= self.config.chunk_duration and session.buffer_duration >= self.config.min_duration:
                await self._process_audio(websocket, session)
                session.reset_buffer()

            # Force process if buffer limit reached (safety fallback)
            elif session.buffer_duration >= self.config.buffer_limit:
                await self._process_audio(websocket, session)
                session.reset_buffer()

        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def _process_audio(
        self,
        websocket: WebSocket,
        session: StreamingSession,
    ) -> None:
        """Process buffered audio and send results with context carryover."""
        if not session.audio_buffer:
            return

        try:
            audio_data = np.concatenate(session.audio_buffer)
            duration = len(audio_data) / self.config.sample_rate

            if duration < 0.3:
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                sf.write(tmp.name, audio_data, self.config.sample_rate)
                tmp_path = tmp.name

            try:
                await websocket.send_json({"type": "processing", "duration": duration})

                # Use streaming transcribe with context carryover
                initial_prompt = None
                if self.config.use_context_carryover and session.last_transcription:
                    initial_prompt = session.last_transcription

                result = await self.asr_service.transcribe_streaming(
                    tmp_path,
                    language=session.config["language"],
                    initial_prompt=initial_prompt,
                    task=session.config.get("task", "transcribe"),
                )

                # Skip empty results (likely no speech detected)
                if not result["text"]:
                    logger.debug("Empty transcription, skipping")
                    return

                # Update context for next chunk
                if self.config.use_context_carryover:
                    session.last_transcription = result.get("last_words", "")

                # Accumulate full session transcript
                if session.accumulated_text:
                    session.accumulated_text += " " + result["text"]
                else:
                    session.accumulated_text = result["text"]

                braille_table = session.config.get("braille_table", self.braille_service.default_table)
                braille_text = self.braille_service.translate(result["text"], braille_table)

                # Accumulate braille
                if session.accumulated_braille:
                    session.accumulated_braille += " " + braille_text
                else:
                    session.accumulated_braille = braille_text

                # Debug logging
                logger.info(f"Transcribed: {result['text'][:50]}")
                if braille_text:
                    logger.info(f"Braille (len={len(braille_text)}): {braille_text[:50]}")

                await websocket.send_json({
                    "type": "result",
                    "transcribed_text": result["text"],
                    "braille": braille_text,
                    "language": result.get("language"),
                    "table_used": braille_table,
                    "audio_duration": result.get("duration"),
                    "success": True,
                })

            finally:
                with contextlib.suppress(OSError):
                    os.unlink(tmp_path)

        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
