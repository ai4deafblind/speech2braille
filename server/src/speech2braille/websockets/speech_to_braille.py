"""WebSocket handler for real-time speech-to-braille streaming."""

import contextlib
import json
import logging
import os
import tempfile

import numpy as np
import soundfile as sf
from fastapi import WebSocket, WebSocketDisconnect

from speech2braille.config import WebSocketConfig
from speech2braille.services.asr_service import ASRService
from speech2braille.services.braille_service import BrailleService

logger = logging.getLogger(__name__)


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

            # Session state
            audio_buffer: list[np.ndarray] = []
            session_config = {
                "language": "en",  # Language is required for whisper.cpp
                "task": "transcribe",
                "braille_table": self.braille_service.default_table,
                "word_timestamps": True,
            }
            is_recording = False
            buffer_duration = 0.0

            while True:
                data = await websocket.receive()

                # Config/command messages
                if "text" in data:
                    await self._handle_text_message(
                        websocket,
                        data["text"],
                        session_config,
                        audio_buffer,
                        buffer_duration,
                        is_recording,
                    )

                    # Update local state based on message type
                    try:
                        message = json.loads(data["text"])
                        if message.get("type") == "start_recording":
                            audio_buffer = []
                            buffer_duration = 0.0
                            is_recording = True
                        elif message.get("type") == "stop_recording":
                            audio_buffer = []
                            buffer_duration = 0.0
                            is_recording = False
                    except json.JSONDecodeError:
                        pass

                # Audio chunks
                elif "bytes" in data:
                    result = await self._handle_audio_chunk(
                        websocket,
                        data["bytes"],
                        session_config,
                        audio_buffer,
                        buffer_duration,
                        is_recording,
                    )
                    audio_buffer = result["audio_buffer"]
                    buffer_duration = result["buffer_duration"]
                    is_recording = result["is_recording"]

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def _handle_text_message(
        self,
        websocket: WebSocket,
        text: str,
        session_config: dict,
        audio_buffer: list,
        buffer_duration: float,
        is_recording: bool,
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
                session_config.update(new_config)
                await websocket.send_json({"type": "config_updated", "config": session_config})

            elif message.get("type") == "start_recording":
                await websocket.send_json({"type": "recording_started"})

            elif message.get("type") == "stop_recording":
                if audio_buffer and buffer_duration >= self.config.min_duration:
                    await self._process_audio(websocket, audio_buffer, session_config)
                await websocket.send_json({"type": "recording_stopped"})

        except json.JSONDecodeError as e:
            await websocket.send_json({"type": "error", "message": f"Invalid JSON: {str(e)}"})
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def _handle_audio_chunk(
        self,
        websocket: WebSocket,
        audio_bytes: bytes,
        session_config: dict,
        audio_buffer: list,
        buffer_duration: float,
        is_recording: bool,
    ) -> dict:
        """Handle an audio chunk and return updated state."""
        try:
            audio_chunk = np.frombuffer(audio_bytes, dtype=np.float32)
            if len(audio_chunk) == 0:
                return {
                    "audio_buffer": audio_buffer,
                    "buffer_duration": buffer_duration,
                    "is_recording": is_recording,
                }

            audio_buffer.append(audio_chunk)
            buffer_duration = sum(len(c) for c in audio_buffer) / self.config.sample_rate

            if not is_recording:
                is_recording = True
                await websocket.send_json({"type": "speech_started"})

            # Process every chunk_duration seconds for real-time output
            if buffer_duration >= self.config.chunk_duration and buffer_duration >= self.config.min_duration:
                await self._process_audio(websocket, audio_buffer, session_config)
                audio_buffer = []
                buffer_duration = 0.0

            # Force process if buffer limit reached (safety fallback)
            elif buffer_duration >= self.config.buffer_limit:
                await self._process_audio(websocket, audio_buffer, session_config)
                audio_buffer = []
                buffer_duration = 0.0

        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

        return {
            "audio_buffer": audio_buffer,
            "buffer_duration": buffer_duration,
            "is_recording": is_recording,
        }

    async def _process_audio(
        self,
        websocket: WebSocket,
        audio_buffer: list,
        session_config: dict,
    ) -> None:
        """Process buffered audio and send results."""
        if not audio_buffer:
            return

        try:
            audio_data = np.concatenate(audio_buffer)
            duration = len(audio_data) / self.config.sample_rate

            if duration < 0.3:
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                sf.write(tmp.name, audio_data, self.config.sample_rate)
                tmp_path = tmp.name

            try:
                await websocket.send_json({"type": "processing", "duration": duration})

                result = await self.asr_service.transcribe(
                    tmp_path,
                    language=session_config["language"],  # Required for whisper.cpp
                    task=session_config.get("task", "transcribe"),
                    word_timestamps=session_config.get("word_timestamps", True),
                )

                braille_table = session_config.get("braille_table", self.braille_service.default_table)
                braille_text = self.braille_service.translate(result["text"], braille_table)

                # Debug logging
                logger.info(f"Transcribed: {result['text'][:50]}")
                logger.info(f"Braille (len={len(braille_text)}): {braille_text[:50]}")
                if braille_text:
                    logger.info(f"First char code: U+{ord(braille_text[0]):04X}")

                await websocket.send_json({
                    "type": "result",
                    "transcribed_text": result["text"],
                    "braille": braille_text,
                    "language": result.get("language"),
                    "table_used": braille_table,
                    "audio_duration": result.get("duration"),
                    "segments": result.get("segments"),
                    "success": True,
                })

            finally:
                with contextlib.suppress(OSError):
                    os.unlink(tmp_path)

        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
