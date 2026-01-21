"""
Service资产的Pydantic Schema。

用于API请求/响应的数据验证与序列化。
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceCreate(BaseModel):
    """创建服务资产的请求模型。"""

    external_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="业务唯一标识（可选，不填自动生成，建议使用 svc:IP:PORT:PROTOCOL）",
        examples=["svc:192.168.1.1:80:TCP"],
    )
    service_name: str | None = Field(
        None,
        max_length=100,
        description="服务名称（如 http、ssh、mysql）",
        examples=["http"],
    )
    port: int = Field(
        ...,
        ge=1,
        le=65535,
        description="端口号",
        examples=[80],
    )
    protocol: str = Field(
        default="TCP",
        max_length=10,
        description="协议类型（TCP/UDP）",
        examples=["TCP"],
    )
    product: str | None = Field(
        None,
        max_length=255,
        description="产品名称（如 Apache、Nginx、MySQL）",
        examples=["Nginx"],
    )
    version: str | None = Field(
        None,
        max_length=100,
        description="版本号",
        examples=["1.21.0"],
    )
    banner: str | None = Field(
        None,
        description="Banner信息",
        examples=["HTTP/1.1 200 OK\\r\\nServer: nginx/1.21.0"],
    )
    is_http: bool = Field(
        default=False,
        description="是否为HTTP/HTTPS服务",
    )
    risk_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="风险评分（0-10）",
    )
    asset_category: str | None = Field(
        None,
        max_length=50,
        description="资产分类（WEB/DATABASE/MIDDLEWARE/CACHE/MESSAGE_QUEUE等）",
        examples=["WEB"],
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
        description="元数据（包含cpe、scripts结果等）",
        examples=[
            {
                "cpe": ["cpe:/a:nginx:nginx:1.21.0"],
                "scripts": {"http-title": "Welcome to nginx!"},
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
                "external_id": "svc:192.168.1.1:80:TCP",
                "service_name": "http",
                "port": 80,
                "protocol": "TCP",
                "product": "Nginx",
                "version": "1.21.0",
                "is_http": True,
                "risk_score": 3.5,
                "asset_category": "WEB",
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "cpe": ["cpe:/a:nginx:nginx:1.21.0"],
                },
                "created_by": "scanner",
            }
        },
    )

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        """验证协议类型的有效性。"""
        allowed = {"TCP", "UDP"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"protocol必须是 {allowed} 之一")
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

    @field_validator("service_name")
    @classmethod
    def normalize_service_name(cls, v: str | None) -> str | None:
        """标准化服务名称（统一小写）。"""
        if v is None:
            return None
        value = v.strip().lower()
        return value if value else None


class ServiceUpdate(BaseModel):
    """更新服务资产的请求模型。"""

    service_name: str | None = Field(
        None,
        max_length=100,
        description="服务名称",
    )
    port: int | None = Field(
        None,
        ge=1,
        le=65535,
        description="端口号",
    )
    protocol: str | None = Field(
        None,
        max_length=10,
        description="协议类型",
    )
    product: str | None = Field(
        None,
        max_length=255,
        description="产品名称",
    )
    version: str | None = Field(
        None,
        max_length=100,
        description="版本号",
    )
    banner: str | None = Field(
        None,
        description="Banner信息",
    )
    is_http: bool | None = Field(
        None,
        description="是否为HTTP/HTTPS服务",
    )
    risk_score: float | None = Field(
        None,
        ge=0.0,
        le=10.0,
        description="风险评分",
    )
    asset_category: str | None = Field(
        None,
        max_length=50,
        description="资产分类",
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
                "version": "1.22.0",
                "risk_score": 4.0,
                "metadata": {
                    "cve": ["CVE-2021-23017"],
                },
            }
        },
    )

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str | None) -> str | None:
        """验证协议类型的有效性。"""
        if v is None:
            return None
        allowed = {"TCP", "UDP"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError(f"protocol必须是 {allowed} 之一")
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

    @field_validator("service_name")
    @classmethod
    def normalize_service_name(cls, v: str | None) -> str | None:
        """标准化服务名称（统一小写）。"""
        if v is None:
            return None
        value = v.strip().lower()
        return value if value else None


class ServiceRead(BaseModel):
    """服务资产的响应模型。"""

    id: UUID = Field(..., description="UUID主键")
    external_id: str = Field(..., description="业务唯一标识")
    service_name: str | None = Field(None, description="服务名称")
    port: int = Field(..., description="端口号")
    protocol: str = Field(..., description="协议类型")
    product: str | None = Field(None, description="产品名称")
    version: str | None = Field(None, description="版本号")
    banner: str | None = Field(None, description="Banner信息")
    is_http: bool = Field(..., description="是否为HTTP/HTTPS服务")
    risk_score: float = Field(..., description="风险评分")
    asset_category: str | None = Field(None, description="资产分类")
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
                "external_id": "svc:192.168.1.1:80:TCP",
                "service_name": "http",
                "port": 80,
                "protocol": "TCP",
                "product": "Nginx",
                "version": "1.21.0",
                "banner": "HTTP/1.1 200 OK\\r\\nServer: nginx/1.21.0",
                "is_http": True,
                "risk_score": 3.5,
                "asset_category": "WEB",
                "scope_policy": "IN_SCOPE",
                "metadata": {
                    "cpe": ["cpe:/a:nginx:nginx:1.21.0"],
                },
                "is_deleted": False,
                "deleted_at": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "scanner",
            }
        },
    )
