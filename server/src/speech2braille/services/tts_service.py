"""TTS (Text-to-Speech) service using piper."""

import io
import logging
import wave
from dataclasses import dataclass, field
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

from speech2braille.config import TTSConfig

logger = logging.getLogger(__name__)


@dataclass
class TTSState:
    """State of the TTS engine."""

    voices: dict[str, PiperVoice] = field(default_factory=dict)
    loaded: bool = False
    loading: bool = False
    error: str | None = None


class TTSService:
    """Service for text-to-speech synthesis using piper."""

    def __init__(self, tts_config: TTSConfig) -> None:
        self.tts_config = tts_config
        self.state = TTSState()

    @property
    def is_loaded(self) -> bool:
        return self.state.loaded

    @property
    def is_loading(self) -> bool:
        return self.state.loading

    @property
    def error(self) -> str | None:
        return self.state.error

    def get_status(self) -> str:
        """Get current TTS status string."""
        if self.state.loaded:
            return "loaded"
        if self.state.loading:
            return "loading"
        return "not loaded"

    def get_voice_ids(self) -> list[str]:
        """Get list of loaded voice IDs."""
        return list(self.state.voices.keys())

    def get_voice_info(self) -> list[dict[str, str]]:
        """Get info about loaded voices."""
        result = []
        for voice_id in self.state.voices:
            parts = voice_id.split("-")
            # e.g. en_US-amy-medium -> language=en_US, quality=medium
            language = parts[0] if parts else voice_id
            quality = parts[-1] if len(parts) >= 3 else "unknown"
            result.append({"voice_id": voice_id, "language": language, "quality": quality})
        return result

    def _resolve_model_dir(self) -> Path:
        """Resolve voice_model_dir relative to the server/ root."""
        model_dir = Path(self.tts_config.voice_model_dir)
        if model_dir.is_absolute():
            return model_dir
        # Resolve relative to server/ root: services/ -> speech2braille/ -> src/ -> server/
        server_root = Path(__file__).resolve().parents[3]
        return server_root / model_dir

    async def load_model(self) -> None:
        """Load all piper voice models from the voice directory."""
        if self.state.loading or self.state.loaded:
            return

        self.state.loading = True
        model_dir = self._resolve_model_dir()
        logger.info(f"Loading piper voices from: {model_dir}")

        try:
            if not model_dir.exists():
                logger.warning(f"Voice model directory does not exist: {model_dir}")
                logger.warning("Run: bash server/scripts/download-voices.sh")
                self.state.loading = False
                return

            onnx_files = sorted(model_dir.glob("*.onnx"))
            if not onnx_files:
                logger.warning(f"No .onnx voice files found in {model_dir}")
                logger.warning("Run: bash server/scripts/download-voices.sh")
                self.state.loading = False
                return

            for onnx_path in onnx_files:
                voice_id = onnx_path.stem  # e.g. en_US-amy-medium
                try:
                    voice = PiperVoice.load(str(onnx_path))
                    self.state.voices[voice_id] = voice
                    logger.info(f"Loaded voice: {voice_id}")
                except Exception as e:
                    logger.error(f"Failed to load voice {voice_id}: {e!s}")

            if self.state.voices:
                self.state.loaded = True
                logger.info(f"Piper TTS ready with {len(self.state.voices)} voice(s)")
            else:
                logger.warning("No voices loaded successfully")

            self.state.loading = False

        except Exception as e:
            logger.error(f"Failed to load TTS voices: {e!s}")
            self.state.error = str(e)
            self.state.loading = False
            self.state.loaded = False

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        length_scale: float | None = None,
        noise_scale: float | None = None,
        noise_w: float | None = None,
    ) -> bytes:
        """Synthesize text to WAV audio bytes.

        Args:
            text: Text to synthesize.
            voice_id: Voice model ID. Uses default if not specified.
            length_scale: Speech speed override.
            noise_scale: Audio variation override.
            noise_w: Phoneme duration variation override.

        Returns:
            WAV audio bytes.

        Raises:
            RuntimeError: If TTS is not loaded.
            ValueError: If the requested voice is not available.
        """
        if not self.state.loaded:
            if self.state.loading:
                raise RuntimeError("TTS models are loading...")
            elif self.state.error:
                raise RuntimeError(f"TTS failed to load: {self.state.error}")
            else:
                raise RuntimeError("TTS models not loaded")

        voice_id = voice_id or self.tts_config.default_voice_id
        voice = self.state.voices.get(voice_id)
        if voice is None:
            available = ", ".join(self.state.voices.keys())
            raise ValueError(f"Voice '{voice_id}' not found. Available: {available}")

        syn_config = SynthesisConfig(
            length_scale=length_scale if length_scale is not None else self.tts_config.length_scale,
            noise_scale=noise_scale if noise_scale is not None else self.tts_config.noise_scale,
            noise_w_scale=noise_w if noise_w is not None else self.tts_config.noise_w,
            normalize_audio=self.tts_config.normalize_audio,
        )

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=syn_config)

        return buf.getvalue()

    def unload(self) -> None:
        """Unload all TTS voices and free resources."""
        if self.state.voices:
            self.state.voices.clear()
            self.state.loaded = False
            logger.info("TTS voices unloaded")
