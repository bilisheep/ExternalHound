"""
Relationship Neo4j sync service.

Handles synchronization of relationships between PostgreSQL and Neo4j,
and provides graph path query capabilities.
"""

import logging
from typing import Any

from app.db.neo4j import Neo4jManager
from app.models.postgres.relationship import Relationship
from app.schemas.relationships.relationship import (
    PathDirection,
    RelationshipPathQuery,
    RelationshipPathRead,
    GraphNode,
    GraphRelationship,
)

logger = logging.getLogger(__name__)


class RelationshipGraphService:
    """
    Relationship graph synchronization service.

    Syncs relationships from PostgreSQL to Neo4j and provides path query
    capabilities leveraging Neo4j's graph traversal algorithms.
    """

    def __init__(self, neo4j: Neo4jManager) -> None:
        """
        Initialize the graph service.

        Args:
            neo4j: Neo4j manager instance
        """
        self.neo4j = neo4j

    async def upsert_relationship(self, relationship: Relationship) -> None:
        """
        Sync relationship to Neo4j (create or update).

        Creates or updates the relationship in Neo4j with all properties
        from the PostgreSQL record.

        Args:
            relationship: Relationship model instance from PostgreSQL

        Raises:
            RuntimeError: If Neo4j driver is not initialized
        """
        properties = self._build_relationship_properties(relationship)

        try:
            await self.neo4j.merge_relationship(
                source_label=relationship.source_type,
                source_id=relationship.source_external_id,
                rel_type=relationship.relation_type,
                target_label=relationship.target_type,
                target_id=relationship.target_external_id,
                rel_id=str(relationship.id),
                properties=properties,
            )
            logger.debug(
                "Synced relationship %s to Neo4j",
                relationship.id,
            )
        except Exception as exc:
            logger.error(
                "Failed to sync relationship %s to Neo4j: %s",
                relationship.id,
                exc,
            )
            raise

    async def delete_relationship(self, relationship_id: str) -> None:
        """
        Delete relationship from Neo4j.

        Args:
            relationship_id: Relationship UUID as string

        Raises:
            RuntimeError: If Neo4j driver is not initialized
        """
        try:
            await self.neo4j.delete_relationship(relationship_id)
            logger.debug(
                "Deleted relationship %s from Neo4j",
                relationship_id,
            )
        except Exception as exc:
            logger.error(
                "Failed to delete relationship %s from Neo4j: %s",
                relationship_id,
                exc,
            )
            raise

    async def delete_node_relationships(
        self,
        node_type: str,
        external_id: str,
    ) -> None:
        """
        Delete all relationships attached to a node in Neo4j.

        Args:
            node_type: Node label
            external_id: Node business id

        Raises:
            RuntimeError: If Neo4j driver is not initialized
        """
        try:
            await self.neo4j.delete_node_relationships(node_type, external_id)
            logger.debug(
                "Deleted relationships for node %s:%s from Neo4j",
                node_type,
                external_id,
            )
        except Exception as exc:
            logger.error(
                "Failed to delete relationships for node %s:%s from Neo4j: %s",
                node_type,
                external_id,
                exc,
            )
            raise

    async def find_paths(
        self,
        query: RelationshipPathQuery,
    ) -> list[RelationshipPathRead]:
        """
        Find paths between nodes in Neo4j.

        Args:
            query: Path query parameters

        Returns:
            List of path results containing nodes and relationships

        Raises:
            RuntimeError: If Neo4j driver is not initialized
        """
        cypher, params = self._build_path_query(query)

        try:
            records = await self.neo4j.execute_query(cypher, params)
            return [
                self._parse_path_record(record)
                for record in records
            ]
        except Exception as exc:
            logger.error("Failed to query paths in Neo4j: %s", exc)
            raise

    def _build_path_query(
        self,
        query: RelationshipPathQuery,
    ) -> tuple[str, dict[str, Any]]:
        """
        构建路径查询的Cypher语句。

        Args:
            query: 路径查询参数

        Returns:
            (cypher_query, parameters)元组
        """
        # 构建源节点和目标节点标签
        source_label = f":{query.source_type.value}" if query.source_type else ""
        target_label = f":{query.target_type.value}" if query.target_type else ""

        # 构建关系类型过滤（直接在模式中指定，而非WHERE子句）
        rel_type_pattern = ""
        if query.relation_types:
            # 将关系类型列表转换为 :TYPE1|TYPE2|TYPE3 格式
            types_str = "|".join([rel.value for rel in query.relation_types])
            rel_type_pattern = f":{types_str}"

        # 构建深度范围
        depth_pattern = f"{query.min_depth}..{query.max_depth}"

        # 根据方向构建关系模式（将类型过滤直接嵌入模式）
        if query.direction == PathDirection.OUT:
            rel_pattern = f"-[rels{rel_type_pattern}*{depth_pattern}]->"
        elif query.direction == PathDirection.IN:
            rel_pattern = f"<-[rels{rel_type_pattern}*{depth_pattern}]-"
        else:  # BOTH
            rel_pattern = f"-[rels{rel_type_pattern}*{depth_pattern}]-"

        # 构建Cypher查询（不再需要WHERE子句过滤关系类型）
        cypher = f"""
        MATCH p = (s{source_label} {{id: $source_id}}){rel_pattern}(t{target_label} {{id: $target_id}})
        RETURN
            [n IN nodes(p) | {{id: n.id, labels: labels(n), properties: properties(n)}}] AS nodes,
            [r IN relationships(p) | {{id: r.id, type: type(r), properties: properties(r)}}] AS relationships
        LIMIT $limit
        """

        params = {
            "source_id": query.source_external_id,
            "target_id": query.target_external_id,
            "limit": query.limit,
        }

        return cypher, params

    def _parse_path_record(self, record: dict[str, Any]) -> RelationshipPathRead:
        """
        Parse Neo4j path record into response model.

        Args:
            record: Neo4j query result record

        Returns:
            RelationshipPathRead model
        """
        nodes = [
            GraphNode(
                id=node["id"],
                labels=node["labels"],
                properties=node["properties"],
            )
            for node in record.get("nodes", [])
        ]

        relationships = [
            GraphRelationship(
                id=rel.get("id"),
                type=rel["type"],
                properties=rel.get("properties", {}),
            )
            for rel in record.get("relationships", [])
        ]

        return RelationshipPathRead(
            nodes=nodes,
            relationships=relationships,
        )

    def _build_relationship_properties(
        self,
        relationship: Relationship,
    ) -> dict[str, Any]:
        """
        Build properties dict for Neo4j from PostgreSQL relationship.

        Args:
            relationship: Relationship model instance

        Returns:
            Properties dictionary for Neo4j
        """
        properties = dict(relationship.properties or {})
        properties.update(
            {
                "edge_key": relationship.edge_key,
                "source_external_id": relationship.source_external_id,
                "source_type": relationship.source_type,
                "target_external_id": relationship.target_external_id,
                "target_type": relationship.target_type,
                "created_at": relationship.created_at.isoformat(),
                "updated_at": relationship.updated_at.isoformat(),
            }
        )

        if relationship.created_by:
            properties["created_by"] = relationship.created_by

        return properties
