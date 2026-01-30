"""
Organization Service

提供组织资产的业务逻辑。
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.pagination import Page
from app.db.neo4j import Neo4jManager
from app.models.postgres.organization import Organization
from app.repositories.assets.organization import OrganizationRepository
from app.schemas.assets.organization import OrganizationCreate, OrganizationUpdate
from app.schemas.relationships.relationship import NodeType
from app.services.relationships.relationship import RelationshipService
from app.utils.external_id import generate_organization_external_id


class OrganizationService:
    """
    组织资产Service

    处理组织相关的业务逻辑。
    """

    def __init__(
        self,
        db: AsyncSession,
        neo4j: Neo4jManager | None = None,
    ) -> None:
        """
        初始化OrganizationService

        Args:
            db: 数据库会话
        """
        self.db = db
        self.repo = OrganizationRepository(db)
        self.relationship_service = (
            RelationshipService(db, neo4j) if neo4j else None
        )

    async def create_organization(
        self,
        data: OrganizationCreate
    ) -> Organization:
        """
        创建组织

        Args:
            data: 组织创建数据

        Returns:
            创建的组织实例

        Raises:
            ConflictError: 当external_id或credit_code已存在时
        """
        external_id = data.external_id.strip() if data.external_id else None
        if not external_id:
            external_id = generate_organization_external_id(data.name, data.credit_code)

        # 检查external_id是否已存在
        existing = await self.repo.get_by_external_id(external_id)
        if existing:
            raise ConflictError(
                resource_type="Organization",
                field="external_id",
                value=external_id
            )

        # 检查credit_code是否已存在（如果提供）
        if data.credit_code:
            existing_credit = await self.repo.get_by_credit_code(data.credit_code)
            if existing_credit:
                raise ConflictError(
                    resource_type="Organization",
                    field="credit_code",
                    value=data.credit_code
                )

        # 创建组织
        create_data = data.model_dump()
        create_data["external_id"] = external_id
        return await self.repo.create(**create_data)

    async def get_organization(self, id: UUID) -> Organization:
        """
        获取组织详情

        Args:
            id: 组织UUID

        Returns:
            组织实例

        Raises:
            NotFoundError: 当组织不存在时
        """
        org = await self.repo.get_by_id(id)
        if not org:
            raise NotFoundError(
                resource_type="Organization",
                resource_id=str(id)
            )
        return org

    async def get_organization_by_external_id(
        self,
        external_id: str
    ) -> Organization:
        """
        根据业务ID获取组织

        Args:
            external_id: 业务唯一标识

        Returns:
            组织实例

        Raises:
            NotFoundError: 当组织不存在时
        """
        org = await self.repo.get_by_external_id(external_id)
        if not org:
            raise NotFoundError(
                resource_type="Organization",
                resource_id=external_id
            )
        return org

    async def list_organizations(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Organization]:
        """
        列出所有组织

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            组织列表
        """
        return await self.repo.list_all(skip=skip, limit=limit)

    async def paginate_organizations(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters
    ) -> Page[Organization]:
        """
        分页查询组织

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 过滤条件

        Returns:
            分页结果
        """
        return await self.repo.paginate(page=page, page_size=page_size, **filters)

    async def update_organization(
        self,
        id: UUID,
        data: OrganizationUpdate
    ) -> Organization:
        """
        更新组织

        Args:
            id: 组织UUID
            data: 更新数据

        Returns:
            更新后的组织实例

        Raises:
            NotFoundError: 当组织不存在时
        """
        # 过滤掉None值
        update_data = {
            k: v for k, v in data.model_dump().items()
            if v is not None
        }

        if not update_data:
            return await self.get_organization(id)

        return await self.repo.update(id, **update_data)

    async def delete_organization(self, id: UUID) -> bool:
        """
        删除组织（硬删除）

        Args:
            id: 组织UUID

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 当组织不存在时
        """
        organization = await self.get_organization(id)
        deleted = await self.repo.hard_delete(id)
        if self.relationship_service:
            await self.relationship_service.delete_relationships_for_node(
                external_id=organization.external_id,
                node_type=NodeType.ORGANIZATION,
            )
        return deleted

    async def get_primary_organizations(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Organization]:
        """
        获取所有一级目标组织

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            一级目标组织列表
        """
        return await self.repo.get_primary_organizations(skip=skip, limit=limit)

    async def search_organizations(
        self,
        name_pattern: str,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Organization]:
        """
        根据名称搜索组织

        Args:
            name_pattern: 名称搜索模式
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的组织列表
        """
        return await self.repo.search_by_name(
            name_pattern=name_pattern,
            skip=skip,
            limit=limit
        )
