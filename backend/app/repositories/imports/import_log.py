"""
Import log repository.
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.import_log import ImportLog


class ImportLogRepository:
    """Repository for import log records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> ImportLog:
        record = ImportLog(**kwargs)
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def get_by_id(self, id: UUID) -> ImportLog | None:
        stmt = select(ImportLog).where(ImportLog.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> Sequence[ImportLog]:
        stmt = select(ImportLog)
        if not include_deleted:
            stmt = stmt.where(
                ImportLog.status != "DELETED",
                ImportLog.file_path.isnot(None),
            )
        stmt = stmt.order_by(ImportLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, id: UUID, **kwargs) -> ImportLog | None:
        stmt = (
            update(ImportLog)
            .where(ImportLog.id == id)
            .values(**kwargs)
            .returning(ImportLog)
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            await self.db.refresh(record)
        return record
