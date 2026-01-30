"""
Relationship API路由

提供关系管理与图路径查询的RESTful API端点。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.db.neo4j import Neo4jManager, get_neo4j
from app.db.postgres import get_db
from app.schemas.common import SuccessResponse
from app.schemas.relationships.relationship import (
    NodeType,
    RelationshipType,
    RelationshipCreate,
    RelationshipUpdate,
    RelationshipRead,
    RelationshipPathQuery,
    RelationshipPathRead,
)
from app.services.relationships.relationship import RelationshipService


router = APIRouter(prefix="/relationships", tags=["Relationships"])


@router.post(
    "",
    response_model=RelationshipRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建关系",
)
async def create_relationship(
    data: RelationshipCreate,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> RelationshipRead:
    """
    创建新的资产关系（写入PostgreSQL并同步到Neo4j）。

    - **source_external_id**: 源节点业务ID（必填）
    - **source_type**: 源节点类型（必填）
    - **target_external_id**: 目标节点业务ID（必填）
    - **target_type**: 目标节点类型（必填）
    - **relation_type**: 关系类型（必填）
    - **edge_key**: 边唯一键（默认default）
    - **properties**: 关系属性（可选）
    - **created_by**: 创建者（可选）

    **关系类型验证**：系统会自动验证源节点和目标节点类型是否符合关系类型的规则。
    例如：OWNS_DOMAIN 关系要求源节点为 Organization，目标节点为 Domain。

    **重复关系**：如果存在相同key的关系，会返回冲突错误。
    """
    service = RelationshipService(db, neo4j)
    relationship = await service.create_relationship(data)
    await db.commit()
    return RelationshipRead.model_validate(relationship)


@router.get(
    "/{id}",
    response_model=RelationshipRead,
    summary="获取关系详情",
)
async def get_relationship(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> RelationshipRead:
    """
    根据UUID获取关系详情。
    """
    service = RelationshipService(db, neo4j)
    relationship = await service.get_relationship(id)
    return RelationshipRead.model_validate(relationship)


@router.get(
    "",
    response_model=Page[RelationshipRead],
    summary="分页查询关系列表",
)
async def list_relationships(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    source_external_id: str | None = Query(None, description="源节点业务ID"),
    source_type: NodeType | None = Query(None, description="源节点类型"),
    target_external_id: str | None = Query(None, description="目标节点业务ID"),
    target_type: NodeType | None = Query(None, description="目标节点类型"),
    relation_type: RelationshipType | None = Query(None, description="关系类型"),
    edge_key: str | None = Query(None, description="边唯一键"),
    include_deleted: bool = Query(False, description="是否包含已删除的关系"),
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> Page[RelationshipRead]:
    """
    分页查询关系列表，支持多种过滤条件。

    **过滤条件**：
    - 可按源节点ID、类型过滤
    - 可按目标节点ID、类型过滤
    - 可按关系类型过滤
    - 可按边唯一键过滤
    - 可选择是否包含已删除的关系（硬删除后通常为空）

    **使用场景**：
    - 查询某个节点的所有出边：传入source_external_id
    - 查询某个节点的所有入边：传入target_external_id
    - 查询特定类型的所有关系：传入relation_type
    """
    service = RelationshipService(db, neo4j)
    result = await service.paginate_relationships(
        page=page,
        page_size=page_size,
        source_external_id=source_external_id,
        source_type=source_type,
        target_external_id=target_external_id,
        target_type=target_type,
        relation_type=relation_type,
        edge_key=edge_key,
        include_deleted=include_deleted,
    )

    return Page(
        items=[
            RelationshipRead.model_validate(relationship)
            for relationship in result.items
        ],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.put(
    "/{id}",
    response_model=RelationshipRead,
    summary="更新关系属性",
)
async def update_relationship(
    id: UUID,
    data: RelationshipUpdate,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> RelationshipRead:
    """
    更新关系的属性字段（properties）。

    **注意**：
    - 只能更新properties字段
    - 源节点、目标节点和关系类型不可修改
    - 新属性会与现有属性合并（新属性覆盖同名旧属性）
    - 更新会同步到Neo4j
    """
    service = RelationshipService(db, neo4j)
    relationship = await service.update_relationship(id, data)
    await db.commit()
    return RelationshipRead.model_validate(relationship)


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="删除关系",
)
async def delete_relationship(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> SuccessResponse:
    """
    删除关系。

    **删除策略**：
    - PostgreSQL：硬删除（物理删除）
    - Neo4j：硬删除（直接删除边）
    """
    service = RelationshipService(db, neo4j)
    await service.delete_relationship(id)
    await db.commit()
    return SuccessResponse(message="Relationship deleted successfully")


@router.post(
    "/paths",
    response_model=list[RelationshipPathRead],
    summary="图路径查询",
)
async def query_paths(
    data: RelationshipPathQuery,
    db: AsyncSession = Depends(get_db),
    neo4j: Neo4jManager = Depends(get_neo4j),
) -> list[RelationshipPathRead]:
    """
    在Neo4j图数据库中查询两个节点之间的路径。

    **查询参数**：
    - **source_external_id**: 起始节点业务ID（必填）
    - **target_external_id**: 目标节点业务ID（必填）
    - **source_type**: 起始节点类型（可选，用于提高查询效率）
    - **target_type**: 目标节点类型（可选，用于提高查询效率）
    - **relation_types**: 限定关系类型列表（可选）
    - **direction**: 路径方向 OUT/IN/BOTH（默认BOTH）
    - **min_depth**: 最小跳数（默认1）
    - **max_depth**: 最大跳数（默认4）
    - **limit**: 返回路径数量上限（默认20，最大100）

    **使用场景**：
    - 分析资产归属链：从IP追溯到组织
    - 发现攻击路径：从外网服务到内网资产
    - 关系探索：查看两个资产之间的所有关联

    **性能建议**：
    - 指定source_type和target_type可提高查询速度
    - 限制max_depth避免查询超时
    - 使用relation_types过滤减少结果数量
    """
    service = RelationshipService(db, neo4j)
    return await service.find_paths(data)
