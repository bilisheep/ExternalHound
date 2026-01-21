"""
Import API endpoints.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.schemas.imports.import_log import ImportLogList, ImportLogRead
from app.schemas.imports.plugin import PluginInfo
from app.services.imports.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.get("/plugins", response_model=list[PluginInfo])
async def list_plugins(
    db: AsyncSession = Depends(get_db),
):
    service = ImportService(db)
    plugins = await service.list_plugins()
    return [
        PluginInfo(
            name=plugin.name,
            version=plugin.version,
            entrypoint=plugin.entrypoint,
            supported_formats=plugin.supported_formats,
            priority=plugin.priority,
            description=plugin.description,
            vendor=plugin.vendor,
        )
        for plugin in plugins
    ]


@router.post("", response_model=ImportLogRead)
async def upload_and_import(
    file: UploadFile = File(...),
    parser_name: str | None = Form(None),
    created_by: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    service = ImportService(db)
    try:
        record = await service.import_file(file, parser_name=parser_name, created_by=created_by)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Import failed")
    return record


@router.get("", response_model=ImportLogList)
async def list_imports(
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
):
    service = ImportService(db)
    items = await service.list_imports(
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )
    return ImportLogList(items=items, total=len(items))


@router.get("/{import_id}", response_model=ImportLogRead)
async def get_import(
    import_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = ImportService(db)
    record = await service.get_import(import_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")
    return record


@router.delete("/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_import_file(
    import_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = ImportService(db)
    deleted = await service.delete_import_file(import_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")
