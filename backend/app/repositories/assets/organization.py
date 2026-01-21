"""
Organization Repository

提供组织资产的数据访问方法。
"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """
    组织资产Repository

    继承BaseRepository，提供组织特定的查询方法。
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        初始化OrganizationRepository

        Args:
            db: 数据库会话
        """
        super().__init__(Organization, db)

    async def get_by_credit_code(self, credit_code: str) -> Organization | None:
        """
        根据统一社会信用代码获取组织

        Args:
            credit_code: 统一社会信用代码

        Returns:
            组织实例，如果不存在或已删除则返回None
        """
        stmt = select(Organization).where(
            Organization.credit_code == credit_code,
            Organization.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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
        stmt = select(Organization).where(
            Organization.is_primary == True,
            Organization.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_tier(
        self,
        tier: int,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Organization]:
        """
        根据层级获取组织列表

        Args:
            tier: 层级（0=总部, 1=子公司）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            指定层级的组织列表
        """
        stmt = select(Organization).where(
            Organization.tier == tier,
            Organization.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_by_name(
        self,
        name_pattern: str,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Organization]:
        """
        根据名称模糊搜索组织

        Args:
            name_pattern: 名称搜索模式（支持%通配符）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的组织列表
        """
        stmt = select(Organization).where(
            Organization.name.ilike(f"%{name_pattern}%"),
            Organization.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
