"""
Netblock Repository。

提供网段资产的数据访问方法，包括CIDR相关的特殊查询。
"""

from typing import Sequence

from sqlalchemy import cast, literal, select
from sqlalchemy.dialects.postgresql import CIDR, INET
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.netblock import Netblock
from app.repositories.base import BaseRepository


class NetblockRepository(BaseRepository[Netblock]):
    """
    网段资产Repository。

    继承BaseRepository，提供网段特定的查询方法，包括CIDR包含、交叉等拓扑查询。
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        初始化NetblockRepository。

        Args:
            db: 数据库会话
        """
        super().__init__(Netblock, db)

    async def get_by_cidr(self, cidr: str) -> Netblock | None:
        """
        根据CIDR获取网段记录。

        Args:
            cidr: 网段CIDR表示

        Returns:
            网段实例，如果不存在或已删除则返回None
        """
        stmt = select(Netblock).where(
            Netblock.cidr == cast(cidr, CIDR),
            Netblock.is_deleted == False,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_asn(
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
        stmt = (
            select(Netblock)
            .where(
                Netblock.asn_number == asn_number,
                Netblock.is_deleted == False,  # noqa: E712
            )
            .order_by(Netblock.created_at.asc(), Netblock.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

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
        stmt = (
            select(Netblock)
            .where(
                Netblock.is_internal == True,  # noqa: E712
                Netblock.is_deleted == False,  # noqa: E712
            )
            .order_by(Netblock.created_at.asc(), Netblock.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_containing_ip(
        self, ip_address: str, skip: int = 0, limit: int = 100
    ) -> Sequence[Netblock]:
        """
        获取包含指定IP的网段列表（使用PostgreSQL CIDR包含运算符>>）。

        Args:
            ip_address: IP地址
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            包含指定IP的网段列表
        """
        ip_literal = cast(literal(ip_address), INET)
        stmt = (
            select(Netblock)
            .where(
                Netblock.cidr.op(">>")(ip_literal),
                Netblock.is_deleted == False,  # noqa: E712
            )
            .order_by(Netblock.created_at.asc(), Netblock.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_overlapping(
        self, cidr: str, skip: int = 0, limit: int = 100
    ) -> Sequence[Netblock]:
        """
        获取与指定CIDR有交集的网段列表（使用PostgreSQL CIDR重叠运算符&&）。

        Args:
            cidr: 网段CIDR表示
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            相交的网段列表
        """
        cidr_literal = cast(literal(cidr), CIDR)
        stmt = (
            select(Netblock)
            .where(
                Netblock.cidr.op("&&")(cidr_literal),
                Netblock.is_deleted == False,  # noqa: E712
            )
            .order_by(Netblock.created_at.asc(), Netblock.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
