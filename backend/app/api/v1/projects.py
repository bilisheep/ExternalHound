"""
Project configuration API endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_config_db
from app.schemas.common import SuccessResponse
from app.schemas.projects.config import ProjectConfigRead, ProjectConfigUpdate
from app.services.projects.config import ProjectConfigService
from app.utils.projects import DEFAULT_PROJECT_ID, resolve_project_id

router = APIRouter(prefix="/projects", tags=["Projects"])


def _to_read_model(project_id: str, config) -> ProjectConfigRead:
    if config is None:
        return ProjectConfigRead(project_id=project_id, postgres=None, neo4j=None)

    postgres = None
    if any(
        [
            config.postgres_host,
            config.postgres_user,
            config.postgres_db,
        ]
    ):
        postgres = {
            "host": config.postgres_host,
            "port": config.postgres_port or 5432,
            "user": config.postgres_user,
            "database": config.postgres_db,
            "sslmode": config.postgres_sslmode,
            "schema": config.postgres_schema,
            "has_password": bool(config.postgres_password),
        }

    neo4j = None
    if any([config.neo4j_uri, config.neo4j_user]):
        neo4j = {
            "uri": config.neo4j_uri,
            "user": config.neo4j_user,
            "has_password": bool(config.neo4j_password),
        }

    return ProjectConfigRead(project_id=project_id, postgres=postgres, neo4j=neo4j)


@router.get("/{project_id}/config", response_model=ProjectConfigRead)
async def get_project_config(
    project_id: str,
    db: AsyncSession = Depends(get_config_db),
):
    try:
        project_id = resolve_project_id(project_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    service = ProjectConfigService(db)
    config = await service.get_config(project_id)
    return _to_read_model(project_id, config)


@router.put("/{project_id}/config", response_model=ProjectConfigRead)
async def upsert_project_config(
    project_id: str,
    payload: ProjectConfigUpdate,
    db: AsyncSession = Depends(get_config_db),
):
    try:
        project_id = resolve_project_id(project_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    service = ProjectConfigService(db)
    config = await service.upsert_config(project_id, payload)
    return _to_read_model(project_id, config)


@router.delete("/{project_id}/config", response_model=SuccessResponse)
async def delete_project_config(
    project_id: str,
    db: AsyncSession = Depends(get_config_db),
):
    try:
        project_id = resolve_project_id(project_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if project_id == DEFAULT_PROJECT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default project cannot be deleted",
        )

    service = ProjectConfigService(db)
    await service.delete_config(project_id)
    return SuccessResponse(message="Project deleted successfully")
