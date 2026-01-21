"""
通用Schema定义

定义了跨模块使用的通用Pydantic模型。
"""

from typing import Generic, TypeVar
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """
    分页响应模型

    用于包装分页查询结果的通用容器。

    Attributes:
        items: 当前页的数据项列表
        total: 总记录数
        page: 当前页码（从1开始）
        page_size: 每页记录数
        total_pages: 总页数
    """

    items: list[T]
    total: int = Field(..., description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, description="每页记录数")
    total_pages: int = Field(..., ge=0, description="总页数")

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """
    分页参数模型

    用于接收和验证分页查询参数。

    Attributes:
        page: 页码，从1开始
        page_size: 每页记录数，默认20，最大100
    """

    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="每页记录数，最大100"
    )


class AssetReadBase(BaseModel):
    """
    资产读取响应基类

    所有资产类型的读取响应都应包含这些基础字段。

    Attributes:
        id: 资产UUID
        external_id: 业务唯一标识（与Neo4j节点id对齐）
        created_at: 创建时间
        updated_at: 更新时间
        created_by: 创建者
        is_deleted: 是否已删除（软删除标记）
        deleted_at: 删除时间
    """

    id: UUID = Field(..., description="资产UUID")
    external_id: str = Field(..., description="业务唯一标识")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: str | None = Field(None, description="创建者")
    is_deleted: bool = Field(False, description="是否已删除")
    deleted_at: datetime | None = Field(None, description="删除时间")

    model_config = ConfigDict(from_attributes=True)


class SuccessResponse(BaseModel):
    """
    成功响应模型

    用于返回简单的成功消息。

    Attributes:
        success: 是否成功
        message: 响应消息
    """

    success: bool = Field(True, description="是否成功")
    message: str = Field(..., description="响应消息")


class ErrorResponse(BaseModel):
    """
    错误响应模型

    用于返回错误信息。

    Attributes:
        error: 错误类型
        message: 错误消息
        details: 错误详情
    """

    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: dict | None = Field(None, description="错误详情")
