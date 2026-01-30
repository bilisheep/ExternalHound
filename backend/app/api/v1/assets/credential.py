"""
Credential API路由。

提供凭证资产的RESTful API端点，包括CRUD操作和凭证特定查询。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.neo4j import Neo4jManager, get_neo4j
from app.db.postgres import get_db
from app.schemas.assets.credential import (
    CredentialCreate,
    CredentialRead,
    CredentialUpdate,
)
from app.schemas.common import SuccessResponse
from app.services.assets.credential import CredentialService

router = APIRouter(prefix="/credentials", tags=["Credentials"])


@router.post(
    "",
    response_model=CredentialRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建凭证",
)
async def create_credential(
    data: CredentialCreate,
    db: AsyncSession = Depends(get_db),
) -> CredentialRead:
    """
    创建新的凭证资产。

    - **external_id**: 业务唯一标识（可选，不填自动生成）
    - **cred_type**: 凭证类型（必填，PASSWORD/API_KEY/TOKEN等）
    - **provider**: 提供方/来源（可选）
    - **username**: 用户名（可选）
    - **email**: 电子邮箱（可选）
    - **phone**: 电话号码（可选）
    - **leaked_count**: 泄露次数（默认0）
    - **content**: 凭证内容（JSONB格式，敏感信息）
    - **validation_result**: 验证结果（可选，VALID/INVALID/UNKNOWN）
    - **scope_policy**: 范围策略（默认IN_SCOPE）
    - **metadata**: 元数据（可选）
    - **created_by**: 创建者标识（可选）
    """
    service = CredentialService(db)
    credential = await service.create_credential(data)
    await db.commit()
    return CredentialRead.model_validate(credential)


@router.get(
    "/{id}",
    response_model=CredentialRead,
    summary="获取凭证详情",
)
async def get_credential(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CredentialRead:
    """根据UUID获取凭证详情。"""
    service = CredentialService(db)
    credential = await service.get_credential(id)
    return CredentialRead.model_validate(credential)


@router.get(
    "/external/{external_id}",
    response_model=CredentialRead,
    summary="根据业务ID获取凭证",
)
async def get_credential_by_external_id(
    external_id: str,
    db: AsyncSession = Depends(get_db),
) -> CredentialRead:
    """根据业务唯一标识获取凭证详情。"""
    service = CredentialService(db)
    credential = await service.get_credential_by_external_id(external_id)
    return CredentialRead.model_validate(credential)


@router.get(
    "",
    response_model=Page[CredentialRead],
    summary="分页查询凭证",
)
async def list_credentials(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    cred_type: str | None = Query(None, description="凭证类型"),
    provider: str | None = Query(None, description="提供方/来源"),
    validation_result: str | None = Query(None, description="验证结果"),
    scope_policy: str | None = Query(None, description="范围策略"),
    db: AsyncSession = Depends(get_db),
) -> Page[CredentialRead]:
    """
    分页查询凭证列表，支持过滤条件。

    - **page**: 页码（默认1）
    - **page_size**: 每页记录数（默认20）
    - **cred_type**: 凭证类型（可选）
    - **provider**: 提供方/来源（可选）
    - **validation_result**: 验证结果（可选）
    - **scope_policy**: 范围策略（可选）
    """
    service = CredentialService(db)
    filters = {}
    if cred_type is not None:
        filters["cred_type"] = cred_type
    if provider is not None:
        filters["provider"] = provider
    if validation_result is not None:
        filters["validation_result"] = validation_result
    if scope_policy is not None:
        filters["scope_policy"] = scope_policy

    result = await service.paginate_credentials(
        page=page,
        page_size=page_size,
        **filters,
    )

    return Page(
        items=[CredentialRead.model_validate(cred) for cred in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.put(
    "/{id}",
    response_model=CredentialRead,
    summary="更新凭证",
)
async def update_credential(
    id: UUID,
    data: CredentialUpdate,
    db: AsyncSession = Depends(get_db),
) -> CredentialRead:
    """更新凭证信息。只更新提供的字段。"""
    service = CredentialService(db)
    credential = await service.update_credential(id, data)
    await db.commit()
    return CredentialRead.model_validate(credential)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除凭证",
)
async def delete_credential(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> SuccessResponse:
    """硬删除凭证（物理删除）。"""
    service = CredentialService(db, neo4j)
    await service.delete_credential(id)
    await db.commit()
    return SuccessResponse(message="Credential deleted successfully")


@router.get(
    "/type/{cred_type}/list",
    response_model=list[CredentialRead],
    summary="根据凭证类型获取凭证列表",
)
async def get_credentials_by_type(
    cred_type: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CredentialRead]:
    """根据凭证类型获取凭证列表（PASSWORD/API_KEY/TOKEN等）。"""
    service = CredentialService(db)
    credentials = await service.get_credentials_by_type(
        cred_type=cred_type,
        skip=skip,
        limit=limit,
    )
    return [CredentialRead.model_validate(cred) for cred in credentials]


@router.get(
    "/leaked/list",
    response_model=list[CredentialRead],
    summary="获取泄露凭证列表",
)
async def get_leaked_credentials(
    min_leaked_count: int = Query(1, ge=0, description="最小泄露次数"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CredentialRead]:
    """获取泄露凭证列表（泄露次数大于等于阈值）。"""
    service = CredentialService(db)
    credentials = await service.get_leaked_credentials(
        min_leaked_count=min_leaked_count,
        skip=skip,
        limit=limit,
    )
    return [CredentialRead.model_validate(cred) for cred in credentials]


@router.get(
    "/provider/{provider}/list",
    response_model=list[CredentialRead],
    summary="根据提供方获取凭证列表",
)
async def get_credentials_by_provider(
    provider: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CredentialRead]:
    """根据提供方/来源获取凭证列表（模糊匹配）。"""
    service = CredentialService(db)
    credentials = await service.get_credentials_by_provider(
        provider=provider,
        skip=skip,
        limit=limit,
    )
    return [CredentialRead.model_validate(cred) for cred in credentials]


@router.get(
    "/search/username",
    response_model=list[CredentialRead],
    summary="根据用户名搜索凭证",
)
async def search_credentials_by_username(
    username: str = Query(..., description="用户名（模糊匹配）"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CredentialRead]:
    """根据用户名搜索凭证（支持模糊匹配）。"""
    service = CredentialService(db)
    credentials = await service.search_by_username(
        username=username,
        skip=skip,
        limit=limit,
    )
    return [CredentialRead.model_validate(cred) for cred in credentials]


@router.get(
    "/search/email",
    response_model=list[CredentialRead],
    summary="根据电子邮箱搜索凭证",
)
async def search_credentials_by_email(
    email: str = Query(..., description="电子邮箱（模糊匹配）"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CredentialRead]:
    """根据电子邮箱搜索凭证（支持模糊匹配）。"""
    service = CredentialService(db)
    credentials = await service.search_by_email(
        email=email,
        skip=skip,
        limit=limit,
    )
    return [CredentialRead.model_validate(cred) for cred in credentials]


@router.get(
    "/validation/{validation_result}/list",
    response_model=list[CredentialRead],
    summary="根据验证结果获取凭证列表",
)
async def get_credentials_by_validation_result(
    validation_result: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CredentialRead]:
    """根据验证结果获取凭证列表（VALID/INVALID/UNKNOWN）。"""
    service = CredentialService(db)
    credentials = await service.get_credentials_by_validation_result(
        validation_result=validation_result,
        skip=skip,
        limit=limit,
    )
    return [CredentialRead.model_validate(cred) for cred in credentials]


@router.get(
    "/valid/list",
    response_model=list[CredentialRead],
    summary="获取有效凭证列表",
)
async def get_valid_credentials(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CredentialRead]:
    """获取有效凭证列表（validation_result=VALID）。"""
    service = CredentialService(db)
    credentials = await service.get_valid_credentials(skip=skip, limit=limit)
    return [CredentialRead.model_validate(cred) for cred in credentials]
