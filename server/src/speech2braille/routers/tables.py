"""Braille tables router."""

from fastapi import APIRouter, Request

from speech2braille.models.braille import BrailleTable
from speech2braille.services.table_service import TableService

router = APIRouter(prefix="/api", tags=["tables"])


@router.get("/tables", response_model=list[BrailleTable])
async def list_tables(request: Request) -> list[BrailleTable]:
    """List all available braille translation tables.

    Scans liblouis table directories and returns metadata for each table.
    """
    table_service: TableService = request.app.state.table_service
    return table_service.list_tables()
