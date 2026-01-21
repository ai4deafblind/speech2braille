"""FastAPI application factory and entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from speech2braille.config import Settings
from speech2braille.routers import health_router, speech_router, tables_router, translation_router
from speech2braille.services.asr_service import ASRService
from speech2braille.services.braille_service import BrailleService
from speech2braille.services.table_service import TableService
from speech2braille.websockets import SpeechToBrailleWebSocket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Application settings. If None, loads from environment.

    Returns:
        Configured FastAPI application.
    """
    if settings is None:
        settings = Settings()

    # Create services
    asr_service = ASRService(settings.asr)
    braille_service = BrailleService(settings.braille)
    table_service = TableService(settings.braille)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager."""
        logger.info("Starting Brailler API...")

        # Store services in app state for access in routes
        app.state.asr_service = asr_service
        app.state.braille_service = braille_service
        app.state.table_service = table_service
        app.state.settings = settings

        # Start ASR model loading in background
        asyncio.create_task(asr_service.load_model())

        yield

        # Shutdown: Clean up
        logger.info("Shutting down Brailler API...")
        asr_service.unload()

    app = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version=settings.app_version,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(tables_router)
    app.include_router(translation_router)
    app.include_router(speech_router)

    # WebSocket endpoint
    ws_handler = SpeechToBrailleWebSocket(asr_service, braille_service, settings.websocket)

    @app.websocket("/ws/speech-to-braille")
    async def websocket_speech_to_braille(websocket: WebSocket):
        """WebSocket for real-time speech-to-braille with whisper.cpp."""
        await ws_handler.handle(websocket)

    return app


# Create default app instance for uvicorn
app = create_app()
