"""
Credential资产的Pydantic Schema。

用于API请求/响应的数据验证与序列化。
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CredentialCreate(BaseModel):
    """创建凭证资产的请求模型。"""

    external_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="业务唯一标识（可选，不填自动生成，建议使用 cred:TYPE:HASH）",
        examples=["cred:PASSWORD:sha256:abcd1234..."],
    )
    cred_type: str = Field(
        ...,
        max_length=50,
        description="凭证类型（PASSWORD/API_KEY/TOKEN/SSH_KEY/CERTIFICATE/COOKIE/SESSION等）",
        examples=["PASSWORD"],
    )
    provider: str | None = Field(
        None,
        max_length=255,
        description="提供方/来源（如 GitHub、AWS、Google）",
        examples=["GitHub"],
    )
    username: str | None = Field(
        None,
        max_length=255,
        description="用户名",
        examples=["user@example.com"],
    )
    email: str | None = Field(
        None,
        max_length=255,
        description="电子邮箱",
        examples=["user@example.com"],
    )
    phone: str | None = Field(
        None,
        max_length=50,
        description="电话号码",
        examples=["+86-13800138000"],
    )
    leaked_count: int = Field(
        default=0,
        ge=0,
        description="泄露次数",
    )
    content: dict[str, Any] = Field(
        default_factory=dict,
        description="凭证内容（敏感信息，如password_hash、api_key等）",
        examples=[
            {
                "password_hash": "sha256:abcd1234...",
                "salt": "xyz789...",
            }
        ],
    )
    validation_result: str | None = Field(
        None,
        max_length=50,
        description="验证结果（VALID/INVALID/UNKNOWN）",
        examples=["VALID"],
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
        description="元数据（包含source、breach_date、breach_name等）",
        examples=[
            {
                "source": "Collection #1",
                "breach_date": "2019-01-17",
                "breach_name": "Collection #1",
            }
        ],
    )
    created_by: str | None = Field(
        None,
        max_length=100,
        description="创建者标识",
        examples=["monitor"],
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "external_id": "cred:PASSWORD:sha256:abcd1234",
                "cred_type": "PASSWORD",
                "provider": "GitHub",
                "username": "user@example.com",
                "email": "user@example.com",
                "leaked_count": 1,
                "content": {
                    "password_hash": "sha256:abcd1234...",
                },
                "validation_result": "VALID",
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "source": "Collection #1",
                    "breach_date": "2019-01-17",
                },
                "created_by": "monitor",
            }
        },
    )

    @field_validator("cred_type")
    @classmethod
    def validate_cred_type(cls, v: str) -> str:
        """验证凭证类型的有效性。"""
        allowed = {
            "PASSWORD",
            "API_KEY",
            "TOKEN",
            "SSH_KEY",
            "CERTIFICATE",
            "COOKIE",
            "SESSION",
            "DATABASE",
            "AWS_KEY",
            "AZURE_KEY",
            "GCP_KEY",
            "OTHER",
        }
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"cred_type必须是 {allowed} 之一")
        return value

    @field_validator("validation_result")
    @classmethod
    def validate_validation_result(cls, v: str | None) -> str | None:
        """验证验证结果的有效性。"""
        if v is None:
            return None
        allowed = {"VALID", "INVALID", "UNKNOWN"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"validation_result必须是 {allowed} 之一")
        return value

    @field_validator("scope_policy")
    @classmethod
    def validate_scope_policy(cls, v: str) -> str:
        """验证范围策略的有效性。"""
        allowed = {"IN_SCOPE", "OUT_OF_SCOPE"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"scope_policy必须是 {allowed} 之一")
        return value


class CredentialUpdate(BaseModel):
    """更新凭证资产的请求模型。"""

    cred_type: str | None = Field(
        None,
        max_length=50,
        description="凭证类型",
    )
    provider: str | None = Field(
        None,
        max_length=255,
        description="提供方/来源",
    )
    username: str | None = Field(
        None,
        max_length=255,
        description="用户名",
    )
    email: str | None = Field(
        None,
        max_length=255,
        description="电子邮箱",
    )
    phone: str | None = Field(
        None,
        max_length=50,
        description="电话号码",
    )
    leaked_count: int | None = Field(
        None,
        ge=0,
        description="泄露次数",
    )
    content: dict[str, Any] | None = Field(
        None,
        description="凭证内容",
    )
    validation_result: str | None = Field(
        None,
        max_length=50,
        description="验证结果",
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
                "validation_result": "INVALID",
                "leaked_count": 2,
                "metadata": {
                    "last_validation": "2024-01-15T10:00:00Z",
                },
            }
        },
    )

    @field_validator("cred_type")
    @classmethod
    def validate_cred_type(cls, v: str | None) -> str | None:
        """验证凭证类型的有效性。"""
        if v is None:
            return None
        allowed = {
            "PASSWORD",
            "API_KEY",
            "TOKEN",
            "SSH_KEY",
            "CERTIFICATE",
            "COOKIE",
            "SESSION",
            "DATABASE",
            "AWS_KEY",
            "AZURE_KEY",
            "GCP_KEY",
            "OTHER",
        }
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"cred_type必须是 {allowed} 之一")
        return value

    @field_validator("validation_result")
    @classmethod
    def validate_validation_result(cls, v: str | None) -> str | None:
        """验证验证结果的有效性。"""
        if v is None:
            return None
        allowed = {"VALID", "INVALID", "UNKNOWN"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"validation_result必须是 {allowed} 之一")
        return value

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


class CredentialRead(BaseModel):
    """凭证资产的响应模型。"""

    id: UUID = Field(..., description="UUID主键")
    external_id: str = Field(..., description="业务唯一标识")
    cred_type: str = Field(..., description="凭证类型")
    provider: str | None = Field(None, description="提供方/来源")
    username: str | None = Field(None, description="用户名")
    email: str | None = Field(None, description="电子邮箱")
    phone: str | None = Field(None, description="电话号码")
    leaked_count: int = Field(..., description="泄露次数")
    content: dict[str, Any] = Field(..., description="凭证内容")
    validation_result: str | None = Field(None, description="验证结果")
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
                "external_id": "cred:PASSWORD:sha256:abcd1234",
                "cred_type": "PASSWORD",
                "provider": "GitHub",
                "username": "user@example.com",
                "email": "user@example.com",
                "phone": None,
                "leaked_count": 1,
                "content": {
                    "password_hash": "sha256:abcd1234...",
                },
                "validation_result": "VALID",
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "source": "Collection #1",
                    "breach_date": "2019-01-17",
                },
                "is_deleted": False,
                "deleted_at": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "monitor",
            }
        },
    )
