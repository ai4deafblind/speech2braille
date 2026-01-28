"""Voice Activity Detection service using Silero VAD."""

import logging
from dataclasses import dataclass

import numpy as np
import torch
from silero_vad import load_silero_vad, VADIterator

from speech2braille.config import VADConfig

logger = logging.getLogger(__name__)


@dataclass
class VADResult:
    """Result from VAD frame processing."""

    is_speech: bool
    probability: float
    speech_start: bool = False
    speech_end: bool = False
    silence_duration_ms: float = 0.0


@dataclass
class VADSessionState:
    """Per-session VAD state."""

    is_speech_active: bool = False
    speech_start_time: float = 0.0
    silence_start_time: float = 0.0
    speech_duration: float = 0.0
    silence_duration: float = 0.0


class VADService:
    """Voice Activity Detection service."""

    def __init__(self, config: VADConfig):
        self.config = config
        self.model = None
        self.iterator = None
        self.is_loaded = False
        self.error = None

    async def load_model(self) -> None:
        """Load Silero VAD model with fallback to WebRTC."""
        if not self.config.enabled:
            logger.info("VAD disabled, using fixed-interval processing")
            return

        try:
            self.model = load_silero_vad()
            self.iterator = VADIterator(
                self.model,
                threshold=self.config.threshold,
                sampling_rate=self.config.sample_rate,
                min_silence_duration_ms=self.config.min_silence_duration_ms,
                speech_pad_ms=self.config.speech_pad_ms,
            )
            self.is_loaded = True
            logger.info("Silero VAD loaded successfully")
        except Exception as e:
            logger.error(f"VAD loading failed: {e}")
            self.error = str(e)
            self.is_loaded = False

    def process_frame(self, audio_chunk: np.ndarray) -> VADResult:
        """Process audio frame and return VAD result."""
        if not self.is_loaded:
            # Fallback: assume speech to avoid missing input
            return VADResult(is_speech=True, probability=0.5)

        try:
            # Convert numpy to torch tensor
            audio_tensor = torch.from_numpy(audio_chunk).float()

            # Ensure exactly frame_size_samples (Silero VAD requires 512 for 16kHz)
            if len(audio_tensor) < self.config.frame_size_samples:
                # Pad if too short
                audio_tensor = torch.nn.functional.pad(
                    audio_tensor, (0, self.config.frame_size_samples - len(audio_tensor))
                )
            elif len(audio_tensor) > self.config.frame_size_samples:
                # Take only the last frame_size_samples if too long
                audio_tensor = audio_tensor[-self.config.frame_size_samples :]

            # Get speech event
            speech_dict = self.iterator(audio_tensor, return_seconds=False)

            is_speech = speech_dict is None  # None = speech continues
            probability = self._get_probability(audio_tensor)

            result = VADResult(is_speech=is_speech, probability=probability)

            # Detect speech start/end
            if speech_dict is not None:
                if "start" in speech_dict:
                    result.speech_start = True
                elif "end" in speech_dict:
                    result.speech_end = True

            return result

        except Exception as e:
            logger.error(f"VAD processing error: {e}")
            return VADResult(is_speech=True, probability=0.5)

    def reset_session(self) -> None:
        """Reset VAD state for new session."""
        if self.iterator:
            self.iterator.reset_states()

    def _get_probability(self, audio_tensor: torch.Tensor) -> float:
        """Get raw speech probability from model."""
        if self.model:
            return float(self.model(audio_tensor, self.config.sample_rate).item())
        return 0.5
