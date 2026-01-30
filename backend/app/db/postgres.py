"""
PostgreSQL数据库连接管理

提供异步数据库连接、会话管理和ORM基类。
"""

import logging
from dataclasses import dataclass
from typing import AsyncGenerator

from fastapi import HTTPException, Request, status
from sqlalchemy import MetaData, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import declarative_base

from app.config import settings
from app.utils.projects import (
    DEFAULT_POSTGRES_SCHEMA,
    DEFAULT_PROJECT_ID,
    PROJECT_HEADER,
    quote_postgres_identifier,
    postgres_schema_for,
    resolve_project_id,
)


# 配置日志
logger = logging.getLogger(__name__)

# 定义命名约定，用于自动生成约束名称
# 这有助于在数据库迁移时保持一致性
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",  # 索引
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # 唯一约束
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # 检查约束
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # 外键
    "pk": "pk_%(table_name)s"  # 主键
}

# 创建元数据对象，应用命名约定
metadata = MetaData(naming_convention=NAMING_CONVENTION)

# 创建ORM基类
# 所有ORM模型都应继承此类
Base = declarative_base(metadata=metadata)


@dataclass(frozen=True)
class PostgresConnection:
    host: str
    port: int
    user: str
    password: str
    database: str
    sslmode: str | None = None

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class DatabaseManager:
    """
    数据库连接管理器

    负责创建和管理数据库引擎、会话工厂等资源。
    使用单例模式确保全局只有一个数据库连接池。
    """

    def __init__(self) -> None:
        """初始化数据库管理器"""
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._default_connection: PostgresConnection | None = None
        self._engines: dict[PostgresConnection, AsyncEngine] = {}
        self._session_factories: dict[
            PostgresConnection, async_sessionmaker[AsyncSession]
        ] = {}
        self._schema_cache: dict[PostgresConnection, set[str]] = {}

    def init_engine(self) -> None:
        """
        初始化数据库引擎

        创建异步数据库引擎和会话工厂。
        应在应用启动时调用一次。
        """
        if self._engine is not None:
            logger.warning("Database engine already initialized")
            return

        self._default_connection = self._build_default_connection()
        self._engine = self._create_engine(self._default_connection)
        self._session_factory = self._create_session_factory(self._engine)
        self._engines[self._default_connection] = self._engine
        self._session_factories[self._default_connection] = self._session_factory

        logger.info(
            f"Database engine initialized: {settings.POSTGRES_HOST}:"
            f"{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

    async def close_engine(self) -> None:
        """
        关闭数据库引擎

        释放所有数据库连接。
        应在应用关闭时调用。
        """
        if not self._engines:
            logger.warning("Database engine not initialized")
            return

        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._session_factories.clear()
        self._schema_cache.clear()
        self._engine = None
        self._session_factory = None
        self._default_connection = None
        logger.info("Database engines closed")

    @property
    def engine(self) -> AsyncEngine:
        """
        获取数据库引擎

        Returns:
            异步数据库引擎

        Raises:
            RuntimeError: 如果引擎未初始化
        """
        if self._engine is None:
            raise RuntimeError(
                "Database engine not initialized. "
                "Call init_engine() first."
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        获取会话工厂

        Returns:
            异步会话工厂

        Raises:
            RuntimeError: 如果会话工厂未初始化
        """
        if self._session_factory is None:
            raise RuntimeError(
                "Session factory not initialized. "
                "Call init_engine() first."
            )
        return self._session_factory

    def get_session_factory_for(
        self,
        connection: PostgresConnection,
    ) -> async_sessionmaker[AsyncSession]:
        if (
            self._default_connection is not None
            and connection == self._default_connection
            and self._session_factory is not None
        ):
            return self._session_factory

        factory = self._session_factories.get(connection)
        if factory is None:
            engine = self._get_engine_for(connection)
            factory = self._create_session_factory(engine)
            self._session_factories[connection] = factory
        return factory

    def default_connection(self) -> PostgresConnection:
        if self._default_connection is None:
            self._default_connection = self._build_default_connection()
        return self._default_connection

    async def create_tables(self) -> None:
        """
        创建所有数据库表

        根据ORM模型定义创建数据库表。
        注意：生产环境应使用Alembic进行数据库迁移。
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def drop_tables(self) -> None:
        """
        删除所有数据库表

        警告：此操作会删除所有数据，仅用于开发和测试环境。
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")

    async def schema_exists(
        self,
        schema: str,
        connection: PostgresConnection | None = None,
    ) -> bool:
        """
        Check whether the schema exists in the target database.
        """
        connection = connection or self.default_connection()
        schema_cache = self._schema_cache.setdefault(connection, set())
        if schema in schema_cache:
            return True
        if schema == DEFAULT_POSTGRES_SCHEMA:
            schema_cache.add(schema)
            return True
        engine = self._get_engine_for(connection)
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT 1 FROM information_schema.schemata "
                    "WHERE schema_name = :schema"
                ),
                {"schema": schema},
            )
            exists = result.scalar() is not None
        if exists:
            schema_cache.add(schema)
        return exists

    def _build_default_connection(self) -> PostgresConnection:
        return PostgresConnection(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            sslmode=settings.POSTGRES_SSLMODE,
        )

    def _get_engine_for(self, connection: PostgresConnection) -> AsyncEngine:
        if (
            self._default_connection is not None
            and connection == self._default_connection
            and self._engine is not None
        ):
            return self._engine
        engine = self._engines.get(connection)
        if engine is None:
            engine = self._create_engine(connection)
            self._engines[connection] = engine
        return engine

    def _create_session_factory(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    def _create_engine(self, connection: PostgresConnection) -> AsyncEngine:
        connect_args = (
            settings.POSTGRES_CONNECT_ARGS
            if self._default_connection is not None
            and connection == self._default_connection
            else self._connect_args_for(connection)
        )
        return create_async_engine(
            connection.url,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args,
            future=True,
        )

    def _connect_args_for(self, connection: PostgresConnection) -> dict[str, object]:
        sslmode = self._resolve_sslmode(connection)
        if not sslmode:
            return {}
        sslmode = sslmode.lower()
        if sslmode == "disable":
            return {"ssl": False}
        if sslmode in {"require", "verify-ca", "verify-full"}:
            return {"ssl": True}
        return {}

    def _resolve_sslmode(self, connection: PostgresConnection) -> str | None:
        if connection.sslmode:
            return connection.sslmode
        if connection.host in {"localhost", "127.0.0.1", "::1"}:
            return "disable"
        return None


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_config_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取配置数据库会话（始终使用默认连接与public schema）。
    """
    session = db_manager.session_factory()
    await session.execute(text("SET search_path TO public"))
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def load_project_config(
    project_id: str,
    request: Request | None = None,
) -> dict[str, object] | None:
    cached_id = getattr(request.state, "project_config_project_id", None) if request else None
    if cached_id == project_id:
        return getattr(request.state, "project_config", None)

    session = db_manager.session_factory()
    try:
        await session.execute(text("SET search_path TO public"))
        result = await session.execute(
            text(
                "SELECT project_id, postgres_host, postgres_port, postgres_user, "
                "postgres_password, postgres_db, postgres_sslmode, postgres_schema, "
                "neo4j_uri, neo4j_user, neo4j_password "
                "FROM public.project_configs WHERE project_id = :project_id"
            ),
            {"project_id": project_id},
        )
        row = result.mappings().first()
    except SQLAlchemyError as exc:
        logger.warning("Failed to load project config for %s: %s", project_id, exc)
        row = None
    finally:
        await session.close()

    if request is not None:
        request.state.project_config_project_id = project_id
        request.state.project_config = row

    return row


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（依赖注入）

    这是一个FastAPI依赖项，用于在路由处理函数中注入数据库会话。
    会话会在请求结束时自动提交或回滚。

    Yields:
        异步数据库会话

    Example:
        ```python
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession

        @router.get("/organizations")
        async def list_organizations(
            db: AsyncSession = Depends(get_db)
        ):
            # 使用db进行数据库操作
            pass
        ```
    """
    try:
        project_id = resolve_project_id(request.headers.get(PROJECT_HEADER))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    config_row = await load_project_config(project_id, request)
    base_connection = db_manager.default_connection()
    schema_override = (
        str(config_row.get("postgres_schema"))
        if config_row and config_row.get("postgres_schema")
        else None
    )

    postgres_values = [
        config_row.get("postgres_host") if config_row else None,
        config_row.get("postgres_user") if config_row else None,
        config_row.get("postgres_password") if config_row else None,
        config_row.get("postgres_db") if config_row else None,
    ]
    has_postgres_config = any(postgres_values)

    if project_id != DEFAULT_PROJECT_ID and not has_postgres_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project PostgreSQL configuration is missing",
        )

    if has_postgres_config:
        if not all(
            [
                config_row.get("postgres_host"),
                config_row.get("postgres_user"),
                config_row.get("postgres_password"),
                config_row.get("postgres_db"),
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PostgreSQL configuration is incomplete",
            )
        connection = PostgresConnection(
            host=str(config_row.get("postgres_host")),
            port=int(config_row.get("postgres_port") or base_connection.port),
            user=str(config_row.get("postgres_user")),
            password=str(config_row.get("postgres_password")),
            database=str(config_row.get("postgres_db")),
            sslmode=(
                str(config_row.get("postgres_sslmode"))
                if config_row.get("postgres_sslmode")
                else None
            ),
        )
        schema = schema_override or postgres_schema_for(project_id)
    else:
        connection = base_connection
        schema = schema_override or postgres_schema_for(project_id)

    if not await db_manager.schema_exists(schema, connection):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PostgreSQL schema '{schema}' does not exist",
        )
    session_factory = db_manager.get_session_factory_for(connection)
    session = session_factory()
    search_path = (
        quote_postgres_identifier(schema)
        if schema == DEFAULT_POSTGRES_SCHEMA
        else f"{quote_postgres_identifier(schema)}, public"
    )
    await session.execute(text(f"SET search_path TO {search_path}"))
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """
    初始化数据库

    应在应用启动时调用。
    """
    db_manager.init_engine()
    logger.info("Database initialized")


async def close_db() -> None:
    """
    关闭数据库连接

    应在应用关闭时调用。
    """
    await db_manager.close_engine()
    logger.info("Database connection closed")
