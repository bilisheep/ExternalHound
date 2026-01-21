"""
Netblock Schema定义。

定义网段资产的Pydantic模型，用于API请求和响应的数据验证与序列化。
"""

import ipaddress
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, IPvAnyNetwork

from app.schemas.common import AssetReadBase


class NetblockCreate(BaseModel):
    """
    创建网段的请求模型。

    Attributes:
        external_id: 业务唯一标识
        cidr: 网段CIDR表示
        asn_number: AS自治系统号（可选）
        live_count: 存活IP数量（默认0）
        risk_score: 风险评分（默认0.0）
        is_internal: 是否为内网段（可选，未指定时自动判断）
        scope_policy: 范围策略（默认IN_SCOPE）
        metadata_: 元数据字典
        created_by: 创建者标识（可选）
    """

    external_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="业务唯一标识（可选，不填自动生成）",
        examples=["cidr:47.100.0.0/16"],
    )
    cidr: str = Field(
        ...,
        description="网段CIDR表示",
        examples=["47.100.0.0/16", "192.168.1.0/24"],
    )
    asn_number: str | None = Field(
        None,
        max_length=20,
        description="AS自治系统号",
        examples=["AS37963", "AS13335"],
    )
    live_count: int = Field(
        default=0,
        ge=0,
        description="存活IP数量",
    )
    risk_score: Decimal = Field(
        default=Decimal("0.0"),
        ge=Decimal("0.0"),
        le=Decimal("10.0"),
        description="风险评分（0.0-10.0）",
    )
    is_internal: bool | None = Field(
        None,
        description="是否为内网段（未指定时根据RFC1918自动判断）",
    )
    scope_policy: str = Field(
        default="IN_SCOPE",
        description="范围策略",
        examples=["IN_SCOPE", "OUT_OF_SCOPE"],
    )
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（JSONB格式）",
        alias="metadata",
    )
    created_by: str | None = Field(
        None,
        max_length=100,
        description="创建者标识",
    )

    @field_validator("cidr")
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        """
        验证CIDR格式并规范化。

        Args:
            v: CIDR字符串

        Returns:
            规范化后的CIDR字符串

        Raises:
            ValueError: CIDR格式无效时
        """
        try:
            network = ipaddress.ip_network(v, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR format: {e}") from e
        return str(network)

    @field_validator("asn_number")
    @classmethod
    def normalize_asn(cls, v: str | None) -> str | None:
        """
        标准化AS号格式（统一大写并去除空格）。

        Args:
            v: AS号字符串

        Returns:
            标准化后的AS号，或None
        """
        if v is None:
            return None
        value = v.strip().upper()
        return value if value else None

    @field_validator("scope_policy")
    @classmethod
    def validate_scope_policy(cls, v: str) -> str:
        """
        验证范围策略的有效性。

        Args:
            v: 范围策略字符串

        Returns:
            验证通过的范围策略

        Raises:
            ValueError: 范围策略无效时
        """
        allowed = {"IN_SCOPE", "OUT_OF_SCOPE"}
        if v not in allowed:
            raise ValueError(f"scope_policy must be one of {allowed}")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "external_id": "cidr:47.100.0.0/16",
                "cidr": "47.100.0.0/16",
                "asn_number": "AS37963",
                "live_count": 128,
                "risk_score": 7.5,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "net_name": "ALIBABA-CN-NET",
                    "description": "Alibaba (China) Technology Co., Ltd.",
                    "abuse_contact": "abuse@aliyun.com",
                },
                "created_by": "admin",
            },
        },
    )


class NetblockUpdate(BaseModel):
    """
    更新网段的请求模型。

    所有字段都是可选的，只更新提供的字段。

    Attributes:
        asn_number: AS自治系统号
        live_count: 存活IP数量
        risk_score: 风险评分
        is_internal: 是否为内网段
        scope_policy: 范围策略
        metadata_: 元数据字典
    """

    asn_number: str | None = Field(
        None,
        max_length=20,
        description="AS自治系统号",
    )
    live_count: int | None = Field(
        None,
        ge=0,
        description="存活IP数量",
    )
    risk_score: Decimal | None = Field(
        None,
        ge=Decimal("0.0"),
        le=Decimal("10.0"),
        description="风险评分",
    )
    is_internal: bool | None = Field(
        None,
        description="是否为内网段",
    )
    scope_policy: str | None = Field(
        None,
        description="范围策略",
    )
    metadata_: dict[str, Any] | None = Field(
        None,
        description="元数据",
        alias="metadata",
    )

    @field_validator("asn_number")
    @classmethod
    def normalize_asn(cls, v: str | None) -> str | None:
        """标准化AS号格式。"""
        if v is None:
            return None
        value = v.strip().upper()
        return value if value else None

    @field_validator("scope_policy")
    @classmethod
    def validate_scope_policy(cls, v: str | None) -> str | None:
        """验证范围策略的有效性。"""
        if v is not None:
            allowed = {"IN_SCOPE", "OUT_OF_SCOPE"}
            if v not in allowed:
                raise ValueError(f"scope_policy must be one of {allowed}")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "live_count": 256,
                "risk_score": 8.0,
                "metadata": {
                    "tags": ["Production", "Cloud"],
                },
            },
        },
    )


class NetblockRead(AssetReadBase):
    """
    网段的响应模型。

    继承AssetReadBase，包含所有基础字段和网段特有字段。

    Attributes:
        cidr: 网段CIDR表示
        asn_number: AS自治系统号
        capacity: 网段容量
        live_count: 存活IP数量
        risk_score: 风险评分
        is_internal: 是否为内网段
        scope_policy: 范围策略
        metadata_: 元数据字典
    """

    cidr: IPvAnyNetwork = Field(..., description="网段CIDR表示")
    asn_number: str | None = Field(None, description="AS自治系统号")
    capacity: int | None = Field(None, description="网段容量（IP地址总数）")
    live_count: int = Field(..., description="存活IP数量")
    risk_score: Decimal = Field(..., description="风险评分（0.0-10.0）")
    is_internal: bool = Field(..., description="是否为内网段")
    scope_policy: str = Field(..., description="范围策略")
    metadata_: dict[str, Any] = Field(
        ...,
        description="元数据",
        serialization_alias="metadata"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "external_id": "cidr:47.100.0.0/16",
                "cidr": "47.100.0.0/16",
                "asn_number": "AS37963",
                "capacity": 65536,
                "live_count": 128,
                "risk_score": 7.5,
                "is_internal": False,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "net_name": "ALIBABA-CN-NET",
                    "description": "Alibaba (China) Technology Co., Ltd.",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin",
                "is_deleted": False,
                "deleted_at": None,
            },
        },
    )
