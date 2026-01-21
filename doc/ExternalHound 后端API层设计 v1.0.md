# ExternalHound 后端API层设计 v1.0

**文档信息**
- 版本：v1.0
- 日期：2026-01-16
- 层次定位：后端API层（Backend API Layer）
- 状态：设计方案

---

## 目录

1. [设计概述](#1-设计概述)
2. [技术栈选型](#2-技术栈选型)
3. [项目结构](#3-项目结构)
4. [数据库连接层](#4-数据库连接层)
5. [认证与授权（后续版本预留）](#5-认证与授权后续版本预留)
6. [核心API端点](#6-核心api端点)
7. [导入API设计](#7-导入api设计)
8. [查询与搜索API](#8-查询与搜索api)
9. [错误处理与日志](#9-错误处理与日志)
10. [测试策略](#10-测试策略)

---

## 1. 设计概述

### 1.1 层次职责

后端API层是 ExternalHound 系统的**核心业务逻辑层**，负责：

1. **RESTful API 服务**：提供标准化的 HTTP API 接口
2. **业务逻辑处理**：资产管理、关系查询、数据导入等核心功能
3. **数据访问控制**：后续版本考虑（v1.0 不包含用户与权限）
4. **数据聚合**：整合 PostgreSQL 和 Neo4j 的查询结果
5. **后台处理**：文件导入与解析等耗时作业

### 1.2 设计原则

1. **RESTful 规范**：遵循 REST API 设计最佳实践
2. **分层架构**：Controller → Service → Repository 清晰分层
3. **依赖注入**：使用 FastAPI 的依赖注入系统
4. **异步优先**：充分利用 Python asyncio 提高性能
5. **类型安全**：使用 Pydantic 进行数据验证和序列化
6. **可测试性**：每层都可独立测试

### 1.3 核心功能模块

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│  Authentication (JWT，后续版本预留)                      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Assets     │  │   Import     │  │   Query      │ │
│  │   Module     │  │   Module     │  │   Module     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Graph      │  │   Parser     │  │   Report     │ │
│  │   Module     │  │   Module     │  │   Module     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────┤
│              Service Layer (Business Logic)             │
├─────────────────────────────────────────────────────────┤
│            Repository Layer (Data Access)               │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │   PostgreSQL         │  │   Neo4j              │   │
│  │   (Metadata)         │  │   (Relationships)    │   │
│  └──────────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 技术栈选型

### 2.1 核心框架

- **FastAPI 0.109+**：现代化的 Python Web 框架
  - 自动生成 OpenAPI 文档
  - 原生支持异步
  - 基于 Pydantic 的数据验证
  - 高性能（基于 Starlette 和 Uvicorn）

### 2.2 数据库驱动

- **asyncpg**：PostgreSQL 异步驱动（高性能）
- **SQLAlchemy 2.0+**：ORM 框架（支持异步）
- **neo4j-driver**：Neo4j 官方 Python 驱动

### 2.3 认证与安全

- **python-jose**：JWT 令牌生成和验证
- **passlib**：密码哈希（bcrypt）
- **python-multipart**：文件上传支持

### 2.4 缓存

- **Redis**：缓存查询结果，提升性能（可选）

### 2.5 其他依赖

- **Pydantic 2.0+**：数据验证和序列化
- **httpx**：异步 HTTP 客户端
- **python-dotenv**：环境变量管理
- **loguru**：日志记录
- **pytest + pytest-asyncio**：测试框架

---

## 3. 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置管理
│   ├── dependencies.py            # 全局依赖注入
│   │
│   ├── api/                       # API 路由层
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # 认证相关 API
│   │   │   ├── organizations.py  # 组织管理 API
│   │   │   ├── assets.py         # 资产管理 API
│   │   │   ├── imports.py        # 数据导入 API
│   │   │   ├── queries.py        # 查询搜索 API
│   │   │   ├── graphs.py         # 图谱查询 API
│   │   │   └── reports.py        # 报告生成 API
│   │   └── deps.py               # API 层依赖
│   │
│   ├── core/                      # 核心功能
│   │   ├── __init__.py
│   │   ├── security.py           # 安全相关（JWT、密码）
│   │   ├── exceptions.py         # 自定义异常
│   │   └── middleware.py         # 中间件
│   │
│   ├── db/                        # 数据库层
│   │   ├── __init__.py
│   │   ├── postgres.py           # PostgreSQL 连接
│   │   ├── neo4j.py              # Neo4j 连接
│   │   └── redis.py              # Redis 连接
│   │
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── domain/               # 领域模型（ORM）
│   │   │   ├── __init__.py
│   │   │   ├── organization.py
│   │   │   ├── netblock.py
│   │   │   ├── domain.py
│   │   │   ├── ip.py
│   │   │   ├── certificate.py
│   │   │   ├── service.py
│   │   │   └── application.py
│   │   └── schemas/              # API 模式（Pydantic）
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── organization.py
│   │       ├── asset.py
│   │       ├── import_log.py
│   │       └── query.py
│   │
│   ├── repositories/              # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py               # 基础仓储类
│   │   ├── organization_repo.py
│   │   ├── asset_repo.py
│   │   ├── graph_repo.py         # Neo4j 查询
│   │   └── import_repo.py
│   │
│   ├── services/                  # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── organization_service.py
│   │   ├── asset_service.py
│   │   ├── import_service.py
│   │   ├── query_service.py
│   │   └── graph_service.py
│   │
│   ├── parsers/                   # 数据解析器（从导入层移植）
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── nmap_parser.py
│   │   ├── masscan_parser.py
│   │   ├── subfinder_parser.py
│   │   └── nuclei_parser.py
│   │
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── logger.py
│       ├── validators.py
│       └── helpers.py
│
├── tests/                         # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_repositories/
│
├── alembic/                       # 数据库迁移
│   ├── versions/
│   └── env.py
│
├── requirements.txt               # 依赖列表
├── .env.example                   # 环境变量示例
├── pytest.ini                     # pytest 配置
└── README.md                      # 项目说明
```

---

## 4. 数据库连接层

### 4.1 PostgreSQL 连接管理

```python
# app/db/postgres.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# ORM 基类
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """初始化数据库（创建表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
```

### 4.2 Neo4j 连接管理

```python
# app/db/neo4j.py
from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import Optional, Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jManager:
    """Neo4j 连接管理器"""

    def __init__(self):
        self.driver: Optional[AsyncDriver] = None

    async def connect(self):
        """建立连接"""
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
        logger.info("Neo4j connection established")

    async def close(self):
        """关闭连接"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行 Cypher 查询"""
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def merge_node(
        self,
        label: str,
        properties: Dict[str, Any],
        unique_key: str = "id"
    ):
        """合并节点（存在则更新，不存在则创建）"""
        query = f"""
        MERGE (n:{label} {{{unique_key}: $unique_value}})
        SET n += $properties
        RETURN n
        """
        await self.execute_query(query, {
            "unique_value": properties[unique_key],
            "properties": properties
        })

    async def merge_relationship(
        self,
        source_label: str,
        source_id: str,
        rel_type: str,
        target_label: str,
        target_id: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """合并关系"""
        query = f"""
        MATCH (a:{source_label} {{id: $source_id}})
        MATCH (b:{target_label} {{id: $target_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        RETURN r
        """
        await self.execute_query(query, {
            "source_id": source_id,
            "target_id": target_id,
            "properties": properties or {}
        })

# 全局实例
neo4j_manager = Neo4jManager()

async def get_neo4j() -> Neo4jManager:
    """获取 Neo4j 管理器（依赖注入）"""
    return neo4j_manager
```

### 4.3 Redis 连接管理

```python
# app/db/redis.py
from redis.asyncio import Redis
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis 连接管理器"""

    def __init__(self):
        self.redis: Optional[Redis] = None

    async def connect(self):
        """建立连接"""
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
            max_connections=50
        )
        logger.info("Redis connection established")

    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        return await self.redis.get(key)

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ):
        """设置值"""
        await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str):
        """删除键"""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.redis.exists(key) > 0

# 全局实例
redis_manager = RedisManager()

async def get_redis() -> RedisManager:
    """获取 Redis 管理器（依赖注入）"""
    return redis_manager
```

### 4.4 配置管理

```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "ExternalHound API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL 配置
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "externalhound_pg_pass"
    POSTGRES_DB: str = "externalhound"

    @property
    def POSTGRES_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "externalhound_neo4j_pass"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "externalhound_redis_pass"
    REDIS_DB: int = 0

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 文件上传配置
    UPLOAD_DIR: str = "/tmp/externalhound/uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()

settings = get_settings()
```

---

## 5. 认证与授权（后续版本预留）

> 说明：v1.0 不包含用户与权限控制，本节作为后续版本参考。

### 5.1 JWT 令牌管理

```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
```

### 5.2 用户认证依赖

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.postgres import get_db
from app.core.security import decode_token
from app.models.schemas.auth import TokenPayload, User
from app.repositories.user_repo import UserRepository

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（依赖注入）"""
    token = credentials.credentials

    # 解码令牌
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证令牌类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # 获取用户信息
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级管理员用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
```

### 5.3 认证 API 端点

```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from app.db.postgres import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.models.schemas.auth import Token, TokenRefresh, UserCreate, UserResponse
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_in)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # 创建令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_refresh: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    payload = decode_token(token_refresh.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    # 创建新令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout():
    """用户登出（客户端删除令牌）"""
    return {"message": "Successfully logged out"}
```

## 6. 核心API端点

### 6.1 资产管理 API

```python
# app/api/v1/assets.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.postgres import get_db
from app.api.deps import get_current_user
from app.models.schemas.auth import User
from app.models.schemas.asset import (
    IPAssetResponse,
    DomainAssetResponse,
    ServiceAssetResponse,
    AssetListResponse,
    AssetFilter
)
from app.services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/ips", response_model=AssetListResponse[IPAssetResponse])
async def list_ips(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scope_policy: Optional[str] = None,
    is_cloud: Optional[bool] = None,
    country_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 IP 资产列表"""
    asset_service = AssetService(db)
    result = await asset_service.list_ips(
        page=page,
        page_size=page_size,
        scope_policy=scope_policy,
        is_cloud=is_cloud,
        country_code=country_code
    )
    return result

@router.get("/ips/{ip_address}", response_model=IPAssetResponse)
async def get_ip_detail(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 IP 资产详情"""
    asset_service = AssetService(db)
    ip_asset = await asset_service.get_ip_by_address(ip_address)

    if not ip_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP asset not found"
        )

    return ip_asset

@router.get("/domains", response_model=AssetListResponse[DomainAssetResponse])
async def list_domains(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    root_domain: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取域名资产列表"""
    asset_service = AssetService(db)
    result = await asset_service.list_domains(
        page=page,
        page_size=page_size,
        root_domain=root_domain,
        is_resolved=is_resolved
    )
    return result

@router.get("/domains/{domain_name}", response_model=DomainAssetResponse)
async def get_domain_detail(
    domain_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取域名资产详情"""
    asset_service = AssetService(db)
    domain_asset = await asset_service.get_domain_by_name(domain_name)

    if not domain_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain asset not found"
        )

    return domain_asset

@router.get("/services", response_model=AssetListResponse[ServiceAssetResponse])
async def list_services(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    port: Optional[int] = None,
    is_http: Optional[bool] = None,
    asset_category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取服务资产列表"""
    asset_service = AssetService(db)
    result = await asset_service.list_services(
        page=page,
        page_size=page_size,
        port=port,
        is_http=is_http,
        asset_category=asset_category
    )
    return result

@router.get("/services/{service_id}", response_model=ServiceAssetResponse)
async def get_service_detail(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取服务资产详情"""
    asset_service = AssetService(db)
    service_asset = await asset_service.get_service_by_id(service_id)

    if not service_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service asset not found"
        )

    return service_asset

@router.patch("/ips/{ip_address}/scope")
async def update_ip_scope(
    ip_address: str,
    scope_policy: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 IP 资产范围策略"""
    asset_service = AssetService(db)
    result = await asset_service.update_ip_scope(ip_address, scope_policy)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP asset not found"
        )

    return {"message": "Scope policy updated successfully"}

@router.delete("/ips/{ip_address}")
async def delete_ip(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除 IP 资产"""
    asset_service = AssetService(db)
    result = await asset_service.delete_ip(ip_address)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP asset not found"
        )

    return {"message": "IP asset deleted successfully"}
```

### 6.2 组织管理 API

```python
# app/api/v1/organizations.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.postgres import get_db
from app.api.deps import get_current_user
from app.models.schemas.auth import User
from app.models.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建组织"""
    org_service = OrganizationService(db)
    organization = await org_service.create_organization(org_in, current_user.id)
    return organization

@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_primary: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织列表"""
    org_service = OrganizationService(db)
    result = await org_service.list_organizations(
        page=page,
        page_size=page_size,
        is_primary=is_primary
    )
    return result

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织详情"""
    org_service = OrganizationService(db)
    organization = await org_service.get_organization_by_id(org_id)

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return organization

@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_update: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新组织信息"""
    org_service = OrganizationService(db)
    organization = await org_service.update_organization(org_id, org_update)

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return organization

@router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除组织"""
    org_service = OrganizationService(db)
    result = await org_service.delete_organization(org_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return {"message": "Organization deleted successfully"}

@router.get("/{org_id}/assets/summary")
async def get_organization_assets_summary(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织资产统计摘要"""
    org_service = OrganizationService(db)
    summary = await org_service.get_assets_summary(org_id)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return summary
```

---

## 7. 导入API设计

### 7.1 文件上传与导入

```python
# app/api/v1/imports.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.postgres import get_db
from app.api.deps import get_current_user
from app.models.schemas.auth import User
from app.models.schemas.import_log import ImportLogResponse, ImportListResponse
from app.services.import_service import ImportService
from app.tasks.import_tasks import import_file_task
import os
import uuid

router = APIRouter(prefix="/imports", tags=["Imports"])

@router.post("/upload", response_model=ImportLogResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_and_import(
    file: UploadFile = File(...),
    parser_type: Optional[str] = Form(None),
    organization_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件并启动导入任务"""
    # 验证文件大小
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 100MB limit"
        )

    # 保存文件
    import_service = ImportService(db)
    file_id = str(uuid.uuid4())
    file_path = await import_service.save_upload_file(file, file_id)

    # 创建导入日志
    import_log = await import_service.create_import_log(
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        parser_type=parser_type,
        created_by=str(current_user.id)
    )

    # 启动异步导入任务
    import_file_task.delay(
        import_id=str(import_log.id),
        file_path=file_path,
        parser_type=parser_type,
        organization_id=organization_id,
        created_by=str(current_user.id)
    )

    return import_log

@router.get("", response_model=ImportListResponse)
async def list_imports(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导入记录列表"""
    import_service = ImportService(db)
    result = await import_service.list_imports(
        page=page,
        page_size=page_size,
        status=status
    )
    return result

@router.get("/{import_id}", response_model=ImportLogResponse)
async def get_import_detail(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导入记录详情"""
    import_service = ImportService(db)
    import_log = await import_service.get_import_by_id(import_id)

    if not import_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import log not found"
        )

    return import_log

@router.delete("/{import_id}")
async def delete_import(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除导入记录"""
    import_service = ImportService(db)
    result = await import_service.delete_import(import_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import log not found"
        )

    return {"message": "Import log deleted successfully"}
```

### 7.2 导入处理（同步或后台任务）

```python
# app/api/v1/imports.py
from fastapi import BackgroundTasks
from app.services.import_service import ImportService

@router.post("/", response_model=ImportLogResponse)
async def create_import(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建导入任务并后台处理"""
    import_service = ImportService(db)
    import_log = await import_service.create_import(...)

    background_tasks.add_task(
        import_service.process_import,
        import_log.id,
        file_path,
        parser_type,
        organization_id,
        current_user.username
    )

    return import_log
```

---

## 8. 查询与搜索API

### 8.1 全文搜索 API

```python
# app/api/v1/queries.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.postgres import get_db
from app.db.neo4j import get_neo4j, Neo4jManager
from app.api.deps import get_current_user
from app.models.schemas.auth import User
from app.models.schemas.query import (
    SearchRequest,
    SearchResponse,
    GraphQueryRequest,
    GraphQueryResponse
)
from app.services.query_service import QueryService

router = APIRouter(prefix="/queries", tags=["Queries"])

@router.post("/search", response_model=SearchResponse)
async def search_assets(
    search_req: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """全文搜索资产"""
    query_service = QueryService(db)
    result = await query_service.search_assets(
        keyword=search_req.keyword,
        asset_types=search_req.asset_types,
        page=search_req.page,
        page_size=search_req.page_size
    )
    return result

@router.get("/suggest")
async def search_suggestions(
    keyword: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索建议（自动补全）"""
    query_service = QueryService(db)
    suggestions = await query_service.get_search_suggestions(keyword, limit)
    return {"suggestions": suggestions}

@router.post("/graph", response_model=GraphQueryResponse)
async def query_graph(
    graph_req: GraphQueryRequest,
    neo4j: Neo4jManager = Depends(get_neo4j),
    current_user: User = Depends(get_current_user)
):
    """图谱查询"""
    query_service = QueryService(None, neo4j)
    result = await query_service.query_graph(
        start_node_id=graph_req.start_node_id,
        relationship_types=graph_req.relationship_types,
        max_depth=graph_req.max_depth
    )
    return result

@router.get("/graph/path")
async def find_shortest_path(
    source_id: str = Query(...),
    target_id: str = Query(...),
    neo4j: Neo4jManager = Depends(get_neo4j),
    current_user: User = Depends(get_current_user)
):
    """查找最短路径"""
    query_service = QueryService(None, neo4j)
    path = await query_service.find_shortest_path(source_id, target_id)

    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No path found between nodes"
        )

    return {"path": path}

@router.get("/statistics/overview")
async def get_statistics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取统计概览"""
    query_service = QueryService(db)
    stats = await query_service.get_statistics_overview()
    return stats
```

### 8.2 高级过滤查询

```python
# app/services/query_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional, Dict, Any
from app.models.domain.ip import IPAsset
from app.models.domain.domain import DomainAsset
from app.models.domain.service import ServiceAsset
from app.db.neo4j import Neo4jManager

class QueryService:
    """查询服务"""

    def __init__(self, db: Optional[AsyncSession], neo4j: Optional[Neo4jManager] = None):
        self.db = db
        self.neo4j = neo4j

    async def search_assets(
        self,
        keyword: str,
        asset_types: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """全文搜索资产"""
        results = {
            "ips": [],
            "domains": [],
            "services": [],
            "total": 0
        }

        if not asset_types or "ip" in asset_types:
            # 搜索 IP
            stmt = select(IPAsset).where(
                or_(
                    IPAsset.address.ilike(f"%{keyword}%"),
                    IPAsset.metadata["hostnames"].astext.ilike(f"%{keyword}%")
                )
            ).limit(page_size).offset((page - 1) * page_size)

            result = await self.db.execute(stmt)
            results["ips"] = result.scalars().all()

        if not asset_types or "domain" in asset_types:
            # 搜索域名
            stmt = select(DomainAsset).where(
                DomainAsset.name.ilike(f"%{keyword}%")
            ).limit(page_size).offset((page - 1) * page_size)

            result = await self.db.execute(stmt)
            results["domains"] = result.scalars().all()

        if not asset_types or "service" in asset_types:
            # 搜索服务
            stmt = select(ServiceAsset).where(
                or_(
                    ServiceAsset.product.ilike(f"%{keyword}%"),
                    ServiceAsset.banner.ilike(f"%{keyword}%")
                )
            ).limit(page_size).offset((page - 1) * page_size)

            result = await self.db.execute(stmt)
            results["services"] = result.scalars().all()

        results["total"] = len(results["ips"]) + len(results["domains"]) + len(results["services"])

        return results

    async def query_graph(
        self,
        start_node_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """图谱查询"""
        if relationship_types:
            rel_filter = "|".join(relationship_types)
            query = f"""
            MATCH path = (start {{id: $start_id}})-[r:{rel_filter}*1..{max_depth}]-(end)
            RETURN path
            LIMIT 100
            """
        else:
            query = f"""
            MATCH path = (start {{id: $start_id}})-[*1..{max_depth}]-(end)
            RETURN path
            LIMIT 100
            """

        result = await self.neo4j.execute_query(query, {"start_id": start_node_id})

        # 提取节点和关系
        nodes = []
        edges = []
        node_ids = set()

        for record in result:
            path = record["path"]
            for node in path.nodes:
                if node.id not in node_ids:
                    nodes.append({
                        "id": node["id"],
                        "label": list(node.labels)[0],
                        "properties": dict(node)
                    })
                    node_ids.add(node.id)

            for rel in path.relationships:
                edges.append({
                    "source": rel.start_node["id"],
                    "target": rel.end_node["id"],
                    "type": rel.type,
                    "properties": dict(rel)
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
```

---

## 9. 错误处理与日志

### 9.1 自定义异常

```python
# app/core/exceptions.py
from fastapi import HTTPException, status

class ExternalHoundException(Exception):
    """基础异常类"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AssetNotFoundException(ExternalHoundException):
    """资产未找到异常"""
    def __init__(self, asset_type: str, asset_id: str):
        message = f"{asset_type} with id {asset_id} not found"
        super().__init__(message, status_code=404)

class ImportException(ExternalHoundException):
    """导入异常"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class ParserException(ExternalHoundException):
    """解析器异常"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class AuthenticationException(ExternalHoundException):
    """认证异常"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class AuthorizationException(ExternalHoundException):
    """授权异常"""
    def __init__(self, message: str = "Not enough permissions"):
        super().__init__(message, status_code=403)
```

### 9.2 全局异常处理器

```python
# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import ExternalHoundException
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ExternalHound API",
    version="1.0.0",
    description="External Attack Surface Management System"
)

@app.exception_handler(ExternalHoundException)
async def externalhound_exception_handler(request: Request, exc: ExternalHoundException):
    """处理自定义异常"""
    logger.error(f"ExternalHound exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证异常"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }
    )
```

### 9.3 日志配置

```python
# app/utils/logger.py
import logging
import sys
from loguru import logger
from app.config import settings

class InterceptHandler(logging.Handler):
    """拦截标准日志并转发到 loguru"""
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO" if not settings.DEBUG else "DEBUG",
        colorize=True
    )

    # 添加文件输出
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )

    # 添加错误日志文件
    logger.add(
        "logs/error.log",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR"
    )

    # 拦截标准库日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # 拦截 uvicorn 日志
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]

    return logger
```

### 9.4 请求日志中间件

```python
# app/core/middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time
import uuid

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始
        start_time = time.time()
        logger.info(
            f"Request started | {request.method} {request.url.path} | "
            f"Request ID: {request_id} | Client: {request.client.host}"
        )

        # 处理请求
        response = await call_next(request)

        # 记录请求结束
        process_time = time.time() - start_time
        logger.info(
            f"Request completed | {request.method} {request.url.path} | "
            f"Status: {response.status_code} | Duration: {process_time:.3f}s | "
            f"Request ID: {request_id}"
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        return response
```

---

## 10. 测试策略

### 10.1 单元测试

```python
# tests/test_services/test_asset_service.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.asset_service import AssetService
from app.models.domain.ip import IPAsset

@pytest.mark.asyncio
async def test_get_ip_by_address(db_session: AsyncSession):
    """测试根据地址获取 IP 资产"""
    # 准备测试数据
    ip_asset = IPAsset(
        address="192.168.1.1",
        version=4,
        is_internal=True
    )
    db_session.add(ip_asset)
    await db_session.commit()

    # 执行测试
    asset_service = AssetService(db_session)
    result = await asset_service.get_ip_by_address("192.168.1.1")

    # 验证结果
    assert result is not None
    assert result.address == "192.168.1.1"
    assert result.version == 4
    assert result.is_internal is True

@pytest.mark.asyncio
async def test_list_ips_with_filters(db_session: AsyncSession):
    """测试带过滤条件的 IP 列表查询"""
    asset_service = AssetService(db_session)
    result = await asset_service.list_ips(
        page=1,
        page_size=20,
        is_cloud=True
    )

    assert result["total"] >= 0
    assert "items" in result
    assert "page" in result
```

### 10.2 集成测试

```python
# tests/test_api/test_assets.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_list_ips_endpoint(async_client: AsyncClient, auth_headers: dict):
    """测试 IP 列表 API 端点"""
    response = await async_client.get(
        "/api/v1/assets/ips",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data

@pytest.mark.asyncio
async def test_get_ip_detail_endpoint(async_client: AsyncClient, auth_headers: dict):
    """测试 IP 详情 API 端点"""
    response = await async_client.get(
        "/api/v1/assets/ips/192.168.1.1",
        headers=auth_headers
    )

    if response.status_code == 200:
        data = response.json()
        assert "address" in data
        assert "version" in data
    elif response.status_code == 404:
        assert response.json()["detail"] == "IP asset not found"
```

### 10.3 测试配置

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.db.postgres import Base, get_db
from app.core.security import create_access_token

# 测试数据库 URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:test@localhost:5432/externalhound_test"

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """创建数据库会话"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def async_client(db_session):
    """创建异步 HTTP 客户端"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    """创建认证头"""
    access_token = create_access_token(data={"sub": "test-user-id"})
    return {"Authorization": f"Bearer {access_token}"}
```

---

## 11. 总结

### 11.1 设计亮点

1. **异步优先**：全面使用 asyncio 提高并发性能
2. **分层架构**：清晰的 Controller → Service → Repository 分层
3. **依赖注入**：充分利用 FastAPI 的依赖注入系统
4. **类型安全**：使用 Pydantic 进行数据验证和序列化
5. **任务处理**：导入解析可按需使用后台任务
6. **完善的错误处理**：统一的异常处理和日志记录
7. **可测试性**：每层都可独立测试

### 11.2 实施建议

1. **优先实现核心功能**：认证、资产管理、数据导入
2. **完善测试覆盖**：单元测试 + 集成测试覆盖率 > 80%
3. **性能监控**：使用 APM 工具监控 API 性能
4. **API 文档**：利用 FastAPI 自动生成的 OpenAPI 文档
5. **安全加固**：HTTPS、CORS、速率限制、SQL 注入防护

### 11.3 下一步工作

1. 实现前端界面
2. 完善导入与解析流程
3. 添加报告生成功能
4. 实现实时通知系统
5. 性能优化和压力测试

---

**文档版本**：v1.0
**最后更新**：2026-01-16
**维护者**：ExternalHound 开发团队
