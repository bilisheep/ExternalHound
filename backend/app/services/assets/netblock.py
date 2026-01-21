"""
Netblock Service。

提供网段资产的业务逻辑，包括自动计算capacity和判断is_internal。
"""

from __future__ import annotations

import ipaddress
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import Page
from app.models.postgres.netblock import Netblock
from app.repositories.assets.netblock import NetblockRepository
from app.schemas.assets.netblock import NetblockCreate, NetblockUpdate
from app.utils.external_id import generate_netblock_external_id


class NetblockService:
    """
    网段资产Service。

    处理网段相关的业务逻辑，包括CIDR capacity自动计算和私有网段自动判定。
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        初始化NetblockService。

        Args:
            db: 数据库会话
        """
        self.db = db
        self.repo = NetblockRepository(db)

    async def create_netblock(self, data: NetblockCreate) -> Netblock:
        """
        创建网段。

        自动计算网段容量（capacity）并根据RFC1918判定is_internal（如果未指定）。

        Args:
            data: 网段创建数据

        Returns:
            创建的网段实例

        Raises:
            ConflictError: 当external_id或cidr已存在时
        """
        external_id = data.external_id.strip() if data.external_id else None
        if not external_id:
            external_id = generate_netblock_external_id(data.cidr)

        # 检查external_id唯一性
        existing = await self.repo.get_by_external_id(external_id)
        if existing:
            raise ConflictError(
                resource_type="Netblock",
                field="external_id",
                value=external_id,
            )

        # 检查cidr唯一性
        existing_cidr = await self.repo.get_by_cidr(data.cidr)
        if existing_cidr:
            raise ConflictError(
                resource_type="Netblock",
                field="cidr",
                value=data.cidr,
            )

        # 准备创建数据
        create_data = data.model_dump()
        create_data["external_id"] = external_id
        network = ipaddress.ip_network(create_data["cidr"], strict=False)

        # 自动计算capacity
        create_data["capacity"] = int(network.num_addresses)

        # 自动判定is_internal（如果未指定）
        if create_data.get("is_internal") is None:
            create_data["is_internal"] = network.is_private

        return await self.repo.create(**create_data)

    async def get_netblock(self, id: UUID) -> Netblock:
        """
        获取网段详情。

        Args:
            id: 网段UUID

        Returns:
            网段实例

        Raises:
            NotFoundError: 当网段不存在时
        """
        netblock = await self.repo.get_by_id(id)
        if not netblock:
            raise NotFoundError(
                resource_type="Netblock",
                resource_id=str(id),
            )
        return netblock

    async def get_netblock_by_external_id(self, external_id: str) -> Netblock:
        """
        根据业务ID获取网段。

        Args:
            external_id: 业务唯一标识

        Returns:
            网段实例

        Raises:
            NotFoundError: 当网段不存在时
        """
        netblock = await self.repo.get_by_external_id(external_id)
        if not netblock:
            raise NotFoundError(
                resource_type="Netblock",
                resource_id=external_id,
            )
        return netblock

    async def get_netblock_by_cidr(self, cidr: str) -> Netblock:
        """
        根据CIDR获取网段。

        Args:
            cidr: 网段CIDR表示

        Returns:
            网段实例

        Raises:
            NotFoundError: 当网段不存在时
        """
        netblock = await self.repo.get_by_cidr(cidr)
        if not netblock:
            raise NotFoundError(
                resource_type="Netblock",
                resource_id=cidr,
            )
        return netblock

    async def list_netblocks(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[Netblock]:
        """
        列出所有网段。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            网段列表
        """
        return await self.repo.list_all(skip=skip, limit=limit)

    async def paginate_netblocks(
        self, page: int = 1, page_size: int = 20, **filters
    ) -> Page[Netblock]:
        """
        分页查询网段。

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 过滤条件

        Returns:
            分页结果
        """
        return await self.repo.paginate(page=page, page_size=page_size, **filters)

    async def update_netblock(self, id: UUID, data: NetblockUpdate) -> Netblock:
        """
        更新网段。

        Args:
            id: 网段UUID
            data: 更新数据

        Returns:
            更新后的网段实例

        Raises:
            NotFoundError: 当网段不存在时
        """
        # 过滤空值
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            return await self.get_netblock(id)

        return await self.repo.update(id, **update_data)

    async def delete_netblock(self, id: UUID) -> bool:
        """
        删除网段（软删除）。

        Args:
            id: 网段UUID

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 当网段不存在时
        """
        return await self.repo.soft_delete(id)

    async def get_internal_netblocks(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[Netblock]:
        """
        获取所有内网段。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            内网段列表
        """
        return await self.repo.get_internal_netblocks(skip=skip, limit=limit)

    async def get_netblocks_by_asn(
        self, asn_number: str, skip: int = 0, limit: int = 100
    ) -> Sequence[Netblock]:
        """
        根据AS号获取网段列表。

        Args:
            asn_number: AS自治系统号
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            指定AS的网段列表
        """
        return await self.repo.get_by_asn(
            asn_number=asn_number,
            skip=skip,
            limit=limit,
        )

    async def get_netblocks_containing_ip(
        self, ip_address: str, skip: int = 0, limit: int = 100
    ) -> Sequence[Netblock]:
        """
        获取包含指定IP的网段列表。

        Args:
            ip_address: IP地址
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            网段列表
        """
        return await self.repo.get_containing_ip(
            ip_address=ip_address,
            skip=skip,
            limit=limit,
        )

    async def get_overlapping_netblocks(
        self, cidr: str, skip: int = 0, limit: int = 100
    ) -> Sequence[Netblock]:
        """
        获取与指定CIDR有交集的网段列表。

        Args:
            cidr: 网段CIDR表示
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            网段列表
        """
        return await self.repo.get_overlapping(
            cidr=cidr,
            skip=skip,
            limit=limit,
        )
