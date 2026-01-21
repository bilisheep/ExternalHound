"""
Organization Schema定义

定义组织资产的Pydantic模型，用于API请求和响应的数据验证。
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.common import AssetReadBase


class OrganizationCreate(BaseModel):
    """
    创建组织的请求模型

    Attributes:
        external_id: 业务唯一标识（与Neo4j节点id对齐）
        name: 简短名称
        full_name: 完整注册名称（可选）
        credit_code: 统一社会信用代码（可选）
        is_primary: 是否为一级目标
        tier: 层级
        scope_policy: 范围策略
        metadata: 元数据
        created_by: 创建者（可选）
    """

    external_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="业务唯一标识（可选，不填自动生成）",
        examples=["org:91110000XXXXXX"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="简短名称",
        examples=["某某科技集团"]
    )
    full_name: str | None = Field(
        None,
        max_length=500,
        description="完整注册名称",
        examples=["某某科技集团有限公司"]
    )
    credit_code: str | None = Field(
        None,
        max_length=100,
        description="统一社会信用代码",
        examples=["91110000XXXXXX"]
    )
    is_primary: bool = Field(
        default=False,
        description="是否为一级目标"
    )
    tier: int = Field(
        default=0,
        ge=0,
        description="层级：0=总部, 1=子公司"
    )
    scope_policy: str = Field(
        default="IN_SCOPE",
        description="范围策略",
        examples=["IN_SCOPE", "OUT_OF_SCOPE"]
    )
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（JSONB）",
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
                "external_id": "org:91110000XXXXXX",
                "name": "某某科技集团",
                "full_name": "某某科技集团有限公司",
                "credit_code": "91110000XXXXXX",
                "is_primary": True,
                "tier": 0,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "english_name": "MoMo Tech Group Co., Ltd.",
                    "industries": ["Internet", "Finance"],
                    "headquarters": "Beijing, China"
                },
                "created_by": "admin"
            }
        }
    )


class OrganizationUpdate(BaseModel):
    """
    更新组织的请求模型

    所有字段都是可选的，只更新提供的字段。
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="简短名称"
    )
    full_name: str | None = Field(
        None,
        max_length=500,
        description="完整注册名称"
    )
    credit_code: str | None = Field(
        None,
        max_length=100,
        description="统一社会信用代码"
    )
    is_primary: bool | None = Field(
        None,
        description="是否为一级目标"
    )
    tier: int | None = Field(
        None,
        ge=0,
        description="层级"
    )
    asset_count: int | None = Field(
        None,
        ge=0,
        description="资产总数"
    )
    risk_score: Decimal | None = Field(
        None,
        ge=Decimal("0.0"),
        le=Decimal("10.0"),
        description="风险评分"
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
                "name": "某某科技集团（更新）",
                "risk_score": 8.5,
                "metadata": {
                    "notes": "该目标将于Q4进行红队演练"
                }
            }
        }
    )


class OrganizationRead(AssetReadBase):
    """
    组织的响应模型

    继承AssetReadBase，包含所有基础字段。
    """

    name: str = Field(..., description="简短名称")
    full_name: str | None = Field(None, description="完整注册名称")
    credit_code: str | None = Field(None, description="统一社会信用代码")
    is_primary: bool = Field(..., description="是否为一级目标")
    tier: int = Field(..., description="层级")
    asset_count: int = Field(..., description="资产总数")
    risk_score: Decimal = Field(..., description="风险评分")
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
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "external_id": "org:91110000XXXXXX",
                "name": "某某科技集团",
                "full_name": "某某科技集团有限公司",
                "credit_code": "91110000XXXXXX",
                "is_primary": True,
                "tier": 0,
                "asset_count": 15420,
                "risk_score": 9.5,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "english_name": "MoMo Tech Group Co., Ltd.",
                    "industries": ["Internet", "Finance"]
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin",
                "is_deleted": False,
                "deleted_at": None
            }
        }
    )
