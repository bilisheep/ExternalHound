"""
Service（服务）ORM模型。

存储网络服务的核心属性与元数据，用于服务识别和安全评估。
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Service(Base):
    """
    服务资产模型。

    Attributes:
        id: UUID主键
        external_id: 业务唯一标识（建议使用 svc:IP:PORT:PROTOCOL）
        service_name: 服务名称（如 http、ssh、mysql）
        port: 端口号
        protocol: 协议类型（TCP/UDP）
        product: 产品名称（如 Apache、Nginx）
        version: 版本号
        banner: Banner信息
        is_http: 是否为HTTP/HTTPS服务
        risk_score: 风险评分（0-10）
        asset_category: 资产分类（WEB/DATABASE/MIDDLEWARE等）
        scope_policy: 范围策略
        metadata_: 元数据（JSONB格式）
        is_deleted: 软删除标记
        deleted_at: 删除时间戳
        created_at: 创建时间戳
        updated_at: 更新时间戳
        created_by: 创建者标识
    """

    __tablename__ = "assets_service"

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
        comment="业务唯一标识（建议使用 svc:IP:PORT:PROTOCOL）",
    )

    # 核心服务字段
    service_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="服务名称（如 http、ssh、mysql）",
    )
    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="端口号（1-65535）",
    )
    protocol: Mapped[str] = mapped_column(
        String(10),
        default="TCP",
        nullable=False,
        index=True,
        comment="协议类型（TCP/UDP）",
    )

    # 产品与版本信息
    product: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="产品名称（如 Apache、Nginx、MySQL）",
    )
    version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="版本号",
    )
    banner: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Banner信息",
    )

    # 服务特性
    is_http: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否为HTTP/HTTPS服务",
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="风险评分（0-10）",
    )

    # 资产分类
    asset_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="资产分类（WEB/DATABASE/MIDDLEWARE/CACHE/MESSAGE_QUEUE等）",
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
        comment="元数据（JSONB格式，包含cpe、scripts结果等）",
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
            "port >= 1 AND port <= 65535",
            name="chk_service_port",
        ),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 10",
            name="chk_service_risk_score",
        ),
        CheckConstraint(
            "protocol IN ('TCP', 'UDP')",
            name="chk_service_protocol",
        ),
        {"comment": "服务资产表"},
    )

    def __repr__(self) -> str:
        """返回对象的字符串表示。"""
        return f"<Service(id={self.id}, service_name={self.service_name}, port={self.port}, protocol={self.protocol})>"
