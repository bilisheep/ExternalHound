"""
Relationship business logic service.

Provides high-level business logic for relationship management,
coordinating between PostgreSQL and Neo4j operations.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.db.neo4j import Neo4jManager
from app.models.postgres.relationship import Relationship
from app.repositories.relationships.relationship import RelationshipRepository
from app.schemas.common import Page
from app.schemas.relationships.relationship import (
    NodeType,
    RelationshipType,
    RelationshipCreate,
    RelationshipUpdate,
    RelationshipPathQuery,
    RelationshipPathRead,
)
from app.services.relationships.neo4j_sync import RelationshipGraphService

logger = logging.getLogger(__name__)


class RelationshipService:
    """
    Relationship business logic service.

    Handles relationship creation, updates, deletion, and path queries,
    ensuring consistency between PostgreSQL and Neo4j.
    """

    def __init__(self, db: AsyncSession, neo4j: Neo4jManager) -> None:
        """
        Initialize the relationship service.

        Args:
            db: Database session
            neo4j: Neo4j manager instance
        """
        self.db = db
        self.repo = RelationshipRepository(db)
        self.graph = RelationshipGraphService(neo4j)

    async def create_relationship(self, data: RelationshipCreate) -> Relationship:
        """
        创建新关系。

        Args:
            data: 关系创建数据

        Returns:
            创建的关系实例

        Raises:
            ConflictError: 存在相同key的关系时抛出
        """
        # 检查是否存在关系
        existing = await self.repo.get_by_key(
            source_external_id=data.source_external_id,
            source_type=data.source_type.value,
            target_external_id=data.target_external_id,
            target_type=data.target_type.value,
            relation_type=data.relation_type.value,
            edge_key=data.edge_key,
        )

        # 如果存在关系，抛出冲突错误
        if existing:
            raise ConflictError(
                resource_type="Relationship",
                field="unique_key",
                value=(
                    f"{data.source_external_id}"
                    f"->{data.target_external_id}:{data.relation_type.value}"
                ),
            )

        # 创建新关系
        relationship = await self.repo.create(
            source_external_id=data.source_external_id,
            source_type=data.source_type.value,
            target_external_id=data.target_external_id,
            target_type=data.target_type.value,
            relation_type=data.relation_type.value,
            edge_key=data.edge_key,
            properties=data.properties,
            created_by=data.created_by,
        )

        # 同步到Neo4j（如果失败，PostgreSQL事务会在上层回滚）
        try:
            await self.graph.upsert_relationship(relationship)
        except Exception as exc:
            logger.error(
                "Failed to sync relationship %s to Neo4j: %s",
                relationship.id,
                exc,
            )
            # 重新抛出异常，让上层处理回滚
            raise

        logger.info(
            "Created relationship %s: %s -> %s",
            relationship.id,
            data.source_external_id,
            data.target_external_id,
        )

        return relationship

    async def get_relationship(self, id: UUID) -> Relationship:
        """
        根据ID获取关系。

        Args:
            id: 关系UUID

        Returns:
            关系实例

        Raises:
            NotFoundError: 关系不存在时抛出
        """
        relationship = await self.repo.get_by_id(id)
        if not relationship:
            raise NotFoundError(
                resource_type="Relationship",
                resource_id=str(id),
            )
        return relationship

    async def paginate_relationships(
        self,
        page: int = 1,
        page_size: int = 20,
        source_external_id: str | None = None,
        source_type: NodeType | None = None,
        target_external_id: str | None = None,
        target_type: NodeType | None = None,
        relation_type: RelationshipType | None = None,
        edge_key: str | None = None,
        include_deleted: bool = False,
    ) -> Page[Relationship]:
        """
        分页查询关系列表，支持可选过滤条件。

        Args:
            page: 页码
            page_size: 每页记录数
            source_external_id: 按源节点ID过滤
            source_type: 按源节点类型过滤
            target_external_id: 按目标节点ID过滤
            target_type: 按目标节点类型过滤
            relation_type: 按关系类型过滤
            edge_key: 按边键过滤
            include_deleted: 是否包含已删除的关系（当前使用硬删除，通常为空）

        Returns:
            关系分页结果
        """
        return await self.repo.paginate(
            page=page,
            page_size=page_size,
            include_deleted=include_deleted,
            source_external_id=source_external_id,
            source_type=source_type.value if source_type else None,
            target_external_id=target_external_id,
            target_type=target_type.value if target_type else None,
            relation_type=relation_type.value if relation_type else None,
            edge_key=edge_key,
        )

    async def update_relationship(
        self,
        id: UUID,
        data: RelationshipUpdate,
    ) -> Relationship:
        """
        更新关系属性。

        Args:
            id: 关系UUID
            data: 更新数据

        Returns:
            更新后的关系实例

        Raises:
            NotFoundError: 关系不存在时抛出
        """
        relationship = await self.get_relationship(id)

        if data.properties is None:
            return relationship

        # 合并属性（新属性覆盖已有属性）
        merged_properties = self._merge_properties(
            relationship.properties,
            data.properties,
        )

        # 更新PostgreSQL
        updated = await self.repo.update_properties(id, merged_properties)

        # 同步到Neo4j（如果失败，PostgreSQL事务会在上层回滚）
        try:
            await self.graph.upsert_relationship(updated)
        except Exception as exc:
            logger.error(
                "Failed to sync updated relationship %s to Neo4j: %s",
                id,
                exc,
            )
            # 重新抛出异常，让上层处理回滚
            raise

        logger.info("Updated relationship %s", id)

        return updated

    async def delete_relationship(self, id: UUID) -> bool:
        """
        删除关系（PostgreSQL硬删除，Neo4j硬删除）。

        Args:
            id: 关系UUID

        Returns:
            删除成功返回True

        Raises:
            NotFoundError: 关系不存在时抛出
        """
        # PostgreSQL硬删除
        await self.repo.hard_delete(id)

        # Neo4j硬删除（如果失败，PostgreSQL事务会在上层回滚）
        try:
            await self.graph.delete_relationship(str(id))
        except Exception as exc:
            logger.error(
                "Failed to delete relationship %s from Neo4j: %s",
                id,
                exc,
            )
            # 重新抛出异常，让上层处理回滚
            raise

        logger.info("Deleted relationship %s", id)

        return True

    async def delete_relationships_for_node(
        self,
        external_id: str,
        node_type: NodeType,
    ) -> int:
        """
        删除节点关联的所有关系（PostgreSQL硬删除，Neo4j硬删除）。

        Args:
            external_id: 节点业务ID
            node_type: 节点类型

        Returns:
            删除的关系数量
        """
        deleted_count = await self.repo.hard_delete_by_node(
            external_id=external_id,
            node_type=node_type.value,
        )

        try:
            await self.graph.delete_node_relationships(
                node_type.value,
                external_id,
            )
        except Exception as exc:
            logger.error(
                "Failed to delete relationships for node %s:%s from Neo4j: %s",
                node_type.value,
                external_id,
                exc,
            )
            raise

        if deleted_count:
            logger.info(
                "Deleted %d relationships for node %s:%s",
                deleted_count,
                node_type.value,
                external_id,
            )

        return deleted_count

    async def find_paths(
        self,
        query: RelationshipPathQuery,
    ) -> list[RelationshipPathRead]:
        """
        在图中查找节点间的路径。

        Args:
            query: 路径查询参数

        Returns:
            找到的路径列表
        """
        logger.debug(
            "Finding paths from %s to %s",
            query.source_external_id,
            query.target_external_id,
        )

        paths = await self.graph.find_paths(query)

        logger.debug("Found %d paths", len(paths))

        return paths

    @staticmethod
    def _merge_properties(
        base: dict[str, Any],
        updates: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        合并属性字典。

        Args:
            base: 基础属性字典
            updates: 需要应用的更新

        Returns:
            合并后的属性字典
        """
        if updates is None:
            return base
        return {**base, **updates}
