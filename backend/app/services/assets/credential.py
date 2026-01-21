"""
Credential资产的Service层。

负责凭证资产的业务逻辑。
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.common import Page
from app.repositories.assets.credential import CredentialRepository
from app.schemas.assets.credential import CredentialCreate, CredentialUpdate
from app.utils.external_id import generate_credential_external_id


class CredentialService:
    """凭证资产的业务逻辑服务。"""

    def __init__(self, db: AsyncSession):
        """初始化服务。

        Args:
            db: 数据库会话
        """
        self.db = db
        self.repo = CredentialRepository(db)

    async def create_credential(self, data: CredentialCreate):
        """创建凭证。

        Args:
            data: 凭证创建数据

        Returns:
            创建的凭证对象

        Raises:
            ResourceAlreadyExistsError: 当external_id已存在时
        """
        external_id = data.external_id.strip() if data.external_id else None
        if not external_id:
            external_id = generate_credential_external_id(
                cred_type=data.cred_type,
                provider=data.provider,
                username=data.username,
                email=data.email,
                phone=data.phone,
                content=data.content,
            )

        # 检查external_id是否已存在
        existing = await self.repo.get_by_external_id(external_id)
        if existing is not None:
            raise ConflictError(
                resource_type="Credential",
                field="external_id",
                value=external_id,
            )

        create_data = data.model_dump()
        create_data["external_id"] = external_id
        return await self.repo.create(**create_data)

    async def get_credential(self, id: UUID):
        """根据UUID获取凭证详情。

        Args:
            id: 凭证UUID

        Returns:
            凭证对象

        Raises:
            NotFoundError: 当凭证不存在时
        """
        credential = await self.repo.get_by_id(id)
        if credential is None:
            raise NotFoundError(
                resource_type="Credential",
                resource_id=str(id),
            )
        return credential

    async def get_credential_by_external_id(self, external_id: str):
        """根据业务ID获取凭证详情。

        Args:
            external_id: 业务唯一标识

        Returns:
            凭证对象

        Raises:
            NotFoundError: 当凭证不存在时
        """
        credential = await self.repo.get_by_external_id(external_id)
        if credential is None:
            raise NotFoundError(
                resource_type="Credential",
                resource_id=external_id,
            )
        return credential

    async def get_credentials_by_type(
        self,
        cred_type: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据凭证类型获取凭证列表。

        Args:
            cred_type: 凭证类型
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            凭证列表
        """
        return await self.repo.get_by_cred_type(
            cred_type=cred_type,
            skip=skip,
            limit=limit,
        )

    async def get_leaked_credentials(
        self,
        min_leaked_count: int = 1,
        skip: int = 0,
        limit: int = 100,
    ):
        """获取泄露凭证列表。

        Args:
            min_leaked_count: 最小泄露次数
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            泄露凭证列表
        """
        return await self.repo.get_leaked_credentials(
            min_leaked_count=min_leaked_count,
            skip=skip,
            limit=limit,
        )

    async def get_credentials_by_provider(
        self,
        provider: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据提供方获取凭证列表。

        Args:
            provider: 提供方/来源
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            凭证列表
        """
        return await self.repo.get_by_provider(
            provider=provider,
            skip=skip,
            limit=limit,
        )

    async def search_by_username(
        self,
        username: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据用户名搜索凭证。

        Args:
            username: 用户名（模糊匹配）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的凭证列表
        """
        return await self.repo.search_by_username(
            username=username,
            skip=skip,
            limit=limit,
        )

    async def search_by_email(
        self,
        email: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据电子邮箱搜索凭证。

        Args:
            email: 电子邮箱（模糊匹配）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的凭证列表
        """
        return await self.repo.search_by_email(
            email=email,
            skip=skip,
            limit=limit,
        )

    async def get_credentials_by_validation_result(
        self,
        validation_result: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据验证结果获取凭证列表。

        Args:
            validation_result: 验证结果（VALID/INVALID/UNKNOWN）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            凭证列表
        """
        return await self.repo.get_by_validation_result(
            validation_result=validation_result,
            skip=skip,
            limit=limit,
        )

    async def get_valid_credentials(self, skip: int = 0, limit: int = 100):
        """获取有效凭证列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            有效凭证列表
        """
        return await self.repo.get_valid_credentials(skip=skip, limit=limit)

    async def paginate_credentials(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters,
    ) -> Page:
        """分页查询凭证列表。

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 过滤条件（cred_type、provider、validation_result、scope_policy等）

        Returns:
            分页结果
        """
        return await self.repo.paginate(
            page=page,
            page_size=page_size,
            **filters,
        )

    async def update_credential(self, id: UUID, data: CredentialUpdate):
        """更新凭证信息。

        Args:
            id: 凭证UUID
            data: 更新数据

        Returns:
            更新后的凭证对象

        Raises:
            NotFoundError: 当凭证不存在时
        """
        credential = await self.repo.get_by_id(id)
        if credential is None:
            raise NotFoundError(
                resource_type="Credential",
                resource_id=str(id),
            )

        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(id, **update_data)

    async def delete_credential(self, id: UUID):
        """软删除凭证（标记为已删除，不物理删除）。

        Args:
            id: 凭证UUID

        Raises:
            NotFoundError: 当凭证不存在时
        """
        credential = await self.repo.get_by_id(id)
        if credential is None:
            raise NotFoundError(
                resource_type="Credential",
                resource_id=str(id),
            )
        await self.repo.soft_delete(id)
