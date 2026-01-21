"""
Certificate资产的Service层。

负责证书资产的业务逻辑，包括自动计算过期状态、自签名判断等。
"""

import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.common import Page
from app.repositories.assets.certificate import CertificateRepository
from app.schemas.assets.certificate import CertificateCreate, CertificateUpdate
from app.utils.external_id import generate_certificate_external_id


class CertificateService:
    """证书资产的业务逻辑服务。"""

    def __init__(self, db: AsyncSession):
        """初始化服务。

        Args:
            db: 数据库会话
        """
        self.db = db
        self.repo = CertificateRepository(db)

    async def create_certificate(self, data: CertificateCreate):
        """创建证书，自动计算过期状态、自签名判断、剩余天数和SAN数量。

        Args:
            data: 证书创建数据

        Returns:
            创建的证书对象

        Raises:
            ConflictError: 当external_id已存在时
        """
        external_id = data.external_id.strip() if data.external_id else None
        if not external_id:
            external_id = generate_certificate_external_id(
                metadata=data.metadata_,
                subject_cn=data.subject_cn,
                issuer_cn=data.issuer_cn,
                issuer_org=data.issuer_org,
                valid_from=data.valid_from,
                valid_to=data.valid_to,
            )

        # 检查external_id是否已存在
        existing = await self.repo.get_by_external_id(external_id)
        if existing is not None:
            raise ConflictError(
                resource_type="Certificate",
                field="external_id",
                value=external_id,
            )

        create_data = data.model_dump()
        create_data["external_id"] = external_id

        # 自动计算is_expired（如果提供了valid_to）
        if create_data.get("valid_to") is not None:
            current_timestamp = int(time.time())
            create_data["is_expired"] = create_data["valid_to"] < current_timestamp

        # 自动计算days_to_expire（如果提供了valid_to）
        if create_data.get("valid_to") is not None:
            current_timestamp = int(time.time())
            seconds_to_expire = create_data["valid_to"] - current_timestamp
            create_data["days_to_expire"] = seconds_to_expire // 86400  # 转换为天数

        # 自动判断is_self_signed（如果subject_cn和issuer_cn都存在且相等）
        subject_cn = create_data.get("subject_cn")
        issuer_cn = create_data.get("issuer_cn")
        if subject_cn and issuer_cn:
            create_data["is_self_signed"] = subject_cn == issuer_cn

        # 自动计算san_count（从metadata的subject_alt_names中获取）
        metadata = create_data.get("metadata_", {})
        subject_alt_names = metadata.get("subject_alt_names", [])
        if isinstance(subject_alt_names, list):
            create_data["san_count"] = len(subject_alt_names)

        return await self.repo.create(**create_data)

    async def get_certificate(self, id: UUID):
        """根据UUID获取证书详情。

        Args:
            id: 证书UUID

        Returns:
            证书对象

        Raises:
            NotFoundError: 当证书不存在时
        """
        certificate = await self.repo.get_by_id(id)
        if certificate is None:
            raise NotFoundError(
                resource_type="Certificate",
                resource_id=str(id),
            )
        return certificate

    async def get_certificate_by_external_id(self, external_id: str):
        """根据业务ID获取证书详情。

        Args:
            external_id: 业务唯一标识

        Returns:
            证书对象

        Raises:
            NotFoundError: 当证书不存在时
        """
        certificate = await self.repo.get_by_external_id(external_id)
        if certificate is None:
            raise NotFoundError(
                resource_type="Certificate",
                resource_id=external_id,
            )
        return certificate

    async def get_certificates_by_subject_cn(
        self,
        subject_cn: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据主题通用名称获取证书列表。

        Args:
            subject_cn: 主题通用名称
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            证书列表
        """
        return await self.repo.get_by_subject_cn(
            subject_cn=subject_cn,
            skip=skip,
            limit=limit,
        )

    async def get_expired_certificates(self, skip: int = 0, limit: int = 100):
        """获取已过期的证书列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            已过期的证书列表
        """
        return await self.repo.get_expired_certificates(skip=skip, limit=limit)

    async def get_self_signed_certificates(self, skip: int = 0, limit: int = 100):
        """获取自签名证书列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            自签名证书列表
        """
        return await self.repo.get_self_signed_certificates(skip=skip, limit=limit)

    async def get_revoked_certificates(self, skip: int = 0, limit: int = 100):
        """获取已吊销的证书列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            已吊销的证书列表
        """
        return await self.repo.get_revoked_certificates(skip=skip, limit=limit)

    async def search_by_issuer(
        self,
        issuer_cn: str | None = None,
        issuer_org: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据颁发者信息搜索证书。

        Args:
            issuer_cn: 颁发者通用名称（模糊匹配）
            issuer_org: 颁发者组织名称（模糊匹配）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的证书列表
        """
        return await self.repo.search_by_issuer(
            issuer_cn=issuer_cn,
            issuer_org=issuer_org,
            skip=skip,
            limit=limit,
        )

    async def get_expiring_soon(
        self,
        days_threshold: int = 30,
        skip: int = 0,
        limit: int = 100,
    ):
        """获取即将过期的证书列表。

        Args:
            days_threshold: 剩余天数阈值（默认30天）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            即将过期的证书列表
        """
        return await self.repo.get_expiring_soon(
            days_threshold=days_threshold,
            skip=skip,
            limit=limit,
        )

    async def paginate_certificates(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters,
    ) -> Page:
        """分页查询证书列表。

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 过滤条件（is_expired、is_self_signed、is_revoked、scope_policy等）

        Returns:
            分页结果
        """
        return await self.repo.paginate(
            page=page,
            page_size=page_size,
            **filters,
        )

    async def update_certificate(self, id: UUID, data: CertificateUpdate):
        """更新证书信息，自动重新计算过期状态和剩余天数（如果valid_to被修改）。

        Args:
            id: 证书UUID
            data: 更新数据

        Returns:
            更新后的证书对象

        Raises:
            NotFoundError: 当证书不存在时
        """
        certificate = await self.repo.get_by_id(id)
        if certificate is None:
            raise NotFoundError(
                resource_type="Certificate",
                resource_id=str(id),
            )

        update_data = data.model_dump(exclude_unset=True)

        # 如果更新了valid_to，自动重新计算is_expired和days_to_expire
        if "valid_to" in update_data and update_data["valid_to"] is not None:
            current_timestamp = int(time.time())
            update_data["is_expired"] = update_data["valid_to"] < current_timestamp
            seconds_to_expire = update_data["valid_to"] - current_timestamp
            update_data["days_to_expire"] = seconds_to_expire // 86400

        # 如果更新了subject_cn或issuer_cn，自动重新判断is_self_signed
        if "subject_cn" in update_data or "issuer_cn" in update_data:
            subject_cn = update_data.get("subject_cn", certificate.subject_cn)
            issuer_cn = update_data.get("issuer_cn", certificate.issuer_cn)
            if subject_cn and issuer_cn:
                update_data["is_self_signed"] = subject_cn == issuer_cn

        # 如果更新了metadata且包含subject_alt_names，自动重新计算san_count
        if "metadata_" in update_data and update_data["metadata_"] is not None:
            metadata = update_data["metadata_"]
            subject_alt_names = metadata.get("subject_alt_names", [])
            if isinstance(subject_alt_names, list):
                update_data["san_count"] = len(subject_alt_names)

        return await self.repo.update(id, **update_data)

    async def delete_certificate(self, id: UUID):
        """软删除证书（标记为已删除，不物理删除）。

        Args:
            id: 证书UUID

        Raises:
            NotFoundError: 当证书不存在时
        """
        certificate = await self.repo.get_by_id(id)
        if certificate is None:
            raise NotFoundError(
                resource_type="Certificate",
                resource_id=str(id),
            )
        await self.repo.soft_delete(id)
