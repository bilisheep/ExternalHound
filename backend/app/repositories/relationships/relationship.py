"""
Relationship Repository.

Provides data access layer for relationship CRUD operations with support
for pagination and complex filtering.
"""

from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select, delete, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import paginate
from app.models.postgres.relationship import Relationship
from app.schemas.common import Page


class RelationshipRepository:
    """
    Relationship Repository.

    Encapsulates all database operations for relationships, providing a clean
    interface for the service layer.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def create(self, **kwargs: Any) -> Relationship:
        """
        创建新关系。

        Args:
            **kwargs: 关系字段

        Returns:
            创建的关系实例

        Raises:
            ConflictError: 违反唯一约束时抛出
        """
        try:
            relationship = Relationship(**kwargs)
            self.db.add(relationship)
            await self.db.flush()
            await self.db.refresh(relationship)
            return relationship
        except IntegrityError as exc:
            # 由上层事务管理器处理回滚，不在Repository层rollback
            raise ConflictError(
                resource_type="Relationship",
                field="unique_key",
                value="relationship",
                details={"original_error": str(exc.orig)},
            ) from exc

    async def get_by_id(
        self,
        id: UUID,
        include_deleted: bool = False,
    ) -> Relationship | None:
        """
        根据UUID获取关系。

        Args:
            id: 关系UUID
            include_deleted: 是否包含软删除的记录

        Returns:
            关系实例，如果不存在则返回None
        """
        stmt = select(Relationship).where(Relationship.id == id)
        if not include_deleted:
            stmt = stmt.where(Relationship.is_deleted == False)  # noqa: E712

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_key(
        self,
        source_external_id: str,
        source_type: str,
        target_external_id: str,
        target_type: str,
        relation_type: str,
        edge_key: str,
        include_deleted: bool = False,
    ) -> Relationship | None:
        """
        根据唯一键获取关系。

        Args:
            source_external_id: 源节点业务ID
            source_type: 源节点类型
            target_external_id: 目标节点业务ID
            target_type: 目标节点类型
            relation_type: 关系类型
            edge_key: 边唯一键
            include_deleted: 是否包含软删除的记录

        Returns:
            关系实例，如果不存在则返回None
        """
        stmt = select(Relationship).where(
            Relationship.source_external_id == source_external_id,
            Relationship.source_type == source_type,
            Relationship.target_external_id == target_external_id,
            Relationship.target_type == target_type,
            Relationship.relation_type == relation_type,
            Relationship.edge_key == edge_key,
        )
        if not include_deleted:
            stmt = stmt.where(Relationship.is_deleted == False)  # noqa: E712

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        **filters: Any,
    ) -> Sequence[Relationship]:
        """
        列出关系列表，支持可选过滤条件。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            include_deleted: 是否包含软删除的记录
            **filters: 额外的过滤条件

        Returns:
            关系实例序列
        """
        stmt = select(Relationship)
        if not include_deleted:
            stmt = stmt.where(Relationship.is_deleted == False)  # noqa: E712

        stmt = self._apply_filters(stmt, **filters)
        # 添加稳定排序：先按创建时间，再按ID（避免分页时记录重复或遗漏）
        stmt = stmt.order_by(Relationship.created_at.asc(), Relationship.id.asc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
        **filters: Any,
    ) -> Page[Relationship]:
        """
        分页查询关系列表，支持可选过滤条件。

        Args:
            page: 页码（从1开始）
            page_size: 每页记录数
            include_deleted: 是否包含软删除的记录
            **filters: 额外的过滤条件

        Returns:
            包含关系列表和分页元数据的Page对象
        """
        stmt = select(Relationship)
        if not include_deleted:
            stmt = stmt.where(Relationship.is_deleted == False)  # noqa: E712

        stmt = self._apply_filters(stmt, **filters)
        # 添加稳定排序：先按创建时间，再按ID（避免分页时记录重复或遗漏）
        stmt = stmt.order_by(Relationship.created_at.asc(), Relationship.id.asc())
        return await paginate(self.db, stmt, page, page_size)

    async def update_properties(
        self,
        id: UUID,
        properties: dict[str, Any],
    ) -> Relationship:
        """
        更新关系的属性字段。

        Args:
            id: 关系UUID
            properties: 更新后的属性字典

        Returns:
            更新后的关系实例

        Raises:
            NotFoundError: 关系不存在时抛出
        """
        relationship = await self.get_by_id(id)
        if relationship is None:
            raise NotFoundError(
                resource_type="Relationship",
                resource_id=str(id),
            )

        relationship.properties = properties
        await self.db.flush()
        await self.db.refresh(relationship)
        return relationship

    async def soft_delete(self, id: UUID) -> bool:
        """
        删除关系（硬删除）。

        Args:
            id: 关系UUID

        Returns:
            删除成功返回True

        Raises:
            NotFoundError: 关系不存在时抛出
        """
        return await self.hard_delete(id)

    async def hard_delete(self, id: UUID) -> bool:
        """
        硬删除关系。

        Args:
            id: 关系UUID

        Returns:
            删除成功返回True

        Raises:
            NotFoundError: 关系不存在时抛出
        """
        stmt = delete(Relationship).where(Relationship.id == id)
        result = await self.db.execute(stmt)
        if not result.rowcount:
            raise NotFoundError(
                resource_type="Relationship",
                resource_id=str(id),
            )
        return True

    async def hard_delete_by_node(
        self,
        external_id: str,
        node_type: str,
    ) -> int:
        """
        硬删除指定节点的所有关系。

        Args:
            external_id: 节点业务ID
            node_type: 节点类型

        Returns:
            删除的关系数量
        """
        stmt = delete(Relationship).where(
            or_(
                and_(
                    Relationship.source_external_id == external_id,
                    Relationship.source_type == node_type,
                ),
                and_(
                    Relationship.target_external_id == external_id,
                    Relationship.target_type == node_type,
                ),
            ),
        )
        result = await self.db.execute(stmt)
        return result.rowcount or 0

    async def restore(
        self,
        id: UUID,
        **kwargs: Any,
    ) -> Relationship:
        """
        恢复软删除的关系。

        Args:
            id: 关系UUID
            **kwargs: 需要更新的额外字段

        Returns:
            恢复后的关系实例

        Raises:
            NotFoundError: 关系不存在时抛出
        """
        relationship = await self.get_by_id(id, include_deleted=True)
        if relationship is None:
            raise NotFoundError(
                resource_type="Relationship",
                resource_id=str(id),
            )

        for key, value in kwargs.items():
            if value is not None and hasattr(relationship, key):
                setattr(relationship, key, value)

        relationship.is_deleted = False
        relationship.deleted_at = None
        await self.db.flush()
        await self.db.refresh(relationship)
        return relationship

    def _apply_filters(
        self,
        stmt: select,
        **filters: Any,
    ) -> select:
        """
        向查询应用过滤条件。

        Args:
            stmt: SQLAlchemy select语句
            **filters: 过滤条件

        Returns:
            修改后的select语句
        """
        if filters.get("source_external_id"):
            stmt = stmt.where(
                Relationship.source_external_id == filters["source_external_id"]
            )
        if filters.get("source_type"):
            stmt = stmt.where(Relationship.source_type == filters["source_type"])
        if filters.get("target_external_id"):
            stmt = stmt.where(
                Relationship.target_external_id == filters["target_external_id"]
            )
        if filters.get("target_type"):
            stmt = stmt.where(Relationship.target_type == filters["target_type"])
        if filters.get("relation_type"):
            stmt = stmt.where(Relationship.relation_type == filters["relation_type"])
        if filters.get("edge_key"):
            stmt = stmt.where(Relationship.edge_key == filters["edge_key"])

        return stmt
