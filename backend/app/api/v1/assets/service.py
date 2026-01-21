"""
Service API路由。

提供服务资产的RESTful API端点，包括CRUD操作和服务特定查询。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.postgres import get_db
from app.schemas.assets.service import ServiceCreate, ServiceRead, ServiceUpdate
from app.schemas.common import SuccessResponse
from app.services.assets.service import ServiceService

router = APIRouter(prefix="/services", tags=["Services"])


@router.post(
    "",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建服务",
)
async def create_service(
    data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    """
    创建新的服务资产。

    - **external_id**: 业务唯一标识（可选，不填自动生成）
    - **service_name**: 服务名称（可选）
    - **port**: 端口号（必填）
    - **protocol**: 协议类型（默认TCP）
    - **product**: 产品名称（可选）
    - **version**: 版本号（可选）
    - **banner**: Banner信息（可选）
    - **is_http**: 是否为HTTP服务（自动检测，可覆盖）
    - **risk_score**: 风险评分（默认0.0）
    - **asset_category**: 资产分类（自动检测，可覆盖）
    - **scope_policy**: 范围策略（默认IN_SCOPE）
    - **metadata**: 元数据（可选）
    - **created_by**: 创建者标识（可选）
    """
    service = ServiceService(db)
    svc = await service.create_service(data)
    await db.commit()
    return ServiceRead.model_validate(svc)


@router.get(
    "/{id}",
    response_model=ServiceRead,
    summary="获取服务详情",
)
async def get_service(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    """根据UUID获取服务详情。"""
    service = ServiceService(db)
    svc = await service.get_service(id)
    return ServiceRead.model_validate(svc)


@router.get(
    "/external/{external_id}",
    response_model=ServiceRead,
    summary="根据业务ID获取服务",
)
async def get_service_by_external_id(
    external_id: str,
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    """根据业务唯一标识获取服务详情。"""
    service = ServiceService(db)
    svc = await service.get_service_by_external_id(external_id)
    return ServiceRead.model_validate(svc)


@router.get(
    "",
    response_model=Page[ServiceRead],
    summary="分页查询服务",
)
async def list_services(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    port: int | None = Query(None, ge=1, le=65535, description="端口号"),
    protocol: str | None = Query(None, description="协议类型（TCP/UDP）"),
    is_http: bool | None = Query(None, description="是否为HTTP服务"),
    asset_category: str | None = Query(None, description="资产分类"),
    scope_policy: str | None = Query(None, description="范围策略"),
    db: AsyncSession = Depends(get_db),
) -> Page[ServiceRead]:
    """
    分页查询服务列表，支持过滤条件。

    - **page**: 页码（默认1）
    - **page_size**: 每页记录数（默认20）
    - **port**: 端口号（可选）
    - **protocol**: 协议类型（可选）
    - **is_http**: 是否为HTTP服务（可选）
    - **asset_category**: 资产分类（可选）
    - **scope_policy**: 范围策略（可选）
    """
    service = ServiceService(db)
    filters = {}
    if port is not None:
        filters["port"] = port
    if protocol is not None:
        filters["protocol"] = protocol.upper()
    if is_http is not None:
        filters["is_http"] = is_http
    if asset_category is not None:
        filters["asset_category"] = asset_category
    if scope_policy is not None:
        filters["scope_policy"] = scope_policy

    result = await service.paginate_services(
        page=page,
        page_size=page_size,
        **filters,
    )

    return Page(
        items=[ServiceRead.model_validate(svc) for svc in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.put(
    "/{id}",
    response_model=ServiceRead,
    summary="更新服务",
)
async def update_service(
    id: UUID,
    data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    """更新服务信息。只更新提供的字段。"""
    service = ServiceService(db)
    svc = await service.update_service(id, data)
    await db.commit()
    return ServiceRead.model_validate(svc)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除服务",
)
async def delete_service(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """软删除服务（标记为已删除，不物理删除）。"""
    service = ServiceService(db)
    await service.delete_service(id)
    await db.commit()
    return SuccessResponse(message="Service deleted successfully")


@router.get(
    "/port/{port}/list",
    response_model=list[ServiceRead],
    summary="根据端口号获取服务列表",
)
async def get_services_by_port(
    port: int,
    protocol: str | None = Query(None, description="协议类型（TCP/UDP）"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    """根据端口号获取服务列表（可选指定协议类型）。"""
    service = ServiceService(db)
    services = await service.get_services_by_port(
        port=port,
        protocol=protocol,
        skip=skip,
        limit=limit,
    )
    return [ServiceRead.model_validate(svc) for svc in services]


@router.get(
    "/name/{service_name}/list",
    response_model=list[ServiceRead],
    summary="根据服务名称获取服务列表",
)
async def get_services_by_name(
    service_name: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    """根据服务名称获取服务列表（不区分大小写）。"""
    service = ServiceService(db)
    services = await service.get_services_by_name(
        service_name=service_name,
        skip=skip,
        limit=limit,
    )
    return [ServiceRead.model_validate(svc) for svc in services]


@router.get(
    "/http/list",
    response_model=list[ServiceRead],
    summary="获取所有HTTP/HTTPS服务列表",
)
async def get_http_services(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    """获取所有HTTP/HTTPS服务列表。"""
    service = ServiceService(db)
    services = await service.get_http_services(skip=skip, limit=limit)
    return [ServiceRead.model_validate(svc) for svc in services]


@router.get(
    "/search/product",
    response_model=list[ServiceRead],
    summary="根据产品名称搜索服务",
)
async def search_services_by_product(
    product: str = Query(..., description="产品名称（模糊匹配）"),
    version: str | None = Query(None, description="版本号（精确匹配）"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    """根据产品名称和版本搜索服务（产品名称支持模糊匹配）。"""
    service = ServiceService(db)
    services = await service.search_by_product(
        product=product,
        version=version,
        skip=skip,
        limit=limit,
    )
    return [ServiceRead.model_validate(svc) for svc in services]


@router.get(
    "/category/{asset_category}/list",
    response_model=list[ServiceRead],
    summary="根据资产分类获取服务列表",
)
async def get_services_by_category(
    asset_category: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    """根据资产分类获取服务列表（如 WEB、DATABASE、MIDDLEWARE等）。"""
    service = ServiceService(db)
    services = await service.get_services_by_category(
        asset_category=asset_category,
        skip=skip,
        limit=limit,
    )
    return [ServiceRead.model_validate(svc) for svc in services]


@router.get(
    "/high-risk/list",
    response_model=list[ServiceRead],
    summary="获取高风险服务列表",
)
async def get_high_risk_services(
    risk_threshold: float = Query(7.0, ge=0.0, le=10.0, description="风险评分阈值"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    """获取高风险服务列表（风险评分大于等于阈值）。"""
    service = ServiceService(db)
    services = await service.get_high_risk_services(
        risk_threshold=risk_threshold,
        skip=skip,
        limit=limit,
    )
    return [ServiceRead.model_validate(svc) for svc in services]
