"""
API v1路由包

聚合所有v1版本的API路由。
"""

from fastapi import APIRouter

from app.api.v1.assets import (
    organization_router,
    domain_router,
    ip_router,
    netblock_router,
    certificate_router,
    service_router,
    client_application_router,
    credential_router,
)
from app.api.v1.relationships import relationship_router
from app.api.v1.imports import router as import_router

# 创建v1路由器
api_router = APIRouter(prefix="/v1")

# 注册资产路由
api_router.include_router(organization_router)
api_router.include_router(domain_router)
api_router.include_router(ip_router)
api_router.include_router(netblock_router)
api_router.include_router(certificate_router)
api_router.include_router(service_router)
api_router.include_router(client_application_router)
api_router.include_router(credential_router)

# 注册关系路由
api_router.include_router(relationship_router)
api_router.include_router(import_router)

__all__ = ["api_router"]
