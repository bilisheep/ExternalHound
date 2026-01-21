"""
资产Repository包

导出所有资产类型的Repository类。
"""

from app.repositories.assets.organization import OrganizationRepository
from app.repositories.assets.domain import DomainRepository
from app.repositories.assets.ip import IPRepository
from app.repositories.assets.netblock import NetblockRepository
from app.repositories.assets.certificate import CertificateRepository
from app.repositories.assets.service import ServiceRepository
from app.repositories.assets.client_application import ClientApplicationRepository
from app.repositories.assets.credential import CredentialRepository

__all__ = [
    "OrganizationRepository",
    "DomainRepository",
    "IPRepository",
    "NetblockRepository",
    "CertificateRepository",
    "ServiceRepository",
    "ClientApplicationRepository",
    "CredentialRepository",
]
