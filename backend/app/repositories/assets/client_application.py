"""
ClientApplication资产的Repository层。

负责客户端应用资产的数据访问操作，包括标准CRUD和应用特定查询。
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.client_application import ClientApplication
from app.repositories.base import BaseRepository


class ClientApplicationRepository(BaseRepository[ClientApplication]):
    """客户端应用资产的数据访问仓库。"""

    def __init__(self, db: AsyncSession):
        """初始化仓库。

        Args:
            db: 数据库会话
        """
        super().__init__(ClientApplication, db)

    async def get_by_platform(
        self,
        platform: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ClientApplication]:
        """根据平台类型获取应用列表。

        Args:
            platform: 平台类型（Android/iOS/Windows/macOS/Linux）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            应用列表
        """
        stmt = (
            select(ClientApplication)
            .where(
                ClientApplication.platform == platform,
                ClientApplication.is_deleted == False,
            )
            .order_by(ClientApplication.created_at.asc(), ClientApplication.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_package_name(
        self,
        package_name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ClientApplication]:
        """根据包名获取应用列表（精确匹配）。

        Args:
            package_name: 包名/应用标识符
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            应用列表
        """
        stmt = (
            select(ClientApplication)
            .where(
                ClientApplication.package_name == package_name,
                ClientApplication.is_deleted == False,
            )
            .order_by(ClientApplication.created_at.asc(), ClientApplication.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_by_app_name(
        self,
        app_name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ClientApplication]:
        """根据应用名称搜索应用（模糊匹配）。

        Args:
            app_name: 应用名称（模糊匹配）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的应用列表
        """
        stmt = (
            select(ClientApplication)
            .where(
                ClientApplication.app_name.ilike(f"%{app_name}%"),
                ClientApplication.is_deleted == False,
            )
            .order_by(ClientApplication.created_at.asc(), ClientApplication.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_high_risk_applications(
        self,
        risk_threshold: float = 7.0,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ClientApplication]:
        """获取高风险应用列表。

        Args:
            risk_threshold: 风险评分阈值（默认7.0）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            高风险应用列表
        """
        stmt = (
            select(ClientApplication)
            .where(
                ClientApplication.risk_score >= risk_threshold,
                ClientApplication.is_deleted == False,
            )
            .order_by(
                ClientApplication.risk_score.desc(), ClientApplication.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_bundle_id(
        self,
        bundle_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ClientApplication]:
        """根据Bundle ID获取应用列表（iOS专用）。

        Args:
            bundle_id: Bundle标识符
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            应用列表
        """
        stmt = (
            select(ClientApplication)
            .where(
                ClientApplication.bundle_id == bundle_id,
                ClientApplication.is_deleted == False,
            )
            .order_by(ClientApplication.created_at.asc(), ClientApplication.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
