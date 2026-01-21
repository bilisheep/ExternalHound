"""
IP Repository

提供IP资产的数据访问方法。
"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, cast
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.ip import IP
from app.repositories.base import BaseRepository


class IPRepository(BaseRepository[IP]):
    """
    IP资产Repository

    继承BaseRepository，提供IP特定的查询方法。
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        初始化IPRepository

        Args:
            db: 数据库会话
        """
        super().__init__(IP, db)

    async def get_by_address(self, address: str) -> IP | None:
        """
        根据IP地址获取记录

        Args:
            address: IP地址

        Returns:
            IP实例，如果不存在或已删除则返回None
        """
        stmt = select(IP).where(
            IP.address == cast(address, INET),
            IP.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_version(
        self,
        version: int,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[IP]:
        """
        根据IP版本获取IP列表

        Args:
            version: IP版本（4或6）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            指定版本的IP列表
        """
        stmt = select(IP).where(
            IP.version == version,
            IP.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

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
        stmt = select(IP).where(
            IP.is_cloud == True,
            IP.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

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
        stmt = select(IP).where(
            IP.is_internal == True,
            IP.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_cdn_ips(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[IP]:
        """
        获取所有CDN节点IP

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            CDN节点IP列表
        """
        stmt = select(IP).where(
            IP.is_cdn == True,
            IP.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_country(
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
        stmt = select(IP).where(
            IP.country_code == country_code.upper(),
            IP.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_asn(
        self,
        asn_number: str,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[IP]:
        """
        根据AS号获取IP列表

        Args:
            asn_number: AS号
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            指定AS的IP列表
        """
        stmt = select(IP).where(
            IP.asn_number == asn_number,
            IP.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

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
        stmt = select(IP).where(
            IP.risk_score >= min_risk_score,
            IP.is_deleted == False
        ).order_by(IP.risk_score.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
