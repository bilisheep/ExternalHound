"""
IP（主机）ORM模型

网络空间的物理锚点，外部扫描结果的状态载体。
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
    func
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base

if TYPE_CHECKING:
    pass


class IP(Base):
    """
    IP/主机实体

    网络空间的物理锚点，是外部扫描结果的状态载体。

    Attributes:
        id: UUID主键
        external_id: 业务唯一标识（与Neo4j节点id对齐）
        address: IP地址（使用PostgreSQL INET类型）
        version: IP版本（4或6）
        is_cloud: 是否为云主机
        is_internal: 是否为内网IP
        is_cdn: 是否为CDN节点
        open_ports_count: 开放端口总数
        risk_score: 聚合风险值
        vuln_critical_count: 严重漏洞数量
        country_code: 国家代码
        asn_number: AS号
        scope_policy: 范围策略
        metadata: 元数据（OS指纹、地理位置、云元数据等）
        is_deleted: 软删除标记
        deleted_at: 删除时间
        created_at: 创建时间
        updated_at: 更新时间
        created_by: 创建者
    """

    __tablename__ = "assets_ip"

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
    address: Mapped[str] = mapped_column(
        INET,
        unique=True,
        nullable=False,
        comment="IP地址"
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="IP版本（4或6）"
    )

    # 拓扑属性
    is_cloud: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否为云主机"
    )
    is_internal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为内网IP"
    )
    is_cdn: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为CDN节点"
    )

    # 聚合统计
    open_ports_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="开放端口总数"
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 1),
        default=Decimal("0.0"),
        nullable=False,
        comment="聚合风险值"
    )
    vuln_critical_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="严重漏洞数量"
    )

    # 地理/归属
    country_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        index=True,
        comment="国家代码"
    )
    asn_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="AS号"
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
        comment="元数据（OS指纹、地理位置、云元数据等）"
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
            "version IN (4, 6)",
            name="chk_ip_version"
        ),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 10",
            name="chk_ip_risk_score"
        ),
        CheckConstraint(
            "open_ports_count >= 0",
            name="chk_ip_open_ports_count"
        ),
        CheckConstraint(
            "vuln_critical_count >= 0",
            name="chk_ip_vuln_critical_count"
        ),
        {"comment": "IP/主机表"}
    )

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<IP(id={self.id}, address={self.address})>"
