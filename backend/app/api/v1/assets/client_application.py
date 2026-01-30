"""
ClientApplication API路由。

提供客户端应用资产的RESTful API端点，包括CRUD操作和应用特定查询。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.neo4j import Neo4jManager, get_neo4j
from app.db.postgres import get_db
from app.schemas.assets.client_application import (
    ClientApplicationCreate,
    ClientApplicationRead,
    ClientApplicationUpdate,
)
from app.schemas.common import SuccessResponse
from app.services.assets.client_application import ClientApplicationService

router = APIRouter(prefix="/client-applications", tags=["Client Applications"])


@router.post(
    "",
    response_model=ClientApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建客户端应用",
)
async def create_application(
    data: ClientApplicationCreate,
    db: AsyncSession = Depends(get_db),
) -> ClientApplicationRead:
    """
    创建新的客户端应用资产。

    - **external_id**: 业务唯一标识（可选，不填自动生成）
    - **app_name**: 应用名称（必填）
    - **package_name**: 包名/应用标识符（必填）
    - **version**: 版本号（可选）
    - **platform**: 平台类型（必填，Android/iOS/Windows/macOS/Linux）
    - **bundle_id**: Bundle标识符（可选，iOS专用）
    - **risk_score**: 风险评分（默认0.0）
    - **scope_policy**: 范围策略（默认IN_SCOPE）
    - **metadata**: 元数据（可选）
    - **created_by**: 创建者标识（可选）
    """
    service = ClientApplicationService(db)
    app = await service.create_application(data)
    await db.commit()
    return ClientApplicationRead.model_validate(app)


@router.get(
    "/{id}",
    response_model=ClientApplicationRead,
    summary="获取应用详情",
)
async def get_application(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ClientApplicationRead:
    """根据UUID获取客户端应用详情。"""
    service = ClientApplicationService(db)
    app = await service.get_application(id)
    return ClientApplicationRead.model_validate(app)


@router.get(
    "/external/{external_id}",
    response_model=ClientApplicationRead,
    summary="根据业务ID获取应用",
)
async def get_application_by_external_id(
    external_id: str,
    db: AsyncSession = Depends(get_db),
) -> ClientApplicationRead:
    """根据业务唯一标识获取客户端应用详情。"""
    service = ClientApplicationService(db)
    app = await service.get_application_by_external_id(external_id)
    return ClientApplicationRead.model_validate(app)


@router.get(
    "",
    response_model=Page[ClientApplicationRead],
    summary="分页查询应用",
)
async def list_applications(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    platform: str | None = Query(None, description="平台类型"),
    scope_policy: str | None = Query(None, description="范围策略"),
    db: AsyncSession = Depends(get_db),
) -> Page[ClientApplicationRead]:
    """
    分页查询客户端应用列表，支持过滤条件。

    - **page**: 页码（默认1）
    - **page_size**: 每页记录数（默认20）
    - **platform**: 平台类型（可选）
    - **scope_policy**: 范围策略（可选）
    """
    service = ClientApplicationService(db)
    filters = {}
    if platform is not None:
        filters["platform"] = platform
    if scope_policy is not None:
        filters["scope_policy"] = scope_policy

    result = await service.paginate_applications(
        page=page,
        page_size=page_size,
        **filters,
    )

    return Page(
        items=[ClientApplicationRead.model_validate(app) for app in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.put(
    "/{id}",
    response_model=ClientApplicationRead,
    summary="更新应用",
)
async def update_application(
    id: UUID,
    data: ClientApplicationUpdate,
    db: AsyncSession = Depends(get_db),
) -> ClientApplicationRead:
    """更新客户端应用信息。只更新提供的字段。"""
    service = ClientApplicationService(db)
    app = await service.update_application(id, data)
    await db.commit()
    return ClientApplicationRead.model_validate(app)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除应用",
)
async def delete_application(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> SuccessResponse:
    """硬删除客户端应用（物理删除）。"""
    service = ClientApplicationService(db, neo4j)
    await service.delete_application(id)
    await db.commit()
    return SuccessResponse(message="Client application deleted successfully")


@router.get(
    "/platform/{platform}/list",
    response_model=list[ClientApplicationRead],
    summary="根据平台类型获取应用列表",
)
async def get_applications_by_platform(
    platform: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ClientApplicationRead]:
    """根据平台类型获取客户端应用列表（Android/iOS/Windows/macOS/Linux）。"""
    service = ClientApplicationService(db)
    apps = await service.get_applications_by_platform(
        platform=platform,
        skip=skip,
        limit=limit,
    )
    return [ClientApplicationRead.model_validate(app) for app in apps]


@router.get(
    "/package/{package_name}/list",
    response_model=list[ClientApplicationRead],
    summary="根据包名获取应用列表",
)
async def get_applications_by_package_name(
    package_name: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ClientApplicationRead]:
    """根据包名获取客户端应用列表（精确匹配）。"""
    service = ClientApplicationService(db)
    apps = await service.get_applications_by_package_name(
        package_name=package_name,
        skip=skip,
        limit=limit,
    )
    return [ClientApplicationRead.model_validate(app) for app in apps]


@router.get(
    "/search/name",
    response_model=list[ClientApplicationRead],
    summary="根据应用名称搜索应用",
)
async def search_applications_by_name(
    app_name: str = Query(..., description="应用名称（模糊匹配）"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ClientApplicationRead]:
    """根据应用名称搜索客户端应用（支持模糊匹配）。"""
    service = ClientApplicationService(db)
    apps = await service.search_by_app_name(
        app_name=app_name,
        skip=skip,
        limit=limit,
    )
    return [ClientApplicationRead.model_validate(app) for app in apps]


@router.get(
    "/high-risk/list",
    response_model=list[ClientApplicationRead],
    summary="获取高风险应用列表",
)
async def get_high_risk_applications(
    risk_threshold: float = Query(7.0, ge=0.0, le=10.0, description="风险评分阈值"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ClientApplicationRead]:
    """获取高风险客户端应用列表（风险评分大于等于阈值）。"""
    service = ClientApplicationService(db)
    apps = await service.get_high_risk_applications(
        risk_threshold=risk_threshold,
        skip=skip,
        limit=limit,
    )
    return [ClientApplicationRead.model_validate(app) for app in apps]


@router.get(
    "/bundle/{bundle_id}/list",
    response_model=list[ClientApplicationRead],
    summary="根据Bundle ID获取应用列表",
)
async def get_applications_by_bundle_id(
    bundle_id: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ClientApplicationRead]:
    """根据Bundle ID获取客户端应用列表（iOS专用）。"""
    service = ClientApplicationService(db)
    apps = await service.get_applications_by_bundle_id(
        bundle_id=bundle_id,
        skip=skip,
        limit=limit,
    )
    return [ClientApplicationRead.model_validate(app) for app in apps]
