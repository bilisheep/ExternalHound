"""
Organization（组织）ORM模型

组织是资产归属的根节点，代表商业实体。
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base

if TYPE_CHECKING:
    pass  # 用于类型检查时的循环导入


class Organization(Base):
    """
    组织/公司实体

    代表资产图谱的根节点，所有资产最终都应追溯到某个组织。

    Attributes:
        id: UUID主键
        external_id: 业务唯一标识（与Neo4j节点id对齐）
        name: 简短名称，用于显示
        full_name: 完整注册名称
        credit_code: 统一社会信用代码（中国企业）
        is_primary: 是否为一级目标/根目标
        tier: 层级（0=总部, 1=一级子公司, 2=孙公司...）
        asset_count: 该组织下的资产总数（聚合字段）
        risk_score: 风险评分（0-10）
        scope_policy: 范围策略（IN_SCOPE/OUT_OF_SCOPE）
        metadata: 灵活的元数据字段（JSONB）
        is_deleted: 软删除标记
        deleted_at: 删除时间
        created_at: 创建时间
        updated_at: 更新时间
        created_by: 创建者
    """

    __tablename__ = "assets_organization"

    # 主键与标识
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="UUID主键"
    )
    external_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="业务唯一标识（与Neo4j节点id对齐）"
    )

    # 核心字段
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="简短名称"
    )
    full_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="完整注册名称"
    )
    credit_code: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="统一社会信用代码"
    )

    # 拓扑属性
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否为一级目标"
    )
    tier: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="层级：0=总部, 1=子公司"
    )
    asset_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="资产总数（聚合字段）"
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 1),
        default=Decimal("0.0"),
        nullable=False,
        comment="风险评分 0-10"
    )

    # 范围控制
    scope_policy: Mapped[str] = mapped_column(
        String(50),
        default="IN_SCOPE",
        nullable=False,
        index=True,
        comment="范围策略：IN_SCOPE, OUT_OF_SCOPE"
    )

    # 元数据（JSONB灵活字段）
    # 使用 metadata_ 避免与 SQLAlchemy 的 metadata 属性冲突
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
        comment="元数据（JSONB）"
    )

    # 软删除
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="软删除标记"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间"
    )

    # 审计字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="创建者"
    )

    # 约束
    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 10",
            name="chk_org_risk_score"
        ),
        CheckConstraint(
            "tier >= 0",
            name="chk_org_tier"
        ),
        CheckConstraint(
            "asset_count >= 0",
            name="chk_org_asset_count"
        ),
        {"comment": "组织/公司表"}
    )

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Organization(id={self.id}, name={self.name})>"
