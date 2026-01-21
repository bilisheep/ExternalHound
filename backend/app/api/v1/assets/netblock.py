"""
Netblock API路由。

提供网段资产的RESTful API端点，包括CRUD操作和CIDR拓扑查询。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.postgres import get_db
from app.schemas.assets.netblock import NetblockCreate, NetblockRead, NetblockUpdate
from app.schemas.common import SuccessResponse
from app.services.assets.netblock import NetblockService

router = APIRouter(prefix="/netblocks", tags=["Netblocks"])


@router.post(
    "",
    response_model=NetblockRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建网段",
)
async def create_netblock(
    data: NetblockCreate,
    db: AsyncSession = Depends(get_db),
) -> NetblockRead:
    """
    创建新的网段资产。

    - **external_id**: 业务唯一标识（可选，不填自动生成）
    - **cidr**: 网段CIDR表示（必填）
    - **asn_number**: AS自治系统号（可选）
    - **live_count**: 存活IP数量（默认0）
    - **risk_score**: 风险评分（默认0.0）
    - **is_internal**: 是否为内网段（可选，未指定时自动判断）
    - **scope_policy**: 范围策略（默认IN_SCOPE）
    - **metadata**: 元数据（可选）
    - **created_by**: 创建者标识（可选）
    """
    service = NetblockService(db)
    netblock = await service.create_netblock(data)
    await db.commit()
    return NetblockRead.model_validate(netblock)


@router.get(
    "/{id}",
    response_model=NetblockRead,
    summary="获取网段详情",
)
async def get_netblock(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> NetblockRead:
    """根据UUID获取网段详情。"""
    service = NetblockService(db)
    netblock = await service.get_netblock(id)
    return NetblockRead.model_validate(netblock)


@router.get(
    "/external/{external_id}",
    response_model=NetblockRead,
    summary="根据业务ID获取网段",
)
async def get_netblock_by_external_id(
    external_id: str,
    db: AsyncSession = Depends(get_db),
) -> NetblockRead:
    """根据业务唯一标识获取网段详情。"""
    service = NetblockService(db)
    netblock = await service.get_netblock_by_external_id(external_id)
    return NetblockRead.model_validate(netblock)


@router.get(
    "/cidr/{cidr:path}",
    response_model=NetblockRead,
    summary="根据CIDR获取网段",
)
async def get_netblock_by_cidr(
    cidr: str,
    db: AsyncSession = Depends(get_db),
) -> NetblockRead:
    """根据CIDR获取网段详情。"""
    service = NetblockService(db)
    netblock = await service.get_netblock_by_cidr(cidr)
    return NetblockRead.model_validate(netblock)


@router.get(
    "",
    response_model=Page[NetblockRead],
    summary="分页查询网段",
)
async def list_netblocks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    asn_number: str | None = Query(None, description="AS号"),
    is_internal: bool | None = Query(None, description="是否为内网段"),
    scope_policy: str | None = Query(None, description="范围策略"),
    db: AsyncSession = Depends(get_db),
) -> Page[NetblockRead]:
    """
    分页查询网段列表，支持过滤条件。

    - **page**: 页码（默认1）
    - **page_size**: 每页记录数（默认20）
    - **asn_number**: AS号（可选）
    - **is_internal**: 是否为内网段（可选）
    - **scope_policy**: 范围策略（可选）
    """
    service = NetblockService(db)
    filters = {}
    if asn_number is not None:
        filters["asn_number"] = asn_number.strip().upper()
    if is_internal is not None:
        filters["is_internal"] = is_internal
    if scope_policy is not None:
        filters["scope_policy"] = scope_policy

    result = await service.paginate_netblocks(
        page=page,
        page_size=page_size,
        **filters,
    )

    return Page(
        items=[NetblockRead.model_validate(netblock) for netblock in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.put(
    "/{id}",
    response_model=NetblockRead,
    summary="更新网段",
)
async def update_netblock(
    id: UUID,
    data: NetblockUpdate,
    db: AsyncSession = Depends(get_db),
) -> NetblockRead:
    """更新网段信息。只更新提供的字段。"""
    service = NetblockService(db)
    netblock = await service.update_netblock(id, data)
    await db.commit()
    return NetblockRead.model_validate(netblock)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除网段",
)
async def delete_netblock(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """软删除网段（标记为已删除，不物理删除）。"""
    service = NetblockService(db)
    await service.delete_netblock(id)
    await db.commit()
    return SuccessResponse(message="Netblock deleted successfully")


@router.get(
    "/internal/list",
    response_model=list[NetblockRead],
    summary="获取内网段列表",
)
async def get_internal_netblocks(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[NetblockRead]:
    """获取所有内网段列表（RFC1918私有地址范围）。"""
    service = NetblockService(db)
    netblocks = await service.get_internal_netblocks(skip=skip, limit=limit)
    return [NetblockRead.model_validate(netblock) for netblock in netblocks]


@router.get(
    "/asn/{asn_number}/list",
    response_model=list[NetblockRead],
    summary="根据AS号获取网段列表",
)
async def get_netblocks_by_asn(
    asn_number: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[NetblockRead]:
    """根据AS自治系统号获取网段列表。"""
    service = NetblockService(db)
    netblocks = await service.get_netblocks_by_asn(
        asn_number=asn_number.strip().upper(),
        skip=skip,
        limit=limit,
    )
    return [NetblockRead.model_validate(netblock) for netblock in netblocks]


@router.get(
    "/contains/{ip_address}",
    response_model=list[NetblockRead],
    summary="查询包含指定IP的网段",
)
async def get_netblocks_containing_ip(
    ip_address: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[NetblockRead]:
    """查询包含指定IP地址的所有网段列表（使用PostgreSQL CIDR包含查询）。"""
    service = NetblockService(db)
    netblocks = await service.get_netblocks_containing_ip(
        ip_address=ip_address,
        skip=skip,
        limit=limit,
    )
    return [NetblockRead.model_validate(netblock) for netblock in netblocks]


@router.get(
    "/overlaps/{cidr:path}",
    response_model=list[NetblockRead],
    summary="查询与指定CIDR有交集的网段",
)
async def get_overlapping_netblocks(
    cidr: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[NetblockRead]:
    """查询与指定CIDR有地址交集的所有网段列表（使用PostgreSQL CIDR重叠查询）。"""
    service = NetblockService(db)
    netblocks = await service.get_overlapping_netblocks(
        cidr=cidr,
        skip=skip,
        limit=limit,
    )
    return [NetblockRead.model_validate(netblock) for netblock in netblocks]
