"""
Certificate资产的Repository层。

负责证书资产的数据访问操作，包括标准CRUD和证书特定查询。
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.certificate import Certificate
from app.repositories.base import BaseRepository


class CertificateRepository(BaseRepository[Certificate]):
    """证书资产的数据访问仓库。"""

    def __init__(self, db: AsyncSession):
        """初始化仓库。

        Args:
            db: 数据库会话
        """
        super().__init__(Certificate, db)

    async def get_by_subject_cn(
        self,
        subject_cn: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Certificate]:
        """根据主题通用名称获取证书列表。

        Args:
            subject_cn: 主题通用名称（精确匹配）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            证书列表
        """
        stmt = (
            select(Certificate)
            .where(
                Certificate.subject_cn == subject_cn,
                Certificate.is_deleted == False,
            )
            .order_by(Certificate.created_at.asc(), Certificate.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_expired_certificates(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Certificate]:
        """获取已过期的证书列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            已过期的证书列表
        """
        stmt = (
            select(Certificate)
            .where(
                Certificate.is_expired == True,
                Certificate.is_deleted == False,
            )
            .order_by(Certificate.created_at.asc(), Certificate.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_self_signed_certificates(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Certificate]:
        """获取自签名证书列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            自签名证书列表
        """
        stmt = (
            select(Certificate)
            .where(
                Certificate.is_self_signed == True,
                Certificate.is_deleted == False,
            )
            .order_by(Certificate.created_at.asc(), Certificate.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_revoked_certificates(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Certificate]:
        """获取已吊销的证书列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            已吊销的证书列表
        """
        stmt = (
            select(Certificate)
            .where(
                Certificate.is_revoked == True,
                Certificate.is_deleted == False,
            )
            .order_by(Certificate.created_at.asc(), Certificate.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_by_issuer(
        self,
        issuer_cn: str | None = None,
        issuer_org: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Certificate]:
        """根据颁发者信息搜索证书。

        Args:
            issuer_cn: 颁发者通用名称（模糊匹配）
            issuer_org: 颁发者组织名称（模糊匹配）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的证书列表
        """
        stmt = select(Certificate).where(Certificate.is_deleted == False)

        if issuer_cn is not None:
            stmt = stmt.where(Certificate.issuer_cn.ilike(f"%{issuer_cn}%"))
        if issuer_org is not None:
            stmt = stmt.where(Certificate.issuer_org.ilike(f"%{issuer_org}%"))

        stmt = (
            stmt.order_by(Certificate.created_at.asc(), Certificate.id.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_expiring_soon(
        self,
        days_threshold: int = 30,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Certificate]:
        """获取即将过期的证书列表（剩余天数小于阈值且未过期）。

        Args:
            days_threshold: 剩余天数阈值（默认30天）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            即将过期的证书列表
        """
        stmt = (
            select(Certificate)
            .where(
                Certificate.is_expired == False,
                Certificate.is_deleted == False,
                Certificate.days_to_expire != None,
                Certificate.days_to_expire <= days_threshold,
                Certificate.days_to_expire >= 0,
            )
            .order_by(Certificate.days_to_expire.asc(), Certificate.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
