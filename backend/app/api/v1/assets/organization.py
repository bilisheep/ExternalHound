"""
Organization API路由

提供组织资产的RESTful API端点。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.neo4j import Neo4jManager, get_neo4j
from app.db.postgres import get_db
from app.schemas.assets.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationRead
)
from app.schemas.common import SuccessResponse
from app.services.assets.organization import OrganizationService


router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建组织"
)
async def create_organization(
    data: OrganizationCreate,
    db: AsyncSession = Depends(get_db)
) -> OrganizationRead:
    """
    创建新的组织资产。

    - **external_id**: 业务唯一标识（可选，不填自动生成）
    - **name**: 简短名称（必填）
    - **full_name**: 完整注册名称（可选）
    - **credit_code**: 统一社会信用代码（可选）
    - **is_primary**: 是否为一级目标（默认False）
    - **tier**: 层级（默认0）
    - **scope_policy**: 范围策略（默认IN_SCOPE）
    - **metadata**: 元数据（可选）
    - **created_by**: 创建者（可选）
    """
    service = OrganizationService(db)
    org = await service.create_organization(data)
    await db.commit()
    return OrganizationRead.model_validate(org)


@router.get(
    "/{id}",
    response_model=OrganizationRead,
    summary="获取组织详情"
)
async def get_organization(
    id: UUID,
    db: AsyncSession = Depends(get_db)
) -> OrganizationRead:
    """
    根据UUID获取组织详情。
    """
    service = OrganizationService(db)
    org = await service.get_organization(id)
    return OrganizationRead.model_validate(org)


@router.get(
    "/external/{external_id}",
    response_model=OrganizationRead,
    summary="根据业务ID获取组织"
)
async def get_organization_by_external_id(
    external_id: str,
    db: AsyncSession = Depends(get_db)
) -> OrganizationRead:
    """
    根据业务唯一标识获取组织详情。
    """
    service = OrganizationService(db)
    org = await service.get_organization_by_external_id(external_id)
    return OrganizationRead.model_validate(org)


@router.get(
    "",
    response_model=Page[OrganizationRead],
    summary="分页查询组织"
)
async def list_organizations(
    page: int = 1,
    page_size: int = 20,
    is_primary: bool | None = None,
    tier: int | None = None,
    scope_policy: str | None = None,
    db: AsyncSession = Depends(get_db)
) -> Page[OrganizationRead]:
    """
    分页查询组织列表，支持过滤条件。

    - **page**: 页码（默认1）
    - **page_size**: 每页记录数（默认20）
    - **is_primary**: 是否为一级目标（可选）
    - **tier**: 层级（可选）
    - **scope_policy**: 范围策略（可选）
    """
    service = OrganizationService(db)
    filters = {}
    if is_primary is not None:
        filters["is_primary"] = is_primary
    if tier is not None:
        filters["tier"] = tier
    if scope_policy is not None:
        filters["scope_policy"] = scope_policy

    result = await service.paginate_organizations(
        page=page,
        page_size=page_size,
        **filters
    )

    return Page(
        items=[OrganizationRead.model_validate(org) for org in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages
    )


@router.put(
    "/{id}",
    response_model=OrganizationRead,
    summary="更新组织"
)
async def update_organization(
    id: UUID,
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db)
) -> OrganizationRead:
    """
    更新组织信息。只更新提供的字段。
    """
    service = OrganizationService(db)
    org = await service.update_organization(id, data)
    await db.commit()
    return OrganizationRead.model_validate(org)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除组织"
)
async def delete_organization(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> SuccessResponse:
    """
    硬删除组织（物理删除）。
    """
    service = OrganizationService(db, neo4j)
    await service.delete_organization(id)
    await db.commit()
    return SuccessResponse(message="Organization deleted successfully")


@router.get(
    "/primary/list",
    response_model=list[OrganizationRead],
    summary="获取一级目标组织"
)
async def get_primary_organizations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[OrganizationRead]:
    """
    获取所有一级目标组织列表。

    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = OrganizationService(db)
    orgs = await service.get_primary_organizations(skip=skip, limit=limit)
    return [OrganizationRead.model_validate(org) for org in orgs]


@router.get(
    "/search/{name_pattern}",
    response_model=list[OrganizationRead],
    summary="搜索组织"
)
async def search_organizations(
    name_pattern: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[OrganizationRead]:
    """
    根据名称模糊搜索组织。

    - **name_pattern**: 名称搜索关键词
    - **skip**: 跳过的记录数（默认0）
    - **limit**: 返回的最大记录数（默认100）
    """
    service = OrganizationService(db)
    orgs = await service.search_organizations(
        name_pattern=name_pattern,
        skip=skip,
        limit=limit
    )
    return [OrganizationRead.model_validate(org) for org in orgs]
