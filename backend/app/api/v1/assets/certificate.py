"""
Certificate API路由。

提供证书资产的RESTful API端点，包括CRUD操作和证书状态查询。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.neo4j import Neo4jManager, get_neo4j
from app.db.postgres import get_db
from app.schemas.assets.certificate import (
    CertificateCreate,
    CertificateRead,
    CertificateUpdate,
)
from app.schemas.common import SuccessResponse
from app.services.assets.certificate import CertificateService

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.post(
    "",
    response_model=CertificateRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建证书",
)
async def create_certificate(
    data: CertificateCreate,
    db: AsyncSession = Depends(get_db),
) -> CertificateRead:
    """
    创建新的证书资产。

    - **external_id**: 业务唯一标识（可选，不填自动生成）
    - **subject_cn**: 主题通用名称（可选）
    - **issuer_cn**: 颁发者通用名称（可选）
    - **issuer_org**: 颁发者组织名称（可选）
    - **valid_from**: 生效时间戳（可选）
    - **valid_to**: 过期时间戳（可选）
    - **is_expired**: 是否已过期（自动计算，可覆盖）
    - **is_self_signed**: 是否为自签名证书（自动计算，可覆盖）
    - **is_revoked**: 是否已被吊销（可选）
    - **san_count**: SAN数量（自动计算，可覆盖）
    - **scope_policy**: 范围策略（默认IN_SCOPE）
    - **metadata**: 元数据（可选）
    - **created_by**: 创建者标识（可选）
    """
    service = CertificateService(db)
    certificate = await service.create_certificate(data)
    await db.commit()
    return CertificateRead.model_validate(certificate)


@router.get(
    "/{id}",
    response_model=CertificateRead,
    summary="获取证书详情",
)
async def get_certificate(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CertificateRead:
    """根据UUID获取证书详情。"""
    service = CertificateService(db)
    certificate = await service.get_certificate(id)
    return CertificateRead.model_validate(certificate)


@router.get(
    "/external/{external_id}",
    response_model=CertificateRead,
    summary="根据业务ID获取证书",
)
async def get_certificate_by_external_id(
    external_id: str,
    db: AsyncSession = Depends(get_db),
) -> CertificateRead:
    """根据业务唯一标识获取证书详情。"""
    service = CertificateService(db)
    certificate = await service.get_certificate_by_external_id(external_id)
    return CertificateRead.model_validate(certificate)


@router.get(
    "",
    response_model=Page[CertificateRead],
    summary="分页查询证书",
)
async def list_certificates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    is_expired: bool | None = Query(None, description="是否已过期"),
    is_self_signed: bool | None = Query(None, description="是否为自签名证书"),
    is_revoked: bool | None = Query(None, description="是否已被吊销"),
    scope_policy: str | None = Query(None, description="范围策略"),
    db: AsyncSession = Depends(get_db),
) -> Page[CertificateRead]:
    """
    分页查询证书列表，支持过滤条件。

    - **page**: 页码（默认1）
    - **page_size**: 每页记录数（默认20）
    - **is_expired**: 是否已过期（可选）
    - **is_self_signed**: 是否为自签名证书（可选）
    - **is_revoked**: 是否已被吊销（可选）
    - **scope_policy**: 范围策略（可选）
    """
    service = CertificateService(db)
    filters = {}
    if is_expired is not None:
        filters["is_expired"] = is_expired
    if is_self_signed is not None:
        filters["is_self_signed"] = is_self_signed
    if is_revoked is not None:
        filters["is_revoked"] = is_revoked
    if scope_policy is not None:
        filters["scope_policy"] = scope_policy

    result = await service.paginate_certificates(
        page=page,
        page_size=page_size,
        **filters,
    )

    return Page(
        items=[CertificateRead.model_validate(cert) for cert in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.put(
    "/{id}",
    response_model=CertificateRead,
    summary="更新证书",
)
async def update_certificate(
    id: UUID,
    data: CertificateUpdate,
    db: AsyncSession = Depends(get_db),
) -> CertificateRead:
    """更新证书信息。只更新提供的字段。"""
    service = CertificateService(db)
    certificate = await service.update_certificate(id, data)
    await db.commit()
    return CertificateRead.model_validate(certificate)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除证书",
)
async def delete_certificate(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> SuccessResponse:
    """硬删除证书（物理删除）。"""
    service = CertificateService(db, neo4j)
    await service.delete_certificate(id)
    await db.commit()
    return SuccessResponse(message="Certificate deleted successfully")


@router.get(
    "/subject/{subject_cn}/list",
    response_model=list[CertificateRead],
    summary="根据主题通用名称获取证书列表",
)
async def get_certificates_by_subject_cn(
    subject_cn: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CertificateRead]:
    """根据主题通用名称获取证书列表（精确匹配）。"""
    service = CertificateService(db)
    certificates = await service.get_certificates_by_subject_cn(
        subject_cn=subject_cn,
        skip=skip,
        limit=limit,
    )
    return [CertificateRead.model_validate(cert) for cert in certificates]


@router.get(
    "/expired/list",
    response_model=list[CertificateRead],
    summary="获取已过期的证书列表",
)
async def get_expired_certificates(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CertificateRead]:
    """获取所有已过期的证书列表。"""
    service = CertificateService(db)
    certificates = await service.get_expired_certificates(skip=skip, limit=limit)
    return [CertificateRead.model_validate(cert) for cert in certificates]


@router.get(
    "/self-signed/list",
    response_model=list[CertificateRead],
    summary="获取自签名证书列表",
)
async def get_self_signed_certificates(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CertificateRead]:
    """获取所有自签名证书列表。"""
    service = CertificateService(db)
    certificates = await service.get_self_signed_certificates(skip=skip, limit=limit)
    return [CertificateRead.model_validate(cert) for cert in certificates]


@router.get(
    "/revoked/list",
    response_model=list[CertificateRead],
    summary="获取已吊销的证书列表",
)
async def get_revoked_certificates(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CertificateRead]:
    """获取所有已吊销的证书列表。"""
    service = CertificateService(db)
    certificates = await service.get_revoked_certificates(skip=skip, limit=limit)
    return [CertificateRead.model_validate(cert) for cert in certificates]


@router.get(
    "/expiring-soon/list",
    response_model=list[CertificateRead],
    summary="获取即将过期的证书列表",
)
async def get_expiring_soon_certificates(
    days: int = Query(30, ge=1, le=365, description="剩余天数阈值"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CertificateRead]:
    """获取即将过期的证书列表（剩余天数小于阈值且未过期）。"""
    service = CertificateService(db)
    certificates = await service.get_expiring_soon(
        days_threshold=days,
        skip=skip,
        limit=limit,
    )
    return [CertificateRead.model_validate(cert) for cert in certificates]


@router.get(
    "/search/issuer",
    response_model=list[CertificateRead],
    summary="根据颁发者信息搜索证书",
)
async def search_certificates_by_issuer(
    issuer_cn: str | None = Query(None, description="颁发者通用名称（模糊匹配）"),
    issuer_org: str | None = Query(None, description="颁发者组织名称（模糊匹配）"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
) -> list[CertificateRead]:
    """根据颁发者信息搜索证书（支持模糊匹配）。"""
    service = CertificateService(db)
    certificates = await service.search_by_issuer(
        issuer_cn=issuer_cn,
        issuer_org=issuer_org,
        skip=skip,
        limit=limit,
    )
    return [CertificateRead.model_validate(cert) for cert in certificates]
