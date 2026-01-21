"""
资产Schema包

导出所有资产类型的Pydantic模型。
"""

from app.schemas.assets.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationRead
)
from app.schemas.assets.domain import (
    DomainCreate,
    DomainUpdate,
    DomainRead
)
from app.schemas.assets.ip import (
    IPCreate,
    IPUpdate,
    IPRead
)
from app.schemas.assets.netblock import (
    NetblockCreate,
    NetblockUpdate,
    NetblockRead
)
from app.schemas.assets.certificate import (
    CertificateCreate,
    CertificateUpdate,
    CertificateRead
)
from app.schemas.assets.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceRead
)
from app.schemas.assets.client_application import (
    ClientApplicationCreate,
    ClientApplicationUpdate,
    ClientApplicationRead
)
from app.schemas.assets.credential import (
    CredentialCreate,
    CredentialUpdate,
    CredentialRead
)

__all__ = [
    # Organization
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationRead",
    # Domain
    "DomainCreate",
    "DomainUpdate",
    "DomainRead",
    # IP
    "IPCreate",
    "IPUpdate",
    "IPRead",
    # Netblock
    "NetblockCreate",
    "NetblockUpdate",
    "NetblockRead",
    # Certificate
    "CertificateCreate",
    "CertificateUpdate",
    "CertificateRead",
    # Service
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceRead",
    # ClientApplication
    "ClientApplicationCreate",
    "ClientApplicationUpdate",
    "ClientApplicationRead",
    # Credential
    "CredentialCreate",
    "CredentialUpdate",
    "CredentialRead",
]
