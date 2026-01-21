"""
Domain API路由

提供域名资产的RESTful API端点。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.postgres import get_db
from app.schemas.assets.domain import (
    DomainCreate,
    DomainUpdate,
    DomainRead
)
from app.schemas.common import SuccessResponse
from app.services.assets.domain import DomainService


router = APIRouter(prefix="/domains", tags=["Domains"])


@router.post(
    "",
    response_model=DomainRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建域名"
)
async def create_domain(
    data: DomainCreate,
    db: AsyncSession = Depends(get_db)
) -> DomainRead:
    """
    创建新的域名资产。

    - **external_id**: 业务唯一标识（可选，不填自动生成）
    - **name**: 完整域名（必填）
    - **root_domain**: 根域名（可选）
    - **tier**: 层级深度（默认1）
    - **is_resolved**: 是否能解析（默认False）
    - **is_wildcard**: 是否为泛解析（默认False）
    - **is_internal**: 是否解析到内网（默认False）
    - **has_waf**: 是否有WAF（默认False）
    - **scope_policy**: 范围策略（默认IN_SCOPE）
    - **metadata**: 元数据（可选）
    - **created_by**: 创建者（可选）
    """
    service = DomainService(db)
    domain = await service.create_domain(data)
    await db.commit()
    return DomainRead.model_validate(domain)


@router.get(
    "/{id}",
    response_model=DomainRead,
    summary="获取域名详情"
)
async def get_domain(
    id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DomainRead:
    """
    根据UUID获取域名详情。
    """
    service = DomainService(db)
    domain = await service.get_domain(id)
    return DomainRead.model_validate(domain)


@router.get(
    "/external/{external_id}",
    response_model=DomainRead,
    summary="根据业务ID获取域名"
)
async def get_domain_by_external_id(
    external_id: str,
    db: AsyncSession = Depends(get_db)
) -> DomainRead:
    """
    根据业务唯一标识获取域名详情。
    """
    service = DomainService(db)
    domain = await service.get_domain_by_external_id(external_id)
    return DomainRead.model_validate(domain)


@router.get(
    "/name/{name}",
    response_model=DomainRead,
    summary="根据域名获取记录"
)
async def get_domain_by_name(
    name: str,
    db: AsyncSession = Depends(get_db)
) -> DomainRead:
    """
    根据完整域名获取记录。
    """
    service = DomainService(db)
    domain = await service.get_domain_by_name(name)
    return DomainRead.model_validate(domain)


@router.get(
    "",
    response_model=Page[DomainRead],
    summary="分页查询域名"
)
async def list_domains(
    page: int = 1,
    page_size: int = 20,
    tier: int | None = None,
    is_resolved: bool | None = None,
    is_wildcard: bool | None = None,
    has_waf: bool | None = None,
    scope_policy: str | None = None,
    db: AsyncSession = Depends(get_db)
) -> Page[DomainRead]:
    """
    分页查询域名列表，支持过滤条件。

    - **page**: 页码（默认1）
    - **page_size**: 每页记录数（默认20）
    - **tier**: 层级深度（可选）
    - **is_resolved**: 是否能解析（可选）
    - **is_wildcard**: 是否为泛解析（可选）
    - **has_waf**: 是否有WAF（可选）
    - **scope_policy**: 范围策略（可选）
    """
    service = DomainService(db)
    filters = {}
    if tier is not None:
        filters["tier"] = tier
    if is_resolved is not None:
        filters["is_resolved"] = is_resolved
    if is_wildcard is not None:
        filters["is_wildcard"] = is_wildcard
    if has_waf is not None:
        filters["has_waf"] = has_waf
    if scope_policy is not None:
        filters["scope_policy"] = scope_policy

    result = await service.paginate_domains(
        page=page,
        page_size=page_size,
        **filters
    )

    return Page(
        items=[DomainRead.model_validate(domain) for domain in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages
    )


@router.put(
    "/{id}",
    response_model=DomainRead,
    summary="更新域名"
)
async def update_domain(
    id: UUID,
    data: DomainUpdate,
    db: AsyncSession = Depends(get_db)
) -> DomainRead:
    """
    更新域名信息。只更新提供的字段。
    """
    service = DomainService(db)
    domain = await service.update_domain(id, data)
    await db.commit()
    return DomainRead.model_validate(domain)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除域名"
)
async def delete_domain(
    id: UUID,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    软删除域名（标记为已删除，不物理删除）。
    """
    service = DomainService(db)
    await service.delete_domain(id)
    await db.commit()
    return SuccessResponse(message="Domain deleted successfully")


@router.get(
    "/root/{root_domain}/subdomains",
    response_model=list[DomainRead],
    summary="获取子域名列表"
)
async def get_subdomains(
    root_domain: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[DomainRead]:
    """
    获取指定根域名的所有子域名。

    - **root_domain**: 根域名
    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = DomainService(db)
    domains = await service.get_subdomains(
        root_domain=root_domain,
        skip=skip,
        limit=limit
    )
    return [DomainRead.model_validate(domain) for domain in domains]


@router.get(
    "/resolved/list",
    response_model=list[DomainRead],
    summary="获取已解析域名"
)
async def get_resolved_domains(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[DomainRead]:
    """
    获取所有已解析的域名列表。

    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = DomainService(db)
    domains = await service.get_resolved_domains(skip=skip, limit=limit)
    return [DomainRead.model_validate(domain) for domain in domains]


@router.get(
    "/wildcard/list",
    response_model=list[DomainRead],
    summary="获取泛解析域名"
)
async def get_wildcard_domains(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[DomainRead]:
    """
    获取所有泛解析域名列表。

    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = DomainService(db)
    domains = await service.get_wildcard_domains(skip=skip, limit=limit)
    return [DomainRead.model_validate(domain) for domain in domains]


@router.get(
    "/waf/list",
    response_model=list[DomainRead],
    summary="获取有WAF的域名"
)
async def get_domains_with_waf(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[DomainRead]:
    """
    获取所有有WAF的域名列表。

    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = DomainService(db)
    domains = await service.get_domains_with_waf(skip=skip, limit=limit)
    return [DomainRead.model_validate(domain) for domain in domains]
