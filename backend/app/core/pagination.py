"""
通用分页工具

提供统一的分页功能，支持任何SQLAlchemy查询。
"""

from __future__ import annotations

from typing import Generic, TypeVar, Sequence
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import Page


T = TypeVar("T")


async def paginate(
    db: AsyncSession,
    query: Select[tuple[T]],
    page: int = 1,
    page_size: int = 20
) -> Page[T]:
    """
    对SQLAlchemy查询进行分页

    此函数接受一个SQLAlchemy Select语句，执行分页查询并返回分页结果。
    它会自动计算总记录数、总页数等分页信息。

    Args:
        db: 异步数据库会话
        query: SQLAlchemy Select查询语句
        page: 页码，从1开始，默认为1
        page_size: 每页记录数，默认为20

    Returns:
        Page对象，包含分页数据和元信息

    Raises:
        HTTPException: 当page或page_size小于1时

    Example:
        ```python
        from sqlalchemy import select
        from app.models.postgres.organization import Organization

        # 构建查询
        query = select(Organization).where(Organization.is_deleted == False)

        # 执行分页
        result = await paginate(db, query, page=1, page_size=20)

        # 访问结果
        print(f"Total: {result.total}")
        for org in result.items:
            print(org.name)
        ```
    """
    # 参数验证
    if page < 1:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="Page number must be >= 1"
        )
    if page_size < 1:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="Page size must be >= 1"
        )

    # 计算偏移量
    offset = (page - 1) * page_size

    # 构建计数查询
    # 从原始查询中提取FROM子句和WHERE子句，用于计数
    count_query = select(func.count()).select_from(query.alias())

    # 执行计数查询
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 执行分页查询
    paginated_query = query.offset(offset).limit(page_size)
    result = await db.execute(paginated_query)
    items: Sequence[T] = result.scalars().all()

    # 构建分页响应
    return Page(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def paginate_with_count(
    db: AsyncSession,
    query: Select[tuple[T]],
    total: int,
    page: int = 1,
    page_size: int = 20
) -> Page[T]:
    """
    使用预先计算的总数进行分页

    当总数已经通过其他方式获得时，可以使用此函数避免重复的COUNT查询。
    这在某些复杂查询场景下可以提高性能。

    Args:
        db: 异步数据库会话
        query: SQLAlchemy Select查询语句
        total: 预先计算的总记录数
        page: 页码，从1开始，默认为1
        page_size: 每页记录数，默认为20

    Returns:
        Page对象，包含分页数据和元信息

    Raises:
        HTTPException: 当page或page_size小于1时
    """
    # 参数验证
    if page < 1:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="Page number must be >= 1"
        )
    if page_size < 1:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="Page size must be >= 1"
        )

    # 计算偏移量和总页数
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 执行分页查询
    paginated_query = query.offset(offset).limit(page_size)
    result = await db.execute(paginated_query)
    items: Sequence[T] = result.scalars().all()

    # 构建分页响应
    return Page(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
