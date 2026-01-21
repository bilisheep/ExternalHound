"""
Domain（域名）ORM模型

DNS体系中的节点，不区分Domain和Subdomain。
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base

if TYPE_CHECKING:
    pass


class Domain(Base):
    """
    域名实体

    DNS体系中的节点。注意：本架构不区分Domain和Subdomain，
    所有层级域名均为Domain节点。

    Attributes:
        id: UUID主键
        external_id: 业务唯一标识（与Neo4j节点id对齐）
        name: 完整域名
        root_domain: 根域名（用于聚合）
        tier: 层级深度（target.com=1, api.target.com=2）
        is_resolved: 是否能解析出IP
        is_wildcard: 是否为泛解析域名
        is_internal: 是否解析到内网IP
        has_waf: 是否有WAF防护
        scope_policy: 范围策略
        metadata: 元数据（DNS记录、ICP备案、技术栈等）
        is_deleted: 软删除标记
        deleted_at: 删除时间
        created_at: 创建时间
        updated_at: 更新时间
        created_by: 创建者
    """

    __tablename__ = "assets_domain"

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
        unique=True,
        nullable=False,
        index=True,
        comment="完整域名"
    )
    root_domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="根域名（用于聚合）"
    )
    tier: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="层级深度"
    )

    # 攻击面状态
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否能解析"
    )
    is_wildcard: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为泛解析"
    )
    is_internal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否解析到内网"
    )
    has_waf: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否有WAF"
    )

    # 范围控制
    scope_policy: Mapped[str] = mapped_column(
        String(50),
        default="IN_SCOPE",
        nullable=False,
        index=True,
        comment="范围策略"
    )

    # 元数据
    # 使用 metadata_ 避免与 SQLAlchemy 的 metadata 属性冲突
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
        comment="元数据（DNS记录、ICP备案、技术栈等）"
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
            "tier >= 1",
            name="chk_domain_tier"
        ),
        {"comment": "域名表"}
    )

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Domain(id={self.id}, name={self.name})>"
