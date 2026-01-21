"""ASR (Automatic Speech Recognition) service using whisper.cpp via pywhispercpp."""

import logging
import re
from dataclasses import dataclass
from typing import Any

from pywhispercpp.model import Model

from speech2braille.config import ASRConfig

# Pattern to match noise annotations like [INAUDIBLE], (music), (keyboard clicking), etc.
NOISE_PATTERN = re.compile(
    r'\s*[\[\(]'  # Opening bracket with optional leading whitespace
    r'[^\]\)]*'   # Content inside brackets
    r'(?:inaudible|music|noise|silence|applause|laughter|cough|sneeze|'
    r'clicking|typing|background|sound|audio|static|buzzing|humming|'
    r'crosstalk|unintelligible|indistinct|unclear)'
    r'[^\]\)]*'   # More content
    r'[\]\)]'     # Closing bracket
    r'\s*',       # Optional trailing whitespace
    re.IGNORECASE
)

logger = logging.getLogger(__name__)


@dataclass
class ASRState:
    """State of the ASR model."""

    model: Model | None = None
    loaded: bool = False
    loading: bool = False
    error: str | None = None


class ASRService:
    """Service for speech recognition using whisper.cpp."""

    def __init__(self, asr_config: ASRConfig) -> None:
        self.asr_config = asr_config
        self.state = ASRState()

    @property
    def model_name(self) -> str:
        return self.asr_config.model_path or self.asr_config.model_name

    @property
    def is_loaded(self) -> bool:
        return self.state.loaded

    @property
    def is_loading(self) -> bool:
        return self.state.loading

    @property
    def error(self) -> str | None:
        return self.state.error

    @property
    def device(self) -> str | None:
        """Return device info (whisper.cpp uses CPU by default)."""
        if self.state.loaded:
            return "cpu"
        return None

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
            return f"whisper.cpp-{self.asr_config.model_name}"
        return None

    async def load_model(self) -> None:
        """Load the whisper.cpp model."""
        if self.state.loading or self.state.loaded:
            return

        self.state.loading = True
        model_id = self.asr_config.model_path or self.asr_config.model_name
        logger.info(f"Loading whisper.cpp model: {model_id}")

        try:
            model = Model(
                model=model_id,
                n_threads=self.asr_config.n_threads,
                print_progress=False,
                print_realtime=False,
            )

            self.state.model = model
            self.state.loaded = True
            self.state.loading = False

            logger.info(f"whisper.cpp loaded: {model_id} with {self.asr_config.n_threads} threads")

        except Exception as e:
            logger.error(f"Failed to load model: {e!s}")
            self.state.error = str(e)
            self.state.loading = False
            self.state.loaded = False

    async def transcribe(
        self,
        audio_path: str,
        language: str,
        task: str = "transcribe",
        word_timestamps: bool = False,
    ) -> dict[str, Any]:
        """Transcribe audio using whisper.cpp.

        Args:
            audio_path: Path to audio file
            language: Language code (REQUIRED - cannot be None)
            task: 'transcribe' or 'translate'
            word_timestamps: Include word-level timestamps (not supported in whisper.cpp)

        Returns:
            Dict with text, language, duration, segments, success

        Raises:
            ValueError: If language is None or empty
            RuntimeError: If ASR model is not loaded
        """
        if not language:
            raise ValueError("Language is required for transcription")

        if not self.state.loaded:
            if self.state.loading:
                raise RuntimeError("ASR model is loading...")
            elif self.state.error:
                raise RuntimeError(f"ASR model failed: {self.state.error}")
            else:
                raise RuntimeError("ASR model not loaded")

        logger.info(f"Transcribing: {audio_path} (language={language}, task={task})")
        model = self.state.model

        # Transcribe with whisper.cpp
        translate = task == "translate"
        segments = model.transcribe(
            audio_path,
            language=language,
            translate=translate,
            extract_probability=True,
        )

        # Process segments
        full_text = []
        segment_list = []
        max_time = 0.0

        for idx, segment in enumerate(segments):
            # Filter out noise annotations from segment text
            clean_text = NOISE_PATTERN.sub('', segment.text).strip()
            if not clean_text:
                continue  # Skip segments that are only noise
            full_text.append(clean_text)

            # t0 and t1 are in centiseconds (1/100 second)
            start_sec = float(segment.t0) / 100.0
            end_sec = float(segment.t1) / 100.0
            max_time = max(max_time, end_sec)

            # Convert numpy float32 to native Python float for JSON serialization
            probability = getattr(segment, "probability", 0.0)
            if probability is None:
                probability = 0.0

            segment_data = {
                "id": idx,
                "start": start_sec,
                "end": end_sec,
                "text": clean_text,
                "avg_logprob": float(probability),
                "no_speech_prob": 0.0,  # Not available in whisper.cpp
            }

            # Note: whisper.cpp doesn't provide word-level timestamps
            # in the same way as faster-whisper

            segment_list.append(segment_data)

        transcription = " ".join(full_text).strip()
        logger.info(f"Transcribed: {transcription[:100]}...")

        return {
            "text": transcription,
            "language": language,
            "duration": float(max_time),
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
