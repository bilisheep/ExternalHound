"""
Service资产的Service层。

负责服务资产的业务逻辑，包括自动识别HTTP服务和资产分类。
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.common import Page
from app.repositories.assets.service import ServiceRepository
from app.schemas.assets.service import ServiceCreate, ServiceUpdate
from app.utils.external_id import generate_service_external_id


class ServiceService:
    """服务资产的业务逻辑服务。"""

    # HTTP相关端口和服务名称
    HTTP_PORTS = {80, 443, 8080, 8443, 8000, 8888, 9000, 3000, 5000}
    HTTP_SERVICE_NAMES = {"http", "https", "http-proxy", "http-alt", "websocket"}
    HTTP_PRODUCTS = {"apache", "nginx", "iis", "tomcat", "lighttpd", "caddy"}

    # 资产分类映射
    CATEGORY_MAPPING = {
        # WEB服务
        "WEB": {
            "ports": {80, 443, 8080, 8443, 8000, 8888, 9000, 3000, 5000},
            "services": {"http", "https", "http-proxy", "http-alt", "websocket"},
            "products": {"apache", "nginx", "iis", "tomcat", "lighttpd", "caddy"},
        },
        # 数据库服务
        "DATABASE": {
            "ports": {3306, 5432, 1433, 1521, 27017, 6379, 5984, 9200, 9042},
            "services": {
                "mysql",
                "postgresql",
                "mssql",
                "oracle",
                "mongodb",
                "redis",
                "couchdb",
                "elasticsearch",
                "cassandra",
            },
            "products": {
                "mysql",
                "postgresql",
                "microsoft sql server",
                "oracle",
                "mongodb",
                "redis",
                "couchdb",
                "elasticsearch",
            },
        },
        # 中间件服务
        "MIDDLEWARE": {
            "ports": set(),
            "services": {"jboss", "weblogic", "websphere", "wildfly"},
            "products": {"jboss", "weblogic", "websphere", "wildfly", "glassfish"},
        },
        # 缓存服务
        "CACHE": {
            "ports": {6379, 11211, 7001},
            "services": {"redis", "memcached"},
            "products": {"redis", "memcached"},
        },
        # 消息队列服务
        "MESSAGE_QUEUE": {
            "ports": {5672, 61616, 9092, 4222},
            "services": {"amqp", "activemq", "kafka", "nats"},
            "products": {"rabbitmq", "activemq", "kafka", "nats"},
        },
        # FTP服务
        "FTP": {
            "ports": {21, 22, 990},
            "services": {"ftp", "sftp", "ftps"},
            "products": {"vsftpd", "proftpd", "filezilla"},
        },
        # SSH服务
        "SSH": {
            "ports": {22},
            "services": {"ssh"},
            "products": {"openssh"},
        },
        # DNS服务
        "DNS": {
            "ports": {53},
            "services": {"dns"},
            "products": {"bind", "dnsmasq"},
        },
        # MAIL服务
        "MAIL": {
            "ports": {25, 110, 143, 465, 587, 993, 995},
            "services": {"smtp", "pop3", "imap", "smtps", "imaps", "pop3s"},
            "products": {"postfix", "sendmail", "exim", "dovecot"},
        },
    }

    def __init__(self, db: AsyncSession):
        """初始化服务。

        Args:
            db: 数据库会话
        """
        self.db = db
        self.repo = ServiceRepository(db)

    def _detect_is_http(
        self, port: int, service_name: str | None, product: str | None
    ) -> bool:
        """自动检测是否为HTTP/HTTPS服务。

        Args:
            port: 端口号
            service_name: 服务名称
            product: 产品名称

        Returns:
            是否为HTTP服务
        """
        # 检查端口
        if port in self.HTTP_PORTS:
            return True

        # 检查服务名称
        if service_name and service_name.lower() in self.HTTP_SERVICE_NAMES:
            return True

        # 检查产品名称
        if product:
            product_lower = product.lower()
            if any(http_prod in product_lower for http_prod in self.HTTP_PRODUCTS):
                return True

        return False

    def _detect_asset_category(
        self, port: int, service_name: str | None, product: str | None
    ) -> str | None:
        """自动检测资产分类。

        Args:
            port: 端口号
            service_name: 服务名称
            product: 产品名称

        Returns:
            资产分类（如果能识别）
        """
        service_lower = service_name.lower() if service_name else ""
        product_lower = product.lower() if product else ""

        # 遍历所有分类，按优先级匹配
        for category, criteria in self.CATEGORY_MAPPING.items():
            # 检查服务名称（优先级最高）
            if service_lower and service_lower in criteria["services"]:
                return category

            # 检查产品名称
            if product_lower:
                for prod_keyword in criteria["products"]:
                    if prod_keyword in product_lower:
                        return category

            # 检查端口号（优先级最低）
            if port in criteria["ports"]:
                return category

        return None

    async def create_service(self, data: ServiceCreate):
        """创建服务，自动判断是否为HTTP服务和资产分类。

        Args:
            data: 服务创建数据

        Returns:
            创建的服务对象

        Raises:
            ConflictError: 当external_id已存在时
        """
        external_id = data.external_id.strip() if data.external_id else None
        if not external_id:
            external_id = generate_service_external_id(
                port=data.port,
                protocol=data.protocol,
                service_name=data.service_name,
                product=data.product,
                metadata=data.metadata_,
            )

        # 检查external_id是否已存在
        existing = await self.repo.get_by_external_id(external_id)
        if existing is not None:
            raise ConflictError(
                resource_type="Service",
                field="external_id",
                value=external_id,
            )

        create_data = data.model_dump()
        create_data["external_id"] = external_id

        # 自动判断is_http（仅当未明确指定时）
        # 检查字段是否在原始输入中设置，而不是使用默认值
        if "is_http" not in data.model_fields_set:
            create_data["is_http"] = self._detect_is_http(
                port=create_data["port"],
                service_name=create_data.get("service_name"),
                product=create_data.get("product"),
            )

        # 自动判断asset_category（如果未指定）
        if create_data.get("asset_category") is None:
            create_data["asset_category"] = self._detect_asset_category(
                port=create_data["port"],
                service_name=create_data.get("service_name"),
                product=create_data.get("product"),
            )

        return await self.repo.create(**create_data)

    async def get_service(self, id: UUID):
        """根据UUID获取服务详情。

        Args:
            id: 服务UUID

        Returns:
            服务对象

        Raises:
            NotFoundError: 当服务不存在时
        """
        service = await self.repo.get_by_id(id)
        if service is None:
            raise NotFoundError(
                resource_type="Service",
                resource_id=str(id),
            )
        return service

    async def get_service_by_external_id(self, external_id: str):
        """根据业务ID获取服务详情。

        Args:
            external_id: 业务唯一标识

        Returns:
            服务对象

        Raises:
            NotFoundError: 当服务不存在时
        """
        service = await self.repo.get_by_external_id(external_id)
        if service is None:
            raise NotFoundError(
                resource_type="Service",
                resource_id=external_id,
            )
        return service

    async def get_services_by_port(
        self,
        port: int,
        protocol: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据端口号获取服务列表。

        Args:
            port: 端口号
            protocol: 协议类型（可选）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            服务列表
        """
        return await self.repo.get_by_port(
            port=port,
            protocol=protocol,
            skip=skip,
            limit=limit,
        )

    async def get_services_by_name(
        self,
        service_name: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据服务名称获取服务列表。

        Args:
            service_name: 服务名称
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            服务列表
        """
        return await self.repo.get_by_service_name(
            service_name=service_name,
            skip=skip,
            limit=limit,
        )

    async def get_http_services(self, skip: int = 0, limit: int = 100):
        """获取所有HTTP/HTTPS服务列表。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            HTTP/HTTPS服务列表
        """
        return await self.repo.get_http_services(skip=skip, limit=limit)

    async def search_by_product(
        self,
        product: str,
        version: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据产品名称和版本搜索服务。

        Args:
            product: 产品名称（模糊匹配）
            version: 版本号（可选）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的服务列表
        """
        return await self.repo.search_by_product(
            product=product,
            version=version,
            skip=skip,
            limit=limit,
        )

    async def get_services_by_category(
        self,
        asset_category: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """根据资产分类获取服务列表。

        Args:
            asset_category: 资产分类
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配分类的服务列表
        """
        return await self.repo.get_by_asset_category(
            asset_category=asset_category,
            skip=skip,
            limit=limit,
        )

    async def get_high_risk_services(
        self,
        risk_threshold: float = 7.0,
        skip: int = 0,
        limit: int = 100,
    ):
        """获取高风险服务列表。

        Args:
            risk_threshold: 风险评分阈值（默认7.0）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            高风险服务列表
        """
        return await self.repo.get_high_risk_services(
            risk_threshold=risk_threshold,
            skip=skip,
            limit=limit,
        )

    async def paginate_services(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters,
    ) -> Page:
        """分页查询服务列表。

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 过滤条件（port、protocol、is_http、asset_category、scope_policy等）

        Returns:
            分页结果
        """
        return await self.repo.paginate(
            page=page,
            page_size=page_size,
            **filters,
        )

    async def update_service(self, id: UUID, data: ServiceUpdate):
        """更新服务信息，自动重新判断is_http和asset_category（如果相关字段被修改）。

        Args:
            id: 服务UUID
            data: 更新数据

        Returns:
            更新后的服务对象

        Raises:
            NotFoundError: 当服务不存在时
        """
        service = await self.repo.get_by_id(id)
        if service is None:
            raise NotFoundError(
                resource_type="Service",
                resource_id=str(id),
            )

        update_data = data.model_dump(exclude_unset=True)

        # 如果更新了port、service_name或product，自动重新判断is_http
        if any(
            key in update_data for key in ["port", "service_name", "product"]
        ) and "is_http" not in update_data:
            port = update_data.get("port", service.port)
            service_name = update_data.get("service_name", service.service_name)
            product = update_data.get("product", service.product)
            update_data["is_http"] = self._detect_is_http(port, service_name, product)

        # 如果更新了port、service_name或product，且未指定asset_category，自动重新判断
        if (
            any(key in update_data for key in ["port", "service_name", "product"])
            and "asset_category" not in update_data
        ):
            port = update_data.get("port", service.port)
            service_name = update_data.get("service_name", service.service_name)
            product = update_data.get("product", service.product)
            detected_category = self._detect_asset_category(
                port, service_name, product
            )
            if detected_category is not None:
                update_data["asset_category"] = detected_category

        return await self.repo.update(id, **update_data)

    async def delete_service(self, id: UUID):
        """软删除服务（标记为已删除，不物理删除）。

        Args:
            id: 服务UUID

        Raises:
            NotFoundError: 当服务不存在时
        """
        service = await self.repo.get_by_id(id)
        if service is None:
            raise NotFoundError(
                resource_type="Service",
                resource_id=str(id),
            )
        await self.repo.soft_delete(id)
