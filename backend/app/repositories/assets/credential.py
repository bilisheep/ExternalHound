"""
Credential资产的Repository层。

负责凭证资产的数据访问操作，包括标准CRUD和凭证特定查询。
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.credential import Credential
from app.repositories.base import BaseRepository


class CredentialRepository(BaseRepository[Credential]):
    """凭证资产的数据访问仓库。"""

    def __init__(self, db: AsyncSession):
        """初始化仓库。

        Args:
            db: 数据库会话
        """
        super().__init__(Credential, db)

    async def get_by_cred_type(
        self,
        cred_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Credential]:
        """根据凭证类型获取凭证列表。

        Args:
            cred_type: 凭证类型
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            凭证列表
        """
        stmt = (
            select(Credential)
            .where(
                Credential.cred_type == cred_type,
                Credential.is_deleted == False,
            )
            .order_by(Credential.created_at.asc(), Credential.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_leaked_credentials(
        self,
        min_leaked_count: int = 1,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Credential]:
        """获取泄露凭证列表（泄露次数大于等于阈值）。

        Args:
            min_leaked_count: 最小泄露次数（默认1）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            泄露凭证列表
        """
        stmt = (
            select(Credential)
            .where(
                Credential.leaked_count >= min_leaked_count,
                Credential.is_deleted == False,
            )
            .order_by(Credential.leaked_count.desc(), Credential.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_provider(
        self,
        provider: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Credential]:
        """根据提供方获取凭证列表。

        Args:
            provider: 提供方/来源
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            凭证列表
        """
        stmt = (
            select(Credential)
            .where(
                Credential.provider.ilike(f"%{provider}%"),
                Credential.is_deleted == False,
            )
            .order_by(Credential.created_at.asc(), Credential.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_by_username(
        self,
        username: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Credential]:
        """根据用户名搜索凭证（模糊匹配）。

        Args:
            username: 用户名
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的凭证列表
        """
        stmt = (
            select(Credential)
            .where(
                Credential.username.ilike(f"%{username}%"),
                Credential.is_deleted == False,
            )
            .order_by(Credential.created_at.asc(), Credential.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_by_email(
        self,
        email: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Credential]:
        """根据电子邮箱搜索凭证（模糊匹配）。

        Args:
            email: 电子邮箱
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的凭证列表
        """
        stmt = (
            select(Credential)
            .where(
                Credential.email.ilike(f"%{email}%"),
                Credential.is_deleted == False,
            )
            .order_by(Credential.created_at.asc(), Credential.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_validation_result(
        self,
        validation_result: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Credential]:
        """根据验证结果获取凭证列表。

        Args:
            validation_result: 验证结果（VALID/INVALID/UNKNOWN）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            凭证列表
        """
        stmt = (
            select(Credential)
            .where(
                Credential.validation_result == validation_result,
                Credential.is_deleted == False,
            )
            .order_by(Credential.created_at.asc(), Credential.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_valid_credentials(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Credential]:
        """获取有效凭证列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            有效凭证列表
        """
        return await self.get_by_validation_result("VALID", skip, limit)
