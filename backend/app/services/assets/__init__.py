"""
资产Service包

导出所有资产类型的Service类。
"""

from app.services.assets.organization import OrganizationService
from app.services.assets.domain import DomainService
from app.services.assets.ip import IPService
from app.services.assets.netblock import NetblockService
from app.services.assets.certificate import CertificateService
from app.services.assets.service import ServiceService
from app.services.assets.client_application import ClientApplicationService
from app.services.assets.credential import CredentialService

__all__ = [
    "OrganizationService",
    "DomainService",
    "IPService",
    "NetblockService",
    "CertificateService",
    "ServiceService",
    "ClientApplicationService",
    "CredentialService",
]
