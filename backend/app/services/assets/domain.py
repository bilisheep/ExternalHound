"""
Domain Service

提供域名资产的业务逻辑。
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.pagination import Page
from app.models.postgres.domain import Domain
from app.repositories.assets.domain import DomainRepository
from app.schemas.assets.domain import DomainCreate, DomainUpdate
from app.utils.external_id import generate_domain_external_id


class DomainService:
    """
    域名资产Service

    处理域名相关的业务逻辑。
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        初始化DomainService

        Args:
            db: 数据库会话
        """
        self.db = db
        self.repo = DomainRepository(db)

    async def create_domain(self, data: DomainCreate) -> Domain:
        """
        创建域名

        Args:
            data: 域名创建数据

        Returns:
            创建的域名实例

        Raises:
            ConflictError: 当external_id或name已存在时
        """
        external_id = data.external_id.strip() if data.external_id else None
        if not external_id:
            external_id = generate_domain_external_id(data.name)

        # 检查external_id是否已存在
        existing = await self.repo.get_by_external_id(external_id)
        if existing:
            raise ConflictError(
                resource_type="Domain",
                field="external_id",
                value=external_id
            )

        # 检查域名是否已存在
        existing_name = await self.repo.get_by_name(data.name)
        if existing_name:
            raise ConflictError(
                resource_type="Domain",
                field="name",
                value=data.name
            )

        # 创建域名
        create_data = data.model_dump()
        create_data["external_id"] = external_id
        return await self.repo.create(**create_data)

    async def get_domain(self, id: UUID) -> Domain:
        """
        获取域名详情

        Args:
            id: 域名UUID

        Returns:
            域名实例

        Raises:
            NotFoundError: 当域名不存在时
        """
        domain = await self.repo.get_by_id(id)
        if not domain:
            raise NotFoundError(
                resource_type="Domain",
                resource_id=str(id)
            )
        return domain

    async def get_domain_by_external_id(self, external_id: str) -> Domain:
        """
        根据业务ID获取域名

        Args:
            external_id: 业务唯一标识

        Returns:
            域名实例

        Raises:
            NotFoundError: 当域名不存在时
        """
        domain = await self.repo.get_by_external_id(external_id)
        if not domain:
            raise NotFoundError(
                resource_type="Domain",
                resource_id=external_id
            )
        return domain

    async def get_domain_by_name(self, name: str) -> Domain:
        """
        根据域名获取记录

        Args:
            name: 完整域名

        Returns:
            域名实例

        Raises:
            NotFoundError: 当域名不存在时
        """
        domain = await self.repo.get_by_name(name)
        if not domain:
            raise NotFoundError(
                resource_type="Domain",
                resource_id=name
            )
        return domain

    async def list_domains(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Domain]:
        """
        列出所有域名

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            域名列表
        """
        return await self.repo.list_all(skip=skip, limit=limit)

    async def paginate_domains(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters
    ) -> Page[Domain]:
        """
        分页查询域名

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 过滤条件

        Returns:
            分页结果
        """
        return await self.repo.paginate(page=page, page_size=page_size, **filters)

    async def update_domain(
        self,
        id: UUID,
        data: DomainUpdate
    ) -> Domain:
        """
        更新域名

        Args:
            id: 域名UUID
            data: 更新数据

        Returns:
            更新后的域名实例

        Raises:
            NotFoundError: 当域名不存在时
            ConflictError: 当更新的name已存在时
        """
        # 如果要更新name，检查是否与其他域名冲突
        if data.name:
            existing = await self.repo.get_by_name(data.name)
            if existing and existing.id != id:
                raise ConflictError(
                    resource_type="Domain",
                    field="name",
                    value=data.name
                )

        # 过滤掉None值
        update_data = {
            k: v for k, v in data.model_dump().items()
            if v is not None
        }

        if not update_data:
            return await self.get_domain(id)

        return await self.repo.update(id, **update_data)

    async def delete_domain(self, id: UUID) -> bool:
        """
        删除域名（软删除）

        Args:
            id: 域名UUID

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 当域名不存在时
        """
        return await self.repo.soft_delete(id)

    async def get_subdomains(
        self,
        root_domain: str,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Domain]:
        """
        获取指定根域名的所有子域名

        Args:
            root_domain: 根域名
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            子域名列表
        """
        return await self.repo.get_by_root_domain(
            root_domain=root_domain,
            skip=skip,
            limit=limit
        )

    async def get_resolved_domains(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Domain]:
        """
        获取所有已解析的域名

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            已解析的域名列表
        """
        return await self.repo.get_resolved_domains(skip=skip, limit=limit)

    async def get_wildcard_domains(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Domain]:
        """
        获取所有泛解析域名

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            泛解析域名列表
        """
        return await self.repo.get_wildcard_domains(skip=skip, limit=limit)

    async def get_domains_with_waf(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Domain]:
        """
        获取所有有WAF的域名

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            有WAF的域名列表
        """
        return await self.repo.get_domains_with_waf(skip=skip, limit=limit)
