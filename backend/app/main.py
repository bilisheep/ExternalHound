"""
FastAPI应用主入口

初始化FastAPI应用，配置中间件、路由和异常处理。
"""

from contextlib import asynccontextmanager

import json

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.config import settings
from app.core.exceptions import AppError
from app.db.postgres import db_manager
from app.db.neo4j import neo4j_manager
from app.services.projects.config import ensure_default_project_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化数据库连接，关闭时清理资源。
    """
    # 启动时初始化数据库
    db_manager.init_engine()
    await ensure_default_project_config()
    await neo4j_manager.connect()
    yield
    # 关闭时清理资源
    await neo4j_manager.close()
    await db_manager.close_engine()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="渗透测试数据管理平台 - 资产与关系管理API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# 全局异常处理器
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    处理自定义应用异常

    Args:
        request: 请求对象
        exc: 应用异常

    Returns:
        JSON响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    处理请求验证错误

    Args:
        request: 请求对象
        exc: 验证异常

    Returns:
        JSON响应
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": json.loads(json.dumps(exc.errors(), default=str))
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    处理HTTP异常

    Args:
        request: 请求对象
        exc: HTTP异常

    Returns:
        JSON响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "details": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    处理未捕获的异常

    Args:
        request: 请求对象
        exc: 异常

    Returns:
        JSON响应
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "Internal server error",
            "details": str(exc) if settings.DEBUG else None
        }
    )


# 注册API路由
app.include_router(api_router, prefix="/api")


# 健康检查端点
@app.get("/health", tags=["Health"])
async def health_check():
    """
    健康检查端点

    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# 根路径
@app.get("/", tags=["Root"])
async def root():
    """
    根路径

    Returns:
        欢迎信息
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }
