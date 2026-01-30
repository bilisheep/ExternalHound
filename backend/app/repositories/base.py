"""
基础Repository类

提供通用的CRUD操作，所有具体的Repository都应继承此类。
"""

from __future__ import annotations

import re
from typing import Generic, TypeVar, Type, Sequence
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.pagination import Page, paginate
from app.db.postgres import Base


ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    基础Repository类

    提供通用的CRUD操作，包括：
    - 创建（create）
    - 读取（get_by_id, get_by_external_id, list_all）
    - 更新（update）
    - 删除（hard_delete/soft_delete，均执行硬删除）
    - 分页查询（paginate）

    查询操作默认过滤is_deleted标记。

    Attributes:
        model: ORM模型类
        db: 数据库会话
    """

    def __init__(self, model: Type[ModelT], db: AsyncSession) -> None:
        """
        初始化Repository

        Args:
            model: ORM模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db

    async def create(self, **kwargs) -> ModelT:
        """
        创建新记录

        Args:
            **kwargs: 模型字段的键值对

        Returns:
            创建的模型实例

        Raises:
            ConflictError: 当唯一约束冲突时
        """
        try:
            instance = self.model(**kwargs)
            self.db.add(instance)
            await self.db.flush()
            await self.db.refresh(instance)
            return instance
        except IntegrityError as e:
            field, value = self._parse_unique_violation(e)
            raise ConflictError(
                resource_type=self.model.__name__,
                field=field,
                value=value,
                details={
                    "original_error": str(e.orig),
                    "constraint_name": getattr(e.orig, "constraint_name", None),
                },
            )

    async def get_by_id(self, id: UUID) -> ModelT | None:
        """
        根据UUID主键获取记录

        Args:
            id: UUID主键

        Returns:
            模型实例，如果不存在或已删除则返回None
        """
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> ModelT | None:
        """
        根据业务唯一标识获取记录

        Args:
            external_id: 业务唯一标识

        Returns:
            模型实例，如果不存在或已删除则返回None
        """
        stmt = select(self.model).where(
            self.model.external_id == external_id,
            self.model.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ModelT]:
        """
        列出所有记录（不包括已删除的）

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            模型实例列表
        """
        stmt = select(self.model).where(
            self.model.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters
    ) -> Page[ModelT]:
        """
        分页查询

        Args:
            page: 页码
            page_size: 每页记录数
            **filters: 额外的过滤条件

        Returns:
            分页结果
        """
        # 构建基础查询
        stmt = select(self.model).where(self.model.is_deleted == False)

        # 应用过滤条件
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        # 执行分页
        return await paginate(self.db, stmt, page, page_size)

    async def update(
        self,
        id: UUID,
        **kwargs
    ) -> ModelT | None:
        """
        更新记录

        Args:
            id: UUID主键
            **kwargs: 要更新的字段键值对

        Returns:
            更新后的模型实例，如果不存在则返回None

        Raises:
            NotFoundError: 当记录不存在时
            ConflictError: 当唯一约束冲突时
        """
        # 先获取记录确保存在
        instance = await self.get_by_id(id)
        if instance is None:
            raise NotFoundError(
                resource_type=self.model.__name__,
                resource_id=str(id)
            )

        # 过滤掉None值和不存在的字段
        update_data = {
            k: v for k, v in kwargs.items()
            if v is not None and hasattr(self.model, k)
        }

        if not update_data:
            return instance

        # 使用ORM实例更新以确保onupdate触发
        try:
            for key, value in update_data.items():
                setattr(instance, key, value)
            await self.db.flush()
            await self.db.refresh(instance)
            return instance
        except IntegrityError as e:
            field, value = self._parse_unique_violation(e)
            raise ConflictError(
                resource_type=self.model.__name__,
                field=field,
                value=value,
                details={
                    "original_error": str(e.orig),
                    "constraint_name": getattr(e.orig, "constraint_name", None),
                },
            )

    async def soft_delete(self, id: UUID) -> bool:
        """
        删除记录（硬删除）

        Args:
            id: UUID主键

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 当记录不存在时
        """
        return await self.hard_delete(id)

    async def hard_delete(self, id: UUID) -> bool:
        """
        硬删除记录（物理删除）

        警告：此操作不可逆，请谨慎使用。

        Args:
            id: UUID主键

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 当记录不存在时
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        if not result.rowcount:
            raise NotFoundError(
                resource_type=self.model.__name__,
                resource_id=str(id),
            )
        return True

    def _parse_unique_violation(self, exc: IntegrityError) -> tuple[str, str]:
        """
        从唯一约束异常中提取字段和值。

        Args:
            exc: IntegrityError异常

        Returns:
            (field, value)元组
        """
        field = "unknown"
        value = "unknown"
        message = str(getattr(exc, "orig", exc))
        match = re.search(r"Key \((?P<field>[^)]+)\)=\((?P<value>[^)]+)\)", message)
        if match:
            field = match.group("field")
            value = match.group("value")
            return field, value

        constraint_name = getattr(exc.orig, "constraint_name", None)
        table_name = getattr(self.model, "__tablename__", None)
        if constraint_name and table_name:
            prefix = f"{table_name}_"
            if constraint_name.startswith(prefix):
                field = constraint_name[len(prefix):]
                if field.endswith("_key"):
                    field = field[:-4]
        return field, value

    async def count(self, **filters) -> int:
        """
        统计记录数

        Args:
            **filters: 过滤条件

        Returns:
            记录总数
        """
        stmt = select(func.count()).select_from(self.model).where(
            self.model.is_deleted == False
        )

        # 应用过滤条件
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def exists(self, **filters) -> bool:
        """
        检查记录是否存在

        Args:
            **filters: 过滤条件

        Returns:
            是否存在
        """
        count = await self.count(**filters)
        return count > 0
