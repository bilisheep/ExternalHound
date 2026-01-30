"""
ClientApplication资产的Service层。

负责客户端应用资产的业务逻辑。
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.db.neo4j import Neo4jManager
from app.schemas.common import Page
from app.repositories.assets.client_application import ClientApplicationRepository
from app.schemas.assets.client_application import (
    ClientApplicationCreate,
    ClientApplicationUpdate,
)
from app.schemas.relationships.relationship import NodeType
from app.services.relationships.relationship import RelationshipService
from app.utils.external_id import generate_client_application_external_id


class ClientApplicationService:
    """客户端应用资产的业务逻辑服务。"""

    def __init__(
        self,
        db: AsyncSession,
        neo4j: Neo4jManager | None = None,
    ):
        """初始化服务。

        Args:
            db: 数据库会话
        """
        self.db = db
        self.repo = ClientApplicationRepository(db)
        self.relationship_service = (
            RelationshipService(db, neo4j) if neo4j else None
        )

    async def create_application(self, data: ClientApplicationCreate):
        """创建客户端应用。

        Args:
            data: 应用创建数据

        Returns:
            创建的应用对象

        Raises:
            ConflictError: 当external_id已存在时
        """
        external_id = data.external_id.strip() if data.external_id else None
        if not external_id:
            external_id = generate_client_application_external_id(
                platform=data.platform,
                package_name=data.package_name,
            )

        # 检查external_id是否已存在
        existing = await self.repo.get_by_external_id(external_id)
        if existing is not None:
            raise ConflictError(
                resource_type="ClientApplication",
                field="external_id",
                value=external_id,
            )

        create_data = data.model_dump()
        create_data["external_id"] = external_id
        return await self.repo.create(**create_data)

    async def get_application(self, id: UUID):
        """根据UUID获取应用详情。

        Args:
            id: 应用UUID

        Returns:
            应用对象

        Raises:
            NotFoundError: 当应用不存在时
        """
        application = await self.repo.get_by_id(id)
        if application is None:
            raise NotFoundError(
                resource_type="ClientApplication",
                resource_id=str(id),
            )
        return application

    async def get_application_by_external_id(self, external_id: str):
        """根据业务ID获取应用详情。

        Args:
            external_id: 业务唯一标识

        Returns:
            应用对象

        Raises:
            NotFoundError: 当应用不存在时
        """
        application = await self.repo.get_by_external_id(external_id)
        if application is None:
            raise NotFoundError(
                resource_type="ClientApplication",
                resource_id=external_id,
            )
        return application

    async def get_applications_by_platform(
        self,
        platform: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据平台类型获取应用列表。

        Args:
            platform: 平台类型
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            应用列表
        """
        return await self.repo.get_by_platform(
            platform=platform,
            skip=skip,
            limit=limit,
        )

    async def get_applications_by_package_name(
        self,
        package_name: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据包名获取应用列表。

        Args:
            package_name: 包名
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            应用列表
        """
        return await self.repo.get_by_package_name(
            package_name=package_name,
            skip=skip,
            limit=limit,
        )

    async def search_by_app_name(
        self,
        app_name: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据应用名称搜索应用。

        Args:
            app_name: 应用名称（模糊匹配）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的应用列表
        """
        return await self.repo.search_by_app_name(
            app_name=app_name,
            skip=skip,
            limit=limit,
        )

    async def get_high_risk_applications(
        self,
        risk_threshold: float = 7.0,
        skip: int = 0,
        limit: int = 100,
    ):
        """获取高风险应用列表。

        Args:
            risk_threshold: 风险评分阈值（默认7.0）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            高风险应用列表
        """
        return await self.repo.get_high_risk_applications(
            risk_threshold=risk_threshold,
            skip=skip,
            limit=limit,
        )

    async def get_applications_by_bundle_id(
        self,
        bundle_id: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据Bundle ID获取应用列表。

        Args:
            bundle_id: Bundle标识符
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            应用列表
        """
        return await self.repo.get_by_bundle_id(
            bundle_id=bundle_id,
            skip=skip,
            limit=limit,
        )

    async def paginate_applications(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters,
    ) -> Page:
        """分页查询应用列表。

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 过滤条件（platform、scope_policy等）

        Returns:
            分页结果
        """
        return await self.repo.paginate(
            page=page,
            page_size=page_size,
            **filters,
        )

    async def update_application(self, id: UUID, data: ClientApplicationUpdate):
        """更新应用信息。

        Args:
            id: 应用UUID
            data: 更新数据

        Returns:
            更新后的应用对象

        Raises:
            NotFoundError: 当应用不存在时
        """
        application = await self.repo.get_by_id(id)
        if application is None:
            raise NotFoundError(
                resource_type="ClientApplication",
                resource_id=str(id),
            )

        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(id, **update_data)

    async def delete_application(self, id: UUID):
        """硬删除应用（物理删除）。

        Args:
            id: 应用UUID

        Raises:
            NotFoundError: 当应用不存在时
        """
        application = await self.repo.get_by_id(id)
        if application is None:
            raise NotFoundError(
                resource_type="ClientApplication",
                resource_id=str(id),
            )
        await self.repo.hard_delete(id)
        if self.relationship_service:
            await self.relationship_service.delete_relationships_for_node(
                external_id=application.external_id,
                node_type=NodeType.CLIENT_APPLICATION,
            )
