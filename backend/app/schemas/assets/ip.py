"""
IP Schema定义

定义IP资产的Pydantic模型，用于API请求和响应的数据验证。
"""

import ipaddress
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, field_validator, IPvAnyAddress

from app.schemas.common import AssetReadBase


class IPCreate(BaseModel):
    """
    创建IP的请求模型

    Attributes:
        external_id: 业务唯一标识
        address: IP地址
        version: IP版本（可选，会自动检测）
        is_cloud: 是否为云主机
        is_internal: 是否为内网IP
        is_cdn: 是否为CDN节点
        country_code: 国家代码
        asn_number: AS号
        scope_policy: 范围策略
        metadata: 元数据
        created_by: 创建者（可选）
    """

    external_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="业务唯一标识（可选，不填自动生成）",
        examples=["ip:47.100.1.15"]
    )
    address: str = Field(
        ...,
        description="IP地址",
        examples=["47.100.1.15", "2001:db8::1"]
    )
    version: int | None = Field(
        None,
        description="IP版本（4或6），不提供时自动检测"
    )
    is_cloud: bool = Field(
        default=False,
        description="是否为云主机"
    )
    is_internal: bool = Field(
        default=False,
        description="是否为内网IP"
    )
    is_cdn: bool = Field(
        default=False,
        description="是否为CDN节点"
    )
    country_code: str | None = Field(
        None,
        min_length=2,
        max_length=2,
        description="国家代码（ISO 3166-1 alpha-2）",
        examples=["CN", "US"]
    )
    asn_number: str | None = Field(
        None,
        max_length=20,
        description="AS号",
        examples=["AS37963"]
    )
    scope_policy: str = Field(
        default="IN_SCOPE",
        description="范围策略"
    )
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（OS指纹、地理位置等）",
        alias="metadata"
    )
    created_by: str | None = Field(
        None,
        max_length=100,
        description="创建者"
    )

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        """验证IP地址格式"""
        try:
            ipaddress.ip_address(v)
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {e}")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: int | None) -> int | None:
        """验证IP版本"""
        if v is not None and v not in (4, 6):
            raise ValueError("IP version must be 4 or 6")
        return v

    @field_validator("scope_policy")
    @classmethod
    def validate_scope_policy(cls, v: str) -> str:
        """验证范围策略"""
        allowed = {"IN_SCOPE", "OUT_OF_SCOPE"}
        if v not in allowed:
            raise ValueError(f"scope_policy must be one of {allowed}")
        return v

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str | None) -> str | None:
        """验证国家代码格式"""
        if v is not None:
            if len(v) != 2:
                raise ValueError("country_code must be 2 characters (ISO 3166-1 alpha-2)")
            return v.upper()
        return v

    def detect_version(self) -> int:
        """
        自动检测IP版本

        Returns:
            4或6
        """
        ip = ipaddress.ip_address(self.address)
        return ip.version

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "external_id": "ip:47.100.1.15",
                "address": "47.100.1.15",
                "version": 4,
                "is_cloud": True,
                "is_internal": False,
                "is_cdn": False,
                "country_code": "CN",
                "asn_number": "AS37963",
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "os_info": {
                        "name": "Ubuntu",
                        "version": "20.04 LTS"
                    },
                    "geo_location": {
                        "city": "Hangzhou",
                        "region": "Zhejiang"
                    }
                },
                "created_by": "admin"
            }
        }
    )


class IPUpdate(BaseModel):
    """
    更新IP的请求模型

    所有字段都是可选的，只更新提供的字段。
    """

    is_cloud: bool | None = Field(
        None,
        description="是否为云主机"
    )
    is_internal: bool | None = Field(
        None,
        description="是否为内网IP"
    )
    is_cdn: bool | None = Field(
        None,
        description="是否为CDN节点"
    )
    open_ports_count: int | None = Field(
        None,
        ge=0,
        description="开放端口总数"
    )
    risk_score: Decimal | None = Field(
        None,
        ge=Decimal("0.0"),
        le=Decimal("10.0"),
        description="聚合风险值"
    )
    vuln_critical_count: int | None = Field(
        None,
        ge=0,
        description="严重漏洞数量"
    )
    country_code: str | None = Field(
        None,
        min_length=2,
        max_length=2,
        description="国家代码"
    )
    asn_number: str | None = Field(
        None,
        max_length=20,
        description="AS号"
    )
    scope_policy: str | None = Field(
        None,
        description="范围策略"
    )
    metadata_: dict[str, Any] | None = Field(
        None,
        description="元数据",
        alias="metadata"
    )

    @field_validator("scope_policy")
    @classmethod
    def validate_scope_policy(cls, v: str | None) -> str | None:
        """验证范围策略"""
        if v is not None:
            allowed = {"IN_SCOPE", "OUT_OF_SCOPE"}
            if v not in allowed:
                raise ValueError(f"scope_policy must be one of {allowed}")
        return v

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str | None) -> str | None:
        """验证国家代码格式"""
        if v is not None:
            if len(v) != 2:
                raise ValueError("country_code must be 2 characters")
            return v.upper()
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "is_cloud": True,
                "open_ports_count": 12,
                "risk_score": 8.5,
                "metadata": {
                    "cloud_metadata": {
                        "provider": "Aliyun",
                        "region_id": "cn-hangzhou"
                    }
                }
            }
        }
    )


class IPRead(AssetReadBase):
    """
    IP的响应模型

    继承AssetReadBase，包含所有基础字段。
    """

    address: IPvAnyAddress = Field(..., description="IP地址")
    version: int = Field(..., description="IP版本")
    is_cloud: bool = Field(..., description="是否为云主机")
    is_internal: bool = Field(..., description="是否为内网IP")
    is_cdn: bool = Field(..., description="是否为CDN节点")
    open_ports_count: int = Field(..., description="开放端口总数")
    risk_score: Decimal = Field(..., description="聚合风险值")
    vuln_critical_count: int = Field(..., description="严重漏洞数量")
    country_code: str | None = Field(None, description="国家代码")
    asn_number: str | None = Field(None, description="AS号")
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
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "external_id": "ip:47.100.1.15",
                "address": "47.100.1.15",
                "version": 4,
                "is_cloud": True,
                "is_internal": False,
                "is_cdn": False,
                "open_ports_count": 12,
                "risk_score": 8.5,
                "vuln_critical_count": 1,
                "country_code": "CN",
                "asn_number": "AS37963",
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "os_info": {
                        "name": "Ubuntu",
                        "version": "20.04 LTS"
                    }
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin",
                "is_deleted": False,
                "deleted_at": None
            }
        }
    )
