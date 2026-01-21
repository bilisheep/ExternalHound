"""
ClientApplication资产的Pydantic Schema。

用于API请求/响应的数据验证与序列化。
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClientApplicationCreate(BaseModel):
    """创建客户端应用资产的请求模型。"""

    external_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="业务唯一标识（可选，不填自动生成，建议使用 app:PLATFORM:PACKAGE_NAME）",
        examples=["app:Android:com.example.app"],
    )
    app_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="应用名称",
        examples=["Example App"],
    )
    package_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="包名/应用标识符",
        examples=["com.example.app"],
    )
    version: str | None = Field(
        None,
        max_length=100,
        description="版本号",
        examples=["1.0.0"],
    )
    platform: str = Field(
        ...,
        max_length=50,
        description="平台类型（Android/iOS/Windows/macOS/Linux）",
        examples=["Android"],
    )
    bundle_id: str | None = Field(
        None,
        max_length=255,
        description="Bundle标识符（iOS专用）",
        examples=["com.example.app"],
    )
    risk_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="风险评分（0-10）",
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
        description="元数据（包含permissions、signatures等）",
        examples=[
            {
                "permissions": [
                    "android.permission.INTERNET",
                    "android.permission.CAMERA",
                ],
                "min_sdk_version": 21,
            }
        ],
    )
    created_by: str | None = Field(
        None,
        max_length=100,
        description="创建者标识",
        examples=["scanner"],
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "external_id": "app:Android:com.example.app",
                "app_name": "Example App",
                "package_name": "com.example.app",
                "version": "1.0.0",
                "platform": "Android",
                "risk_score": 3.5,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "permissions": [
                        "android.permission.INTERNET",
                        "android.permission.CAMERA",
                    ],
                },
                "created_by": "scanner",
            }
        },
    )

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """验证平台类型的有效性。"""
        allowed = {"Android", "iOS", "Windows", "macOS", "Linux"}
        # 首字母大写，其余小写（除了iOS和macOS的特殊大小写）
        value = v.strip()
        if value.lower() == "ios":
            value = "iOS"
        elif value.lower() == "macos":
            value = "macOS"
        else:
            value = value.capitalize()

        if value not in allowed:
            raise ValueError(f"platform必须是 {allowed} 之一")
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


class ClientApplicationUpdate(BaseModel):
    """更新客户端应用资产的请求模型。"""

    app_name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="应用名称",
    )
    package_name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="包名/应用标识符",
    )
    version: str | None = Field(
        None,
        max_length=100,
        description="版本号",
    )
    platform: str | None = Field(
        None,
        max_length=50,
        description="平台类型",
    )
    bundle_id: str | None = Field(
        None,
        max_length=255,
        description="Bundle标识符",
    )
    risk_score: float | None = Field(
        None,
        ge=0.0,
        le=10.0,
        description="风险评分",
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
                "version": "1.0.1",
                "risk_score": 4.0,
                "metadata": {
                    "vulnerabilities": ["CVE-2021-12345"],
                },
            }
        },
    )

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str | None) -> str | None:
        """验证平台类型的有效性。"""
        if v is None:
            return None
        allowed = {"Android", "iOS", "Windows", "macOS", "Linux"}
        value = v.strip()
        if value.lower() == "ios":
            value = "iOS"
        elif value.lower() == "macos":
            value = "macOS"
        else:
            value = value.capitalize()

        if value not in allowed:
            raise ValueError(f"platform必须是 {allowed} 之一")
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


class ClientApplicationRead(BaseModel):
    """客户端应用资产的响应模型。"""

    id: UUID = Field(..., description="UUID主键")
    external_id: str = Field(..., description="业务唯一标识")
    app_name: str = Field(..., description="应用名称")
    package_name: str = Field(..., description="包名/应用标识符")
    version: str | None = Field(None, description="版本号")
    platform: str = Field(..., description="平台类型")
    bundle_id: str | None = Field(None, description="Bundle标识符")
    risk_score: float = Field(..., description="风险评分")
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
                "external_id": "app:Android:com.example.app",
                "app_name": "Example App",
                "package_name": "com.example.app",
                "version": "1.0.0",
                "platform": "Android",
                "bundle_id": None,
                "risk_score": 3.5,
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "permissions": [
                        "android.permission.INTERNET",
                        "android.permission.CAMERA",
                    ],
                },
                "is_deleted": False,
                "deleted_at": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "scanner",
            }
        },
    )
