"""FastAPI dependency injection functions."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from speech2braille.config import Settings
from speech2braille.services.asr_service import ASRService
from speech2braille.services.braille_service import BrailleService
from speech2braille.services.table_service import TableService


@lru_cache
def get_settings() -> Settings:
    """Get application settings (cached singleton)."""
    return Settings()


def get_asr_service(settings: Annotated[Settings, Depends(get_settings)]) -> ASRService:
    """Get the ASR service instance.

    Note: The actual singleton is managed by the application lifespan.
    This dependency retrieves it from app.state.
    """
    # This will be overridden in main.py to use app.state
    # For now, create a new instance (will be replaced at runtime)
    return ASRService(settings.asr, settings.vad)


def get_braille_service(settings: Annotated[Settings, Depends(get_settings)]) -> BrailleService:
    """Get the braille service instance."""
    return BrailleService(settings.braille)


def get_table_service(settings: Annotated[Settings, Depends(get_settings)]) -> TableService:
    """Get the table service instance."""
    return TableService(settings.braille)


# Type aliases for use in route dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]
ASRServiceDep = Annotated[ASRService, Depends(get_asr_service)]
BrailleServiceDep = Annotated[BrailleService, Depends(get_braille_service)]
TableServiceDep = Annotated[TableService, Depends(get_table_service)]
