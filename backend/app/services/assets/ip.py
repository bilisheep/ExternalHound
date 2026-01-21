"""
IP Service

提供IP资产的业务逻辑。
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.pagination import Page
from app.models.postgres.ip import IP
from app.repositories.assets.ip import IPRepository
from app.schemas.assets.ip import IPCreate, IPUpdate
from app.utils.external_id import generate_ip_external_id


class IPService:
    """
    IP资产Service

    处理IP相关的业务逻辑。
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        初始化IPService

        Args:
            db: 数据库会话
        """
        self.db = db
        self.repo = IPRepository(db)

    async def create_ip(self, data: IPCreate) -> IP:
        """
        创建IP

        Args:
            data: IP创建数据

        Returns:
            创建的IP实例

        Raises:
            ConflictError: 当external_id或address已存在时
        """
        external_id = data.external_id.strip() if data.external_id else None
        if not external_id:
            external_id = generate_ip_external_id(data.address)

        # 检查external_id是否已存在
        existing = await self.repo.get_by_external_id(external_id)
        if existing:
            raise ConflictError(
                resource_type="IP",
                field="external_id",
                value=external_id
            )

        # 检查IP地址是否已存在
        existing_address = await self.repo.get_by_address(data.address)
        if existing_address:
            raise ConflictError(
                resource_type="IP",
                field="address",
                value=data.address
            )

        # 如果没有提供version，自动检测
        create_data = data.model_dump()
        create_data["external_id"] = external_id
        if create_data.get("version") is None:
            create_data["version"] = data.detect_version()

        # 创建IP
        return await self.repo.create(**create_data)

    async def get_ip(self, id: UUID) -> IP:
        """
        获取IP详情

        Args:
            id: IP UUID

        Returns:
            IP实例

        Raises:
            NotFoundError: 当IP不存在时
        """
        ip = await self.repo.get_by_id(id)
        if not ip:
            raise NotFoundError(
                resource_type="IP",
                resource_id=str(id)
            )
        return ip

    async def get_ip_by_external_id(self, external_id: str) -> IP:
        """
        根据业务ID获取IP

        Args:
            external_id: 业务唯一标识

        Returns:
            IP实例

        Raises:
            NotFoundError: 当IP不存在时
        """
        ip = await self.repo.get_by_external_id(external_id)
        if not ip:
            raise NotFoundError(
                resource_type="IP",
                resource_id=external_id
            )
        return ip

    async def get_ip_by_address(self, address: str) -> IP:
        """
        根据IP地址获取记录

        Args:
            address: IP地址

        Returns:
            IP实例

        Raises:
            NotFoundError: 当IP不存在时
        """
        ip = await self.repo.get_by_address(address)
        if not ip:
            raise NotFoundError(
                resource_type="IP",
                resource_id=address
            )
        return ip

    async def list_ips(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[IP]:
        """
        列出所有IP

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            IP列表
        """
        return await self.repo.list_all(skip=skip, limit=limit)

    async def paginate_ips(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters
    ) -> Page[IP]:
        """
        分页查询IP

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 过滤条件

        Returns:
            分页结果
        """
        return await self.repo.paginate(page=page, page_size=page_size, **filters)

    async def update_ip(
        self,
        id: UUID,
        data: IPUpdate
    ) -> IP:
        """
        更新IP

        Args:
            id: IP UUID
            data: 更新数据

        Returns:
            更新后的IP实例

        Raises:
            NotFoundError: 当IP不存在时
        """
        # 过滤掉None值
        update_data = {
            k: v for k, v in data.model_dump().items()
            if v is not None
        }

        if not update_data:
            return await self.get_ip(id)

        return await self.repo.update(id, **update_data)

    async def delete_ip(self, id: UUID) -> bool:
        """
        删除IP（软删除）

        Args:
            id: IP UUID

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 当IP不存在时
        """
        return await self.repo.soft_delete(id)

    async def get_cloud_ips(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[IP]:
        """
        获取所有云主机IP

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            云主机IP列表
        """
        return await self.repo.get_cloud_ips(skip=skip, limit=limit)

    async def get_internal_ips(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[IP]:
        """
        获取所有内网IP

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            内网IP列表
        """
        return await self.repo.get_internal_ips(skip=skip, limit=limit)

    async def get_high_risk_ips(
        self,
        min_risk_score: float = 7.0,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[IP]:
        """
        获取高风险IP列表

        Args:
            min_risk_score: 最小风险分数阈值
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            高风险IP列表
        """
        return await self.repo.get_high_risk_ips(
            min_risk_score=min_risk_score,
            skip=skip,
            limit=limit
        )

    async def get_ips_by_country(
        self,
        country_code: str,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[IP]:
        """
        根据国家代码获取IP列表

        Args:
            country_code: 国家代码（ISO 3166-1 alpha-2）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            指定国家的IP列表
        """
        return await self.repo.get_by_country(
            country_code=country_code,
            skip=skip,
            limit=limit
        )
