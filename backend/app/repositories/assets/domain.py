"""
Domain Repository

提供域名资产的数据访问方法。
"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.domain import Domain
from app.repositories.base import BaseRepository


class DomainRepository(BaseRepository[Domain]):
    """
    域名资产Repository

    继承BaseRepository，提供域名特定的查询方法。
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        初始化DomainRepository

        Args:
            db: 数据库会话
        """
        super().__init__(Domain, db)

    async def get_by_name(self, name: str) -> Domain | None:
        """
        根据域名获取记录

        Args:
            name: 完整域名

        Returns:
            域名实例，如果不存在或已删除则返回None
        """
        stmt = select(Domain).where(
            Domain.name == name,
            Domain.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_root_domain(
        self,
        root_domain: str,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Domain]:
        """
        根据根域名获取所有子域名

        Args:
            root_domain: 根域名
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            子域名列表
        """
        stmt = select(Domain).where(
            Domain.root_domain == root_domain,
            Domain.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_tier(
        self,
        tier: int,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Domain]:
        """
        根据层级获取域名列表

        Args:
            tier: 层级深度
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            指定层级的域名列表
        """
        stmt = select(Domain).where(
            Domain.tier == tier,
            Domain.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

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
        stmt = select(Domain).where(
            Domain.is_resolved == True,
            Domain.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

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
        stmt = select(Domain).where(
            Domain.is_wildcard == True,
            Domain.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

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
        stmt = select(Domain).where(
            Domain.has_waf == True,
            Domain.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
