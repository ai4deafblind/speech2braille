"""API routers."""

from speech2braille.routers.health import router as health_router
from speech2braille.routers.speech import router as speech_router
from speech2braille.routers.tables import router as tables_router
from speech2braille.routers.translation import router as translation_router

__all__ = [
    "health_router",
    "speech_router",
    "tables_router",
    "translation_router",
]
