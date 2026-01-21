"""
Service资产的Repository层。

负责服务资产的数据访问操作，包括标准CRUD和服务特定查询。
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.service import Service
from app.repositories.base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    """服务资产的数据访问仓库。"""

    def __init__(self, db: AsyncSession):
        """初始化仓库。

        Args:
            db: 数据库会话
        """
        super().__init__(Service, db)

    async def get_by_port(
        self,
        port: int,
        protocol: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Service]:
        """根据端口号获取服务列表。

        Args:
            port: 端口号
            protocol: 协议类型（可选，TCP/UDP）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            服务列表
        """
        stmt = select(Service).where(
            Service.port == port,
            Service.is_deleted == False,
        )

        if protocol is not None:
            stmt = stmt.where(Service.protocol == protocol.upper())

        stmt = (
            stmt.order_by(Service.created_at.asc(), Service.id.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_service_name(
        self,
        service_name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Service]:
        """根据服务名称获取服务列表。

        Args:
            service_name: 服务名称（精确匹配，不区分大小写）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            服务列表
        """
        stmt = (
            select(Service)
            .where(
                Service.service_name.ilike(service_name),
                Service.is_deleted == False,
            )
            .order_by(Service.created_at.asc(), Service.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_http_services(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Service]:
        """获取所有HTTP/HTTPS服务列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            HTTP/HTTPS服务列表
        """
        stmt = (
            select(Service)
            .where(
                Service.is_http == True,
                Service.is_deleted == False,
            )
            .order_by(Service.created_at.asc(), Service.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_by_product(
        self,
        product: str,
        version: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Service]:
        """根据产品名称和版本搜索服务。

        Args:
            product: 产品名称（模糊匹配）
            version: 版本号（可选，精确匹配）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的服务列表
        """
        stmt = select(Service).where(
            Service.product.ilike(f"%{product}%"),
            Service.is_deleted == False,
        )

        if version is not None:
            stmt = stmt.where(Service.version == version)

        stmt = (
            stmt.order_by(Service.created_at.asc(), Service.id.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_asset_category(
        self,
        asset_category: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Service]:
        """根据资产分类获取服务列表。

        Args:
            asset_category: 资产分类（如 WEB、DATABASE、MIDDLEWARE等）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配分类的服务列表
        """
        stmt = (
            select(Service)
            .where(
                Service.asset_category == asset_category,
                Service.is_deleted == False,
            )
            .order_by(Service.created_at.asc(), Service.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_high_risk_services(
        self,
        risk_threshold: float = 7.0,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Service]:
        """获取高风险服务列表。

        Args:
            risk_threshold: 风险评分阈值（默认7.0）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            高风险服务列表
        """
        stmt = (
            select(Service)
            .where(
                Service.risk_score >= risk_threshold,
                Service.is_deleted == False,
            )
            .order_by(Service.risk_score.desc(), Service.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
