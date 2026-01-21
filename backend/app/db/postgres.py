"""
PostgreSQL数据库连接管理

提供异步数据库连接、会话管理和ORM基类。
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import declarative_base

from app.config import settings


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

    def init_engine(self) -> None:
        """
        初始化数据库引擎

        创建异步数据库引擎和会话工厂。
        应在应用启动时调用一次。
        """
        if self._engine is not None:
            logger.warning("Database engine already initialized")
            return

        # 创建异步引擎
        self._engine = create_async_engine(
            settings.POSTGRES_URL,
            echo=settings.DEBUG,  # 在调试模式下打印SQL语句
            pool_size=20,  # 连接池大小
            max_overflow=40,  # 连接池溢出大小
            pool_pre_ping=True,  # 在使用连接前测试连接是否有效
            pool_recycle=3600,  # 连接回收时间（秒）
            connect_args=settings.POSTGRES_CONNECT_ARGS,
            future=True  # 使用SQLAlchemy 2.0风格
        )

        # 创建会话工厂
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,  # 提交后不过期对象
            autocommit=False,  # 禁用自动提交
            autoflush=False  # 禁用自动刷新
        )

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
        if self._engine is None:
            logger.warning("Database engine not initialized")
            return

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        logger.info("Database engine closed")

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


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
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
    session = db_manager.session_factory()
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
