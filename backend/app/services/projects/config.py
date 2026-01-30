"""
Project configuration service.
"""

from __future__ import annotations

import logging

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ValidationError
from app.db.postgres import db_manager
from app.models.postgres.project_config import ProjectConfig
from app.schemas.projects.config import ProjectConfigUpdate
from app.utils.projects import DEFAULT_PROJECT_ID, DEFAULT_POSTGRES_SCHEMA


logger = logging.getLogger(__name__)


class ProjectConfigService:
    """
    Manage per-project database connection configuration.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_config(self, project_id: str) -> ProjectConfig | None:
        stmt = select(ProjectConfig).where(ProjectConfig.project_id == project_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_config(
        self,
        project_id: str,
        payload: ProjectConfigUpdate,
    ) -> ProjectConfig:
        config = await self.get_config(project_id)
        if config is None:
            config = ProjectConfig(project_id=project_id)
            self.db.add(config)

        if payload.reset_postgres:
            config.postgres_host = None
            config.postgres_port = None
            config.postgres_user = None
            config.postgres_password = None
            config.postgres_db = None
            config.postgres_sslmode = None
            config.postgres_schema = None

        if payload.reset_neo4j:
            config.neo4j_uri = None
            config.neo4j_user = None
            config.neo4j_password = None

        if payload.postgres:
            update = payload.postgres
            if update.host is not None:
                config.postgres_host = update.host.strip() or None
            if update.port is not None:
                config.postgres_port = update.port
            if update.user is not None:
                config.postgres_user = update.user.strip() or None
            if update.password is not None:
                config.postgres_password = update.password.strip() or None
            if update.database is not None:
                config.postgres_db = update.database.strip() or None
            if update.sslmode is not None:
                config.postgres_sslmode = update.sslmode.strip() or None
            if update.db_schema is not None:
                config.postgres_schema = update.db_schema.strip() or None

        if payload.neo4j:
            update = payload.neo4j
            if update.uri is not None:
                config.neo4j_uri = update.uri.strip() or None
            if update.user is not None:
                config.neo4j_user = update.user.strip() or None
            if update.password is not None:
                config.neo4j_password = update.password.strip() or None

        self._validate_postgres_config(project_id, config)
        self._validate_neo4j_config(project_id, config)

        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete_config(self, project_id: str) -> bool:
        config = await self.get_config(project_id)
        if config is None:
            return False
        await self.db.delete(config)
        await self.db.flush()
        return True

    def _validate_postgres_config(self, project_id: str, config: ProjectConfig) -> None:
        values = [
            config.postgres_host,
            config.postgres_user,
            config.postgres_password,
            config.postgres_db,
        ]
        if not any(values):
            return

        if not all(values):
            raise ValidationError(
                message="PostgreSQL configuration is incomplete",
                field="postgres",
            )

        if config.postgres_port is None:
            config.postgres_port = settings.POSTGRES_PORT

    def _validate_neo4j_config(self, project_id: str, config: ProjectConfig) -> None:
        values = [
            config.neo4j_uri,
            config.neo4j_user,
            config.neo4j_password,
        ]
        if not any(values):
            if project_id != DEFAULT_PROJECT_ID:
                return
            return

        if not all(values):
            raise ValidationError(
                message="Neo4j configuration is incomplete",
                field="neo4j",
            )


async def ensure_default_project_config() -> None:
    """
    Ensure the default project has a stored configuration.

    Uses settings values to seed the config table if missing.
    """
    session = db_manager.session_factory()
    await session.execute(text("SET search_path TO public"))
    try:
        result = await session.execute(
            select(ProjectConfig).where(ProjectConfig.project_id == DEFAULT_PROJECT_ID)
        )
        config = result.scalar_one_or_none()
        if config is not None:
            return
        config = ProjectConfig(
            project_id=DEFAULT_PROJECT_ID,
            postgres_host=settings.POSTGRES_HOST,
            postgres_port=settings.POSTGRES_PORT,
            postgres_user=settings.POSTGRES_USER,
            postgres_password=settings.POSTGRES_PASSWORD,
            postgres_db=settings.POSTGRES_DB,
            postgres_sslmode=settings.POSTGRES_SSLMODE,
            postgres_schema=DEFAULT_POSTGRES_SCHEMA,
            neo4j_uri=settings.NEO4J_URI,
            neo4j_user=settings.NEO4J_USER,
            neo4j_password=settings.NEO4J_PASSWORD,
        )
        session.add(config)
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        logger.warning("Failed to ensure default project config: %s", exc)
    finally:
        await session.close()
