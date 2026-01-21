"""Configuration management using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ASRConfig(BaseSettings):
    """ASR (Automatic Speech Recognition) configuration for whisper.cpp."""

    model_config = SettingsConfigDict(env_prefix="S2B_ASR_")

    model_name: str = Field(default="base", description="Whisper model name (tiny, base, small, medium, large-v3)")
    model_path: str | None = Field(default=None, description="Optional path to local GGML model file")
    n_threads: int = Field(default=4, description="Number of threads for inference")
    default_language: str = Field(default="en", description="Default language for transcription (required)")

    # Non-speech suppression
    # Note: suppress_non_speech_tokens is not exposed in pywhispercpp C bindings (v1.4.1)
    suppress_blank: bool = Field(default=True, description="Suppress blank outputs")

    # Quality thresholds
    entropy_thold: float = Field(default=2.4, description="Entropy threshold for quality filtering")
    logprob_thold: float = Field(default=-1.0, description="Log probability threshold")
    no_speech_thold: float = Field(default=0.6, description="No-speech probability threshold")

    # Streaming optimization
    temperature: float = Field(default=0.0, description="Sampling temperature (0 = greedy)")
    split_on_word: bool = Field(default=True, description="Split on word boundaries rather than tokens")


class WebSocketConfig(BaseSettings):
    """WebSocket streaming configuration."""

    model_config = SettingsConfigDict(env_prefix="S2B_WS_")

    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    chunk_duration: float = Field(default=3.0, description="Process audio every N seconds")
    buffer_limit: float = Field(default=30.0, description="Maximum buffer duration before force processing")
    min_duration: float = Field(default=0.5, description="Minimum audio duration to process")

    # Context carryover for streaming
    context_window_seconds: float = Field(default=1.0, description="Seconds of audio to overlap for context")
    use_context_carryover: bool = Field(default=True, description="Use previous transcription as prompt for context")


class BrailleConfig(BaseSettings):
    """Braille translation configuration."""

    model_config = SettingsConfigDict(env_prefix="S2B_BRAILLE_")

    default_table: str = Field(default="en-ueb-g2.ctb", description="Default braille table")
    table_directories: list[str] = Field(
        default=[
            "/usr/share/liblouis/tables",
            "/usr/local/share/liblouis/tables",
            "/opt/homebrew/share/liblouis/tables",
        ],
        description="Directories to search for braille tables",
    )


class CORSConfig(BaseSettings):
    """CORS configuration."""

    model_config = SettingsConfigDict(env_prefix="S2B_CORS_")

    allow_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    allow_credentials: bool = Field(default=True, description="Allow credentials")
    allow_methods: list[str] = Field(default=["*"], description="Allowed HTTP methods")
    allow_headers: list[str] = Field(default=["*"], description="Allowed HTTP headers")


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="S2B_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Nested configuration objects
    asr: ASRConfig = Field(default_factory=ASRConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)
    braille: BrailleConfig = Field(default_factory=BrailleConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)

    # Application metadata
    app_title: str = Field(default="Brailler API", description="Application title")
    app_description: str = Field(
        default="Offline-first speech-to-braille translation service with whisper.cpp",
        description="Application description",
    )
    app_version: str = Field(default="0.0.1", description="Application version")
