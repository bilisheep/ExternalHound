"""
资产API路由包

导出所有资产类型的路由。
"""

from app.api.v1.assets.organization import router as organization_router
from app.api.v1.assets.domain import router as domain_router
from app.api.v1.assets.ip import router as ip_router
from app.api.v1.assets.netblock import router as netblock_router
from app.api.v1.assets.certificate import router as certificate_router
from app.api.v1.assets.service import router as service_router
from app.api.v1.assets.client_application import router as client_application_router
from app.api.v1.assets.credential import router as credential_router

__all__ = [
    "organization_router",
    "domain_router",
    "ip_router",
    "netblock_router",
    "certificate_router",
    "service_router",
    "client_application_router",
    "credential_router",
]
