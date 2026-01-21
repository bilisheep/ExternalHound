"""
IP API路由

提供IP资产的RESTful API端点。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.postgres import get_db
from app.schemas.assets.ip import (
    IPCreate,
    IPUpdate,
    IPRead
)
from app.schemas.common import SuccessResponse
from app.services.assets.ip import IPService


router = APIRouter(prefix="/ips", tags=["IPs"])


@router.post(
    "",
    response_model=IPRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建IP"
)
async def create_ip(
    data: IPCreate,
    db: AsyncSession = Depends(get_db)
) -> IPRead:
    """
    创建新的IP资产。

    - **external_id**: 业务唯一标识（可选，不填自动生成）
    - **address**: IP地址（必填）
    - **version**: IP版本（可选，会自动检测）
    - **is_cloud**: 是否为云主机（默认False）
    - **is_internal**: 是否为内网IP（默认False）
    - **is_cdn**: 是否为CDN节点（默认False）
    - **country_code**: 国家代码（可选）
    - **asn_number**: AS号（可选）
    - **scope_policy**: 范围策略（默认IN_SCOPE）
    - **metadata**: 元数据（可选）
    - **created_by**: 创建者（可选）
    """
    service = IPService(db)
    ip = await service.create_ip(data)
    await db.commit()
    return IPRead.model_validate(ip)


@router.get(
    "/{id}",
    response_model=IPRead,
    summary="获取IP详情"
)
async def get_ip(
    id: UUID,
    db: AsyncSession = Depends(get_db)
) -> IPRead:
    """
    根据UUID获取IP详情。
    """
    service = IPService(db)
    ip = await service.get_ip(id)
    return IPRead.model_validate(ip)


@router.get(
    "/external/{external_id}",
    response_model=IPRead,
    summary="根据业务ID获取IP"
)
async def get_ip_by_external_id(
    external_id: str,
    db: AsyncSession = Depends(get_db)
) -> IPRead:
    """
    根据业务唯一标识获取IP详情。
    """
    service = IPService(db)
    ip = await service.get_ip_by_external_id(external_id)
    return IPRead.model_validate(ip)


@router.get(
    "/address/{address}",
    response_model=IPRead,
    summary="根据IP地址获取记录"
)
async def get_ip_by_address(
    address: str,
    db: AsyncSession = Depends(get_db)
) -> IPRead:
    """
    根据IP地址获取记录。
    """
    service = IPService(db)
    ip = await service.get_ip_by_address(address)
    return IPRead.model_validate(ip)


@router.get(
    "",
    response_model=Page[IPRead],
    summary="分页查询IP"
)
async def list_ips(
    page: int = 1,
    page_size: int = 20,
    version: int | None = None,
    is_cloud: bool | None = None,
    is_internal: bool | None = None,
    is_cdn: bool | None = None,
    country_code: str | None = None,
    scope_policy: str | None = None,
    db: AsyncSession = Depends(get_db)
) -> Page[IPRead]:
    """
    分页查询IP列表，支持过滤条件。

    - **page**: 页码（默认1）
    - **page_size**: 每页记录数（默认20）
    - **version**: IP版本（可选）
    - **is_cloud**: 是否为云主机（可选）
    - **is_internal**: 是否为内网IP（可选）
    - **is_cdn**: 是否为CDN节点（可选）
    - **country_code**: 国家代码（可选）
    - **scope_policy**: 范围策略（可选）
    """
    service = IPService(db)
    filters = {}
    if version is not None:
        filters["version"] = version
    if is_cloud is not None:
        filters["is_cloud"] = is_cloud
    if is_internal is not None:
        filters["is_internal"] = is_internal
    if is_cdn is not None:
        filters["is_cdn"] = is_cdn
    if country_code is not None:
        filters["country_code"] = country_code.upper()
    if scope_policy is not None:
        filters["scope_policy"] = scope_policy

    result = await service.paginate_ips(
        page=page,
        page_size=page_size,
        **filters
    )

    return Page(
        items=[IPRead.model_validate(ip) for ip in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages
    )


@router.put(
    "/{id}",
    response_model=IPRead,
    summary="更新IP"
)
async def update_ip(
    id: UUID,
    data: IPUpdate,
    db: AsyncSession = Depends(get_db)
) -> IPRead:
    """
    更新IP信息。只更新提供的字段。
    """
    service = IPService(db)
    ip = await service.update_ip(id, data)
    await db.commit()
    return IPRead.model_validate(ip)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除IP"
)
async def delete_ip(
    id: UUID,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    软删除IP（标记为已删除，不物理删除）。
    """
    service = IPService(db)
    await service.delete_ip(id)
    await db.commit()
    return SuccessResponse(message="IP deleted successfully")


@router.get(
    "/cloud/list",
    response_model=list[IPRead],
    summary="获取云主机IP"
)
async def get_cloud_ips(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[IPRead]:
    """
    获取所有云主机IP列表。

    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = IPService(db)
    ips = await service.get_cloud_ips(skip=skip, limit=limit)
    return [IPRead.model_validate(ip) for ip in ips]


@router.get(
    "/internal/list",
    response_model=list[IPRead],
    summary="获取内网IP"
)
async def get_internal_ips(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[IPRead]:
    """
    获取所有内网IP列表。

    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = IPService(db)
    ips = await service.get_internal_ips(skip=skip, limit=limit)
    return [IPRead.model_validate(ip) for ip in ips]


@router.get(
    "/high-risk/list",
    response_model=list[IPRead],
    summary="获取高风险IP"
)
async def get_high_risk_ips(
    min_risk_score: float = 7.0,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[IPRead]:
    """
    获取高风险IP列表。

    - **min_risk_score**: 最小风险分数阈值（默认7.0）
    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = IPService(db)
    ips = await service.get_high_risk_ips(
        min_risk_score=min_risk_score,
        skip=skip,
        limit=limit
    )
    return [IPRead.model_validate(ip) for ip in ips]


@router.get(
    "/country/{country_code}/list",
    response_model=list[IPRead],
    summary="根据国家获取IP"
)
async def get_ips_by_country(
    country_code: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[IPRead]:
    """
    根据国家代码获取IP列表。

    - **country_code**: 国家代码（ISO 3166-1 alpha-2）
    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = IPService(db)
    ips = await service.get_ips_by_country(
        country_code=country_code,
        skip=skip,
        limit=limit
    )
    return [IPRead.model_validate(ip) for ip in ips]
