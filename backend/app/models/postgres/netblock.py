"""
Netblock（网段）ORM模型。

表示一段连续的IP地址范围，用于管理网络资产的拓扑结构。
"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import CIDR, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Netblock(Base):
    """
    网段资产模型。

    Attributes:
        id: UUID主键
        external_id: 业务唯一标识（与Neo4j节点id对齐）
        cidr: 网段CIDR表示
        asn_number: AS自治系统号
        capacity: 网段可容纳的IP地址数量
        live_count: 存活的IP数量
        risk_score: 风险评分（0-10）
        scope_policy: 范围策略（IN_SCOPE/OUT_OF_SCOPE）
        is_internal: 是否为内网段（RFC1918私有地址）
        metadata_: 元数据（JSONB格式）
        is_deleted: 软删除标记
        deleted_at: 删除时间戳
        created_at: 创建时间戳
        updated_at: 更新时间戳
        created_by: 创建者标识
    """

    __tablename__ = "assets_netblock"

    # 主键与唯一标识
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="UUID主键",
    )
    external_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="业务唯一标识（与Neo4j节点id对齐）",
    )

    # 核心网段字段
    cidr: Mapped[str] = mapped_column(
        CIDR,
        unique=True,
        nullable=False,
        index=True,
        comment="网段CIDR表示（如 192.168.0.0/24）",
    )
    asn_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="AS自治系统号（如 AS37963）",
    )

    # 拓扑统计属性
    capacity: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="网段可容纳的IP地址数量（自动从CIDR计算）",
    )
    live_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="存活的IP数量",
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 1),
        default=Decimal("0.0"),
        nullable=False,
        comment="风险评分（0.0-10.0）",
    )

    # 范围与分类
    scope_policy: Mapped[str] = mapped_column(
        String(50),
        default="IN_SCOPE",
        nullable=False,
        index=True,
        comment="范围策略（IN_SCOPE/OUT_OF_SCOPE）",
    )
    is_internal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否为内网段（RFC1918私有地址）",
    )

    # 元数据（使用 metadata_ 避免与 SQLAlchemy 的 metadata 属性冲突）
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
        comment="元数据（JSONB格式，包含net_name、description等）",
    )

    # 软删除
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="软删除标记",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间戳",
    )

    # 审计字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="创建时间戳",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间戳",
    )
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="创建者标识",
    )

    # 表级约束
    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 10",
            name="chk_netblock_risk_score",
        ),
        CheckConstraint(
            "live_count >= 0",
            name="chk_netblock_live_count",
        ),
        CheckConstraint(
            "capacity IS NULL OR capacity >= 0",
            name="chk_netblock_capacity",
        ),
        CheckConstraint(
            "capacity IS NULL OR live_count <= capacity",
            name="chk_netblock_live_count_capacity",
        ),
        {"comment": "网段资产表"},
    )

    def __repr__(self) -> str:
        """返回对象的字符串表示。"""
        return f"<Netblock(id={self.id}, cidr={self.cidr}, asn={self.asn_number})>"
