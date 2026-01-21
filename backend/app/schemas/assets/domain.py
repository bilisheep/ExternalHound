"""
Domain Schema定义

定义域名资产的Pydantic模型，用于API请求和响应的数据验证。
"""

from typing import Any

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.common import AssetReadBase


class DomainCreate(BaseModel):
    """
    创建域名的请求模型

    Attributes:
        external_id: 业务唯一标识
        name: 完整域名
        root_domain: 根域名（可选）
        tier: 层级深度
        is_resolved: 是否能解析
        is_wildcard: 是否为泛解析
        is_internal: 是否解析到内网
        has_waf: 是否有WAF
        scope_policy: 范围策略
        metadata: 元数据
        created_by: 创建者（可选）
    """

    external_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="业务唯一标识（可选，不填自动生成）",
        examples=["domain:api.target.com"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="完整域名",
        examples=["api.target.com"]
    )
    root_domain: str | None = Field(
        None,
        max_length=255,
        description="根域名",
        examples=["target.com"]
    )
    tier: int = Field(
        default=1,
        ge=1,
        description="层级深度"
    )
    is_resolved: bool = Field(
        default=False,
        description="是否能解析"
    )
    is_wildcard: bool = Field(
        default=False,
        description="是否为泛解析"
    )
    is_internal: bool = Field(
        default=False,
        description="是否解析到内网"
    )
    has_waf: bool = Field(
        default=False,
        description="是否有WAF"
    )
    scope_policy: str = Field(
        default="IN_SCOPE",
        description="范围策略"
    )
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（DNS记录、ICP备案等）",
        alias="metadata"
    )
    created_by: str | None = Field(
        None,
        max_length=100,
        description="创建者"
    )

    @field_validator("scope_policy")
    @classmethod
    def validate_scope_policy(cls, v: str) -> str:
        """验证范围策略"""
        allowed = {"IN_SCOPE", "OUT_OF_SCOPE"}
        if v not in allowed:
            raise ValueError(f"scope_policy must be one of {allowed}")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "external_id": "domain:api.target.com",
                "name": "api.target.com",
                "root_domain": "target.com",
                "tier": 2,
                "is_resolved": True,
                "is_wildcard": False,
                "is_internal": False,
                "has_waf": True,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "records": {
                        "A": ["1.2.3.4"],
                        "CNAME": ["aliyun-waf.com"]
                    },
                    "icp_license": "京ICP备xxxxx号-1"
                },
                "created_by": "admin"
            }
        }
    )


class DomainUpdate(BaseModel):
    """
    更新域名的请求模型

    所有字段都是可选的，只更新提供的字段。
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="完整域名"
    )
    root_domain: str | None = Field(
        None,
        max_length=255,
        description="根域名"
    )
    tier: int | None = Field(
        None,
        ge=1,
        description="层级深度"
    )
    is_resolved: bool | None = Field(
        None,
        description="是否能解析"
    )
    is_wildcard: bool | None = Field(
        None,
        description="是否为泛解析"
    )
    is_internal: bool | None = Field(
        None,
        description="是否解析到内网"
    )
    has_waf: bool | None = Field(
        None,
        description="是否有WAF"
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

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "is_resolved": True,
                "has_waf": True,
                "metadata": {
                    "page_title": "用户登录中心",
                    "http_status_code": 200
                }
            }
        }
    )


class DomainRead(AssetReadBase):
    """
    域名的响应模型

    继承AssetReadBase，包含所有基础字段。
    """

    name: str = Field(..., description="完整域名")
    root_domain: str | None = Field(None, description="根域名")
    tier: int = Field(..., description="层级深度")
    is_resolved: bool = Field(..., description="是否能解析")
    is_wildcard: bool = Field(..., description="是否为泛解析")
    is_internal: bool = Field(..., description="是否解析到内网")
    has_waf: bool = Field(..., description="是否有WAF")
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
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "external_id": "domain:api.target.com",
                "name": "api.target.com",
                "root_domain": "target.com",
                "tier": 2,
                "is_resolved": True,
                "is_wildcard": False,
                "is_internal": False,
                "has_waf": True,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "records": {
                        "A": ["1.2.3.4"]
                    },
                    "icp_license": "京ICP备xxxxx号-1"
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin",
                "is_deleted": False,
                "deleted_at": None
            }
        }
    )
