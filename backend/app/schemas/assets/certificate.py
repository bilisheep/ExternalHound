"""
Certificate资产的Pydantic Schema。

用于API请求/响应的数据验证与序列化。
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CertificateCreate(BaseModel):
    """创建证书资产的请求模型。"""

    external_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="业务唯一标识（可选，不填自动生成，建议使用 cert:SHA256）",
        examples=["cert:sha256:abcd1234..."],
    )
    subject_cn: str | None = Field(
        None,
        max_length=255,
        description="主题通用名称（Subject Common Name）",
        examples=["*.example.com"],
    )
    issuer_cn: str | None = Field(
        None,
        max_length=255,
        description="颁发者通用名称（Issuer Common Name）",
        examples=["Let's Encrypt Authority X3"],
    )
    issuer_org: str | None = Field(
        None,
        max_length=255,
        description="颁发者组织名称",
        examples=["Let's Encrypt"],
    )
    valid_from: int | None = Field(
        None,
        ge=0,
        description="生效时间戳（Unix秒）",
        examples=[1704067200],
    )
    valid_to: int | None = Field(
        None,
        ge=0,
        description="过期时间戳（Unix秒）",
        examples=[1735689600],
    )
    days_to_expire: int | None = Field(
        None,
        description="剩余有效天数（可为负数表示已过期）",
        examples=[30],
    )
    is_expired: bool = Field(
        default=False,
        description="是否已过期",
    )
    is_self_signed: bool = Field(
        default=False,
        description="是否为自签名证书",
    )
    is_revoked: bool = Field(
        default=False,
        description="是否已被吊销",
    )
    san_count: int = Field(
        default=0,
        ge=0,
        description="SAN（主题备用名称）数量",
    )
    scope_policy: str = Field(
        default="IN_SCOPE",
        max_length=50,
        description="范围策略（IN_SCOPE/OUT_OF_SCOPE）",
        examples=["IN_SCOPE"],
    )
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        alias="metadata",
        description="元数据（包含subject_alt_names、fingerprints等）",
        examples=[
            {
                "subject_alt_names": ["example.com", "www.example.com"],
                "fingerprints": {
                    "sha256": "abcd1234...",
                    "sha1": "xyz789...",
                },
            }
        ],
    )
    created_by: str | None = Field(
        None,
        max_length=100,
        description="创建者标识",
        examples=["system"],
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "external_id": "cert:sha256:a1b2c3d4e5f6...",
                "subject_cn": "*.example.com",
                "issuer_cn": "Let's Encrypt Authority X3",
                "issuer_org": "Let's Encrypt",
                "valid_from": 1704067200,
                "valid_to": 1735689600,
                "is_self_signed": False,
                "san_count": 2,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "subject_alt_names": ["example.com", "www.example.com"],
                    "fingerprints": {
                        "sha256": "a1b2c3d4e5f6...",
                    },
                },
                "created_by": "scanner",
            }
        },
    )

    @field_validator("valid_from", "valid_to")
    @classmethod
    def validate_timestamp(cls, v: int | None) -> int | None:
        """验证Unix时间戳的合理性。"""
        if v is not None and v < 0:
            raise ValueError("时间戳不能为负数")
        return v

    @field_validator("scope_policy")
    @classmethod
    def validate_scope_policy(cls, v: str) -> str:
        """验证范围策略的有效性。"""
        allowed = {"IN_SCOPE", "OUT_OF_SCOPE"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"scope_policy必须是 {allowed} 之一")
        return value


class CertificateUpdate(BaseModel):
    """更新证书资产的请求模型。"""

    subject_cn: str | None = Field(
        None,
        max_length=255,
        description="主题通用名称",
    )
    issuer_cn: str | None = Field(
        None,
        max_length=255,
        description="颁发者通用名称",
    )
    issuer_org: str | None = Field(
        None,
        max_length=255,
        description="颁发者组织名称",
    )
    valid_from: int | None = Field(
        None,
        ge=0,
        description="生效时间戳（Unix秒）",
    )
    valid_to: int | None = Field(
        None,
        ge=0,
        description="过期时间戳（Unix秒）",
    )
    days_to_expire: int | None = Field(
        None,
        description="剩余有效天数",
    )
    is_expired: bool | None = Field(
        None,
        description="是否已过期",
    )
    is_self_signed: bool | None = Field(
        None,
        description="是否为自签名证书",
    )
    is_revoked: bool | None = Field(
        None,
        description="是否已被吊销",
    )
    san_count: int | None = Field(
        None,
        ge=0,
        description="SAN数量",
    )
    scope_policy: str | None = Field(
        None,
        max_length=50,
        description="范围策略",
    )
    metadata_: dict[str, Any] | None = Field(
        None,
        alias="metadata",
        description="元数据",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "is_revoked": True,
                "scope_policy": "OUT_OF_SCOPE",
                "metadata": {
                    "revocation_reason": "keyCompromise",
                    "revocation_date": "2024-01-15",
                },
            }
        },
    )

    @field_validator("valid_from", "valid_to")
    @classmethod
    def validate_timestamp(cls, v: int | None) -> int | None:
        """验证Unix时间戳的合理性。"""
        if v is not None and v < 0:
            raise ValueError("时间戳不能为负数")
        return v

    @field_validator("scope_policy")
    @classmethod
    def validate_scope_policy(cls, v: str | None) -> str | None:
        """验证范围策略的有效性。"""
        if v is None:
            return None
        allowed = {"IN_SCOPE", "OUT_OF_SCOPE"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"scope_policy必须是 {allowed} 之一")
        return value


class CertificateRead(BaseModel):
    """证书资产的响应模型。"""

    id: UUID = Field(..., description="UUID主键")
    external_id: str = Field(..., description="业务唯一标识")
    subject_cn: str | None = Field(None, description="主题通用名称")
    issuer_cn: str | None = Field(None, description="颁发者通用名称")
    issuer_org: str | None = Field(None, description="颁发者组织名称")
    valid_from: int | None = Field(None, description="生效时间戳（Unix秒）")
    valid_to: int | None = Field(None, description="过期时间戳（Unix秒）")
    days_to_expire: int | None = Field(None, description="剩余有效天数")
    is_expired: bool = Field(..., description="是否已过期")
    is_self_signed: bool = Field(..., description="是否为自签名证书")
    is_revoked: bool = Field(..., description="是否已被吊销")
    san_count: int = Field(..., description="SAN数量")
    scope_policy: str = Field(..., description="范围策略")
    metadata_: dict[str, Any] = Field(
        ...,
        description="元数据",
        serialization_alias="metadata",
    )
    is_deleted: bool = Field(..., description="软删除标记")
    deleted_at: datetime | None = Field(None, description="删除时间戳")
    created_at: datetime = Field(..., description="创建时间戳")
    updated_at: datetime = Field(..., description="更新时间戳")
    created_by: str | None = Field(None, description="创建者标识")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "external_id": "cert:sha256:a1b2c3d4e5f6...",
                "subject_cn": "*.example.com",
                "issuer_cn": "Let's Encrypt Authority X3",
                "issuer_org": "Let's Encrypt",
                "valid_from": 1704067200,
                "valid_to": 1735689600,
                "days_to_expire": 365,
                "is_expired": False,
                "is_self_signed": False,
                "is_revoked": False,
                "san_count": 2,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "subject_alt_names": ["example.com", "www.example.com"],
                    "fingerprints": {
                        "sha256": "a1b2c3d4e5f6...",
                    },
                },
                "is_deleted": False,
                "deleted_at": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "scanner",
            }
        },
    )
