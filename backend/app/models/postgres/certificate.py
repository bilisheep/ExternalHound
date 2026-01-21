"""
Certificate（证书）ORM模型。

存储SSL/TLS证书的核心属性与元数据，用于证书管理和风险评估。
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
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


class Certificate(Base):
    """
    证书资产模型。

    Attributes:
        id: UUID主键
        external_id: 业务唯一标识（建议使用 cert:SHA256）
        subject_cn: 主题通用名称
        issuer_cn: 颁发者通用名称
        issuer_org: 颁发者组织
        valid_from: 生效时间戳（Unix秒）
        valid_to: 过期时间戳（Unix秒）
        days_to_expire: 剩余有效天数
        is_expired: 是否已过期
        is_self_signed: 是否为自签名证书
        is_revoked: 是否已被吊销
        san_count: SAN（主题备用名称）数量
        scope_policy: 范围策略
        metadata_: 元数据（JSONB格式）
        is_deleted: 软删除标记
        deleted_at: 删除时间戳
        created_at: 创建时间戳
        updated_at: 更新时间戳
        created_by: 创建者标识
    """

    __tablename__ = "assets_certificate"

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
        comment="业务唯一标识（建议使用 cert:SHA256）",
    )

    # 核心证书字段
    subject_cn: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="主题通用名称（Subject Common Name）",
    )
    issuer_cn: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="颁发者通用名称（Issuer Common Name）",
    )
    issuer_org: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="颁发者组织名称",
    )

    # 有效期属性
    valid_from: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="生效时间戳（Unix秒）",
    )
    valid_to: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="过期时间戳（Unix秒）",
    )
    days_to_expire: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="剩余有效天数（可为负数表示已过期）",
    )

    # 风险评估属性
    is_expired: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否已过期",
    )
    is_self_signed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否为自签名证书",
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否已被吊销",
    )

    # 统计属性
    san_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="SAN（主题备用名称）数量",
    )

    # 范围控制
    scope_policy: Mapped[str] = mapped_column(
        String(50),
        default="IN_SCOPE",
        nullable=False,
        index=True,
        comment="范围策略（IN_SCOPE/OUT_OF_SCOPE）",
    )

    # 元数据（使用 metadata_ 避免与 SQLAlchemy 的 metadata 属性冲突）
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
        comment="元数据（JSONB格式，包含subject_alt_names、fingerprints等）",
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
            "san_count >= 0",
            name="chk_cert_san_count",
        ),
        CheckConstraint(
            "valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to",
            name="chk_cert_valid_range",
        ),
        {"comment": "证书资产表"},
    )

    def __repr__(self) -> str:
        """返回对象的字符串表示。"""
        return f"<Certificate(id={self.id}, subject_cn={self.subject_cn}, expired={self.is_expired})>"
