"""OCR service using RapidOCR PP-OCRv5."""

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from speech2braille.config import OCRConfig

logger = logging.getLogger(__name__)

# Map language codes to RapidOCR LangRec enums (imported lazily)
LANG_MAP_NAMES = {
    "en": "EN",
    "ch": "CH",
    "fr": "LATIN",
    "de": "LATIN",
    "ja": "JAPAN",
    "ko": "KOREAN",
    "es": "LATIN",
    "pt": "LATIN",
    "it": "LATIN",
    "ru": "CYRILLIC",
    "ar": "ARABIC",
    "hi": "DEVANAGARI",
    "id": "LATIN",
    "vi": "LATIN",
}


@dataclass
class OCRState:
    """State of the OCR engines."""

    engines: dict[str, Any] = field(default_factory=dict)
    loaded: bool = False
    loading: bool = False
    error: str | None = None


class OCRService:
    """Service for optical character recognition using RapidOCR PP-OCRv5."""

    def __init__(self, ocr_config: OCRConfig) -> None:
        self.ocr_config = ocr_config
        self.state = OCRState()

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
        """Get current OCR status string."""
        if self.state.loaded:
            return "loaded"
        if self.state.loading:
            return "loading"
        if self.state.error:
            return f"error: {self.state.error}"
        return "not loaded"

    def get_loaded_languages(self) -> list[str]:
        """Return list of currently loaded language engines."""
        return list(self.state.engines.keys())

    def _get_or_create_engine(self, language: str) -> Any:
        """Get an existing engine or create a new one for the given language.

        Engines are cached per language in state.engines.
        """
        if language in self.state.engines:
            return self.state.engines[language]

        from rapidocr import EngineType, LangRec, ModelType, OCRVersion, RapidOCR

        lang_name = LANG_MAP_NAMES.get(language, "LATIN")
        lang_enum = getattr(LangRec, lang_name)

        model_type = ModelType.SERVER if self.ocr_config.model_type == "server" else ModelType.MOBILE

        logger.info(f"Creating RapidOCR engine for language: {language} (lang_type={lang_name}, model={self.ocr_config.model_type})")
        engine = RapidOCR(params={
            "Global.text_score": self.ocr_config.min_confidence,
            "Global.max_side_len": self.ocr_config.max_side_len,
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Det.ocr_version": OCRVersion.PPOCRV5,
            "Det.model_type": model_type,
            "Rec.engine_type": EngineType.ONNXRUNTIME,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.model_type": model_type,
            "Rec.lang_type": lang_enum,
        })
        self.state.engines[language] = engine
        logger.info(f"RapidOCR engine created for language: {language}")
        return engine

    def load_model_sync(self) -> None:
        """Pre-load the default language engine (synchronous, call from thread)."""
        if self.state.loading or self.state.loaded:
            return

        self.state.loading = True
        default_lang = self.ocr_config.default_language
        logger.info(f"Loading RapidOCR PP-OCRv5 (default language: {default_lang})")

        try:
            self._get_or_create_engine(default_lang)
            self.state.loaded = True
            self.state.loading = False
            logger.info(f"RapidOCR PP-OCRv5 loaded successfully (language: {default_lang})")
        except Exception as e:
            logger.error(f"Failed to load RapidOCR: {e!s}")
            self.state.error = str(e)
            self.state.loading = False
            self.state.loaded = False

    def recognize(self, image_path: str, language: str | None = None) -> dict[str, Any]:
        """Run OCR on an image file.

        Args:
            image_path: Path to image file.
            language: Language code. Uses default if not specified.

        Returns:
            Dict with lines, full_text, language, success.
        """
        if not self.state.loaded:
            if self.state.loading:
                raise RuntimeError("OCR model is loading...")
            elif self.state.error:
                raise RuntimeError(f"OCR model failed: {self.state.error}")
            else:
                raise RuntimeError("OCR model not loaded")

        lang = language or self.ocr_config.default_language
        engine = self._get_or_create_engine(lang)

        logger.info(f"Running OCR on: {image_path} (language={lang})")
        result = engine(image_path)

        lines = []
        text_parts = []

        if result.txts is None or len(result.txts) == 0:
            logger.warning(f"OCR returned no text for: {image_path}")
        else:
            for i, text in enumerate(result.txts):
                confidence = float(result.scores[i]) if result.scores and i < len(result.scores) else 0.0
                bbox = []
                if result.boxes is not None and i < len(result.boxes):
                    box = result.boxes[i]
                    if isinstance(box, np.ndarray):
                        bbox = box.tolist()
                    else:
                        bbox = list(box)

                lines.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox,
                })
                text_parts.append(text)

        full_text = "\n".join(text_parts)
        logger.info(f"OCR recognized {len(lines)} lines: {full_text[:100]}...")

        return {
            "lines": lines,
            "full_text": full_text,
            "language": lang,
            "success": True,
        }

    def unload(self) -> None:
        """Unload all OCR engines and free resources."""
        self.state.engines.clear()
        self.state.loaded = False
        logger.info("OCR engines unloaded")
