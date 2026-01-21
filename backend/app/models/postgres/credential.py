"""
Credential（凭证）ORM模型。

存储泄露凭证的核心属性与元数据，用于凭证泄露监测和安全评估。
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Credential(Base):
    """
    凭证资产模型。

    Attributes:
        id: UUID主键
        external_id: 业务唯一标识（建议使用 cred:TYPE:HASH）
        cred_type: 凭证类型（PASSWORD/API_KEY/TOKEN/SSH_KEY/CERTIFICATE等）
        provider: 提供方/来源（如 GitHub、AWS、Google）
        username: 用户名
        email: 电子邮箱
        phone: 电话号码
        leaked_count: 泄露次数
        content: 凭证内容（JSONB格式，敏感信息）
        validation_result: 验证结果（VALID/INVALID/UNKNOWN）
        scope_policy: 范围策略
        metadata_: 元数据（JSONB格式）
        is_deleted: 软删除标记
        deleted_at: 删除时间戳
        created_at: 创建时间戳
        updated_at: 更新时间戳
        created_by: 创建者标识
    """

    __tablename__ = "assets_credential"

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
        comment="业务唯一标识（建议使用 cred:TYPE:HASH）",
    )

    # 核心凭证字段
    cred_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="凭证类型（PASSWORD/API_KEY/TOKEN/SSH_KEY/CERTIFICATE等）",
    )
    provider: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="提供方/来源（如 GitHub、AWS、Google）",
    )

    # 身份标识
    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="用户名",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="电子邮箱",
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="电话号码",
    )

    # 泄露统计
    leaked_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="泄露次数",
    )

    # 凭证内容（敏感信息，JSONB存储）
    content: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="凭证内容（JSONB格式，包含password_hash、api_key等敏感信息）",
    )

    # 验证结果
    validation_result: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="验证结果（VALID/INVALID/UNKNOWN）",
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
        comment="元数据（JSONB格式，包含source、breach_date等）",
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
            "leaked_count >= 0",
            name="chk_cred_leaked_count",
        ),
        CheckConstraint(
            "validation_result IS NULL OR validation_result IN ('VALID', 'INVALID', 'UNKNOWN')",
            name="chk_cred_validation_result",
        ),
        {"comment": "凭证资产表"},
    )

    def __repr__(self) -> str:
        """返回对象的字符串表示。"""
        return f"<Credential(id={self.id}, cred_type={self.cred_type}, username={self.username})>"
