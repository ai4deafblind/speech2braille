"""API routers."""

from speech2braille.routers.braille_to_speech import router as braille_to_speech_router
from speech2braille.routers.health import router as health_router
from speech2braille.routers.speech import router as speech_router
from speech2braille.routers.tables import router as tables_router
from speech2braille.routers.translation import router as translation_router

__all__ = [
    "braille_to_speech_router",
    "health_router",
    "speech_router",
    "tables_router",
    "translation_router",
]
