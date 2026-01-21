"""
ClientApplication（客户端应用）ORM模型。

存储移动应用和桌面应用的核心属性与元数据，用于应用安全评估。
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class ClientApplication(Base):
    """
    客户端应用资产模型。

    Attributes:
        id: UUID主键
        external_id: 业务唯一标识（建议使用 app:PLATFORM:PACKAGE_NAME）
        app_name: 应用名称
        package_name: 包名/应用标识符
        version: 版本号
        platform: 平台类型（Android/iOS/Windows/macOS/Linux）
        bundle_id: Bundle标识符（iOS专用）
        risk_score: 风险评分（0-10）
        scope_policy: 范围策略
        metadata_: 元数据（JSONB格式）
        is_deleted: 软删除标记
        deleted_at: 删除时间戳
        created_at: 创建时间戳
        updated_at: 更新时间戳
        created_by: 创建者标识
    """

    __tablename__ = "assets_client_application"

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
        comment="业务唯一标识（建议使用 app:PLATFORM:PACKAGE_NAME）",
    )

    # 核心应用字段
    app_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="应用名称",
    )
    package_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="包名/应用标识符（如 com.example.app）",
    )
    version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="版本号",
    )

    # 平台信息
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="平台类型（Android/iOS/Windows/macOS/Linux）",
    )
    bundle_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Bundle标识符（iOS专用）",
    )

    # 风险评估
    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="风险评分（0-10）",
    )

    # 范围控制
    scope_policy: Mapped[str] = mapped_column(
        String(50),
        default="IN_SCOPE",
        nullable=False,
        index=True,
        comment="范围策略（IN_SCOPE/OUT_OF_SCOPE）",
    )

    # 元数据
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
        comment="元数据（JSONB格式，包含permissions、signatures等）",
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
            name="chk_app_risk_score",
        ),
        CheckConstraint(
            "platform IN ('Android', 'iOS', 'Windows', 'macOS', 'Linux')",
            name="chk_app_platform",
        ),
        {"comment": "客户端应用资产表"},
    )

    def __repr__(self) -> str:
        """返回对象的字符串表示。"""
        return f"<ClientApplication(id={self.id}, app_name={self.app_name}, platform={self.platform})>"
