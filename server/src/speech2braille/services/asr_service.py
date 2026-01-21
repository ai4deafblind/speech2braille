"""ASR (Automatic Speech Recognition) service using faster-whisper."""

import logging
from dataclasses import dataclass, field
from typing import Any

from faster_whisper import WhisperModel

from speech2braille.config import ASRConfig, VADConfig

logger = logging.getLogger(__name__)


@dataclass
class ASRState:
    """State of the ASR model."""

    model: WhisperModel | None = None
    device: str | None = None
    compute_type: str | None = None
    loaded: bool = False
    loading: bool = False
    error: str | None = None


class ASRService:
    """Service for speech recognition using faster-whisper."""

    def __init__(self, asr_config: ASRConfig, vad_config: VADConfig) -> None:
        self.asr_config = asr_config
        self.vad_config = vad_config
        self.state = ASRState()

    @property
    def model_size(self) -> str:
        return self.asr_config.model_size

    @property
    def is_loaded(self) -> bool:
        return self.state.loaded

    @property
    def is_loading(self) -> bool:
        return self.state.loading

    @property
    def device(self) -> str | None:
        return self.state.device

    @property
    def error(self) -> str | None:
        return self.state.error

    def get_status(self) -> str:
        """Get current ASR status string."""
        if self.state.loaded:
            return "loaded"
        if self.state.loading:
            return "loading"
        return "not loaded"

    def get_model_name(self) -> str | None:
        """Get the model name if loaded."""
        if self.state.loaded:
            return f"faster-whisper-{self.asr_config.model_size}"
        return None

    async def load_model(self) -> None:
        """Load the faster-whisper model."""
        if self.state.loading or self.state.loaded:
            return

        self.state.loading = True
        model_size = self.asr_config.model_size
        logger.info(f"Loading faster-whisper model: {model_size}")

        try:
            # Determine device and compute type
            device = self.asr_config.device
            compute_type = self.asr_config.compute_type

            if device is None:
                # Auto-detect
                try:
                    import torch

                    has_cuda = torch.cuda.is_available()
                except ImportError:
                    has_cuda = False

                if has_cuda:
                    device = "cuda"
                    compute_type = compute_type or "int8_float16"
                    logger.info(f"Using CUDA with {compute_type}")
                else:
                    device = "cpu"
                    compute_type = compute_type or "int8"
                    logger.info(f"Using CPU with {compute_type} quantization")

            self.state.device = device
            self.state.compute_type = compute_type

            # Initialize model
            logger.info(f"Loading model size '{model_size}'...")
            model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=self.asr_config.download_root,
                local_files_only=self.asr_config.local_files_only,
            )

            self.state.model = model
            self.state.loaded = True
            self.state.loading = False

            logger.info(f"faster-whisper loaded: {model_size} on {device}")

        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self.state.error = str(e)
            self.state.loading = False
            self.state.loaded = False

    async def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        task: str = "transcribe",
        word_timestamps: bool = False,
    ) -> dict[str, Any]:
        """Transcribe audio using faster-whisper.

        Args:
            audio_path: Path to audio file
            language: Optional language code
            task: 'transcribe' or 'translate'
            word_timestamps: Include word-level timestamps

        Returns:
            Dict with text, language, duration, segments, success
        """
        if not self.state.loaded:
            if self.state.loading:
                raise RuntimeError("ASR model is loading...")
            elif self.state.error:
                raise RuntimeError(f"ASR model failed: {self.state.error}")
            else:
                raise RuntimeError("ASR model not loaded")

        logger.info(f"Transcribing: {audio_path}")
        model = self.state.model

        # VAD parameters from config
        vad_parameters = {
            "threshold": self.vad_config.threshold,
            "min_speech_duration_ms": self.vad_config.min_speech_duration_ms,
            "min_silence_duration_ms": self.vad_config.min_silence_duration_ms,
            "speech_pad_ms": self.vad_config.speech_pad_ms,
        }

        # Transcribe with faster-whisper
        segments, info = model.transcribe(
            audio_path,
            language=language,
            task=task,
            beam_size=5,
            word_timestamps=word_timestamps,
            vad_filter=True,
            vad_parameters=vad_parameters,
        )

        # Process segments
        full_text = []
        segment_list = []

        for segment in segments:
            full_text.append(segment.text)

            segment_data = {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "avg_logprob": segment.avg_logprob,
                "no_speech_prob": segment.no_speech_prob,
            }

            if word_timestamps and hasattr(segment, "words") and segment.words:
                segment_data["words"] = [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability,
                    }
                    for word in segment.words
                ]

            segment_list.append(segment_data)

        transcription = " ".join(full_text).strip()
        logger.info(f"Transcribed: {transcription[:100]}...")

        return {
            "text": transcription,
            "language": info.language,
            "duration": info.duration,
            "segments": segment_list if word_timestamps else None,
            "success": True,
        }

    def unload(self) -> None:
        """Unload the ASR model and free resources."""
        if self.state.model is not None:
            del self.state.model
            self.state.model = None
            self.state.loaded = False
            logger.info("ASR model unloaded")
