"""
Neo4j connection manager.

Provides async driver lifecycle and basic Cypher helpers for managing
graph database operations.
"""

import logging
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jManager:
    """
    Neo4j connection manager.

    Manages the lifecycle of Neo4j async driver and provides helper methods
    for common graph operations.
    """

    def __init__(self) -> None:
        """Initialize the Neo4j manager."""
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """
        Initialize the Neo4j driver.

        Raises:
            RuntimeError: If driver is already initialized.
        """
        if self._driver is not None:
            logger.warning("Neo4j driver already initialized")
            return

        self._driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_pool_size=50,
            connection_acquisition_timeout=60,
        )
        logger.info("Neo4j driver initialized: %s", settings.NEO4J_URI)

    async def close(self) -> None:
        """Close the Neo4j driver and release resources."""
        if self._driver is None:
            logger.warning("Neo4j driver not initialized")
            return

        await self._driver.close()
        self._driver = None
        logger.info("Neo4j driver closed")

    @property
    def driver(self) -> AsyncDriver:
        """
        Return the initialized driver.

        Returns:
            AsyncDriver: The Neo4j async driver instance.

        Raises:
            RuntimeError: If driver is not initialized.
        """
        if self._driver is None:
            raise RuntimeError(
                "Neo4j driver not initialized. Call connect() first."
            )
        return self._driver

    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return result data.

        Args:
            query: Cypher query string.
            parameters: Query parameters.

        Returns:
            List of result records as dictionaries.

        Raises:
            RuntimeError: If driver is not initialized.
            Exception: If query execution fails.
        """
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

    async def merge_node(
        self,
        label: str,
        node_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """
        Merge a node by id and update its properties.

        Uses MERGE to create node if it doesn't exist or update if it does.

        Args:
            label: Node label (e.g., "Organization", "IP").
            node_id: Unique node identifier.
            properties: Node properties to set.

        Raises:
            RuntimeError: If driver is not initialized.
            Exception: If merge operation fails.
        """
        query = f"""
        MERGE (n:{label} {{id: $node_id}})
        SET n += $properties
        RETURN n
        """
        await self.execute_query(
            query,
            {"node_id": node_id, "properties": properties or {}},
        )

    async def merge_relationship(
        self,
        source_label: str,
        source_id: str,
        rel_type: str,
        target_label: str,
        target_id: str,
        rel_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """
        Merge a relationship by id and update its properties.

        Creates source and target nodes if they don't exist, then creates
        or updates the relationship between them.

        Args:
            source_label: Source node label.
            source_id: Source node id.
            rel_type: Relationship type (e.g., "OWNS_DOMAIN").
            target_label: Target node label.
            target_id: Target node id.
            rel_id: Unique relationship identifier.
            properties: Relationship properties to set.

        Raises:
            RuntimeError: If driver is not initialized.
            Exception: If merge operation fails.
        """
        query = f"""
        MERGE (a:{source_label} {{id: $source_id}})
        MERGE (b:{target_label} {{id: $target_id}})
        MERGE (a)-[r:{rel_type} {{id: $rel_id}}]->(b)
        SET r += $properties
        RETURN r
        """
        await self.execute_query(
            query,
            {
                "source_id": source_id,
                "target_id": target_id,
                "rel_id": rel_id,
                "properties": properties or {},
            },
        )

    async def delete_relationship(self, rel_id: str) -> None:
        """
        Delete a relationship by id.

        Args:
            rel_id: Unique relationship identifier.

        Raises:
            RuntimeError: If driver is not initialized.
            Exception: If delete operation fails.
        """
        query = """
        MATCH ()-[r {id: $rel_id}]-()
        DELETE r
        """
        await self.execute_query(query, {"rel_id": rel_id})


# Global Neo4j manager instance
neo4j_manager = Neo4jManager()


async def get_neo4j() -> Neo4jManager:
    """
    Dependency to provide Neo4j manager.

    Returns:
        Neo4jManager: The global Neo4j manager instance.
    """
    return neo4j_manager
