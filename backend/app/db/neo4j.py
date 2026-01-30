"""
Neo4j connection manager.

Provides async driver lifecycle and basic Cypher helpers for managing
graph database operations.
"""

import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.config import settings
from app.db.postgres import load_project_config
from app.utils.projects import (
    DEFAULT_PROJECT_ID,
    PROJECT_HEADER,
    resolve_project_id,
)
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Neo4jConnection:
    uri: str
    user: str
    password: str


CURRENT_NEO4J_CONNECTION: ContextVar[Neo4jConnection | None] = ContextVar(
    "current_neo4j_connection",
    default=None,
)


class Neo4jManager:
    """
    Neo4j connection manager.

    Manages the lifecycle of Neo4j async driver and provides helper methods
    for common graph operations.
    """

    def __init__(self) -> None:
        """Initialize the Neo4j manager."""
        self._drivers: dict[Neo4jConnection, AsyncDriver] = {}

    async def connect(self) -> None:
        """
        Initialize the default Neo4j driver.
        """
        default_connection = self._default_connection()
        if default_connection in self._drivers:
            logger.warning("Neo4j driver already initialized")
            return
        self._drivers[default_connection] = self._create_driver(default_connection)
        logger.info("Neo4j driver initialized: %s", default_connection.uri)

    async def close(self) -> None:
        """Close the Neo4j driver and release resources."""
        if not self._drivers:
            logger.warning("Neo4j driver not initialized")
            return
        for driver in self._drivers.values():
            await driver.close()
        self._drivers.clear()
        logger.info("Neo4j drivers closed")

    @property
    def driver(self) -> AsyncDriver:
        """
        Return the driver for the current project connection.

        Falls back to the default Neo4j connection if none is set.
        """
        connection = CURRENT_NEO4J_CONNECTION.get() or self._default_connection()
        driver = self._drivers.get(connection)
        if driver is None:
            driver = self._create_driver(connection)
            self._drivers[connection] = driver
        return driver

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
            Exception: If query execution fails.
        """
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

    def ensure_connection(self, connection: Neo4jConnection) -> None:
        if connection in self._drivers:
            return
        self._drivers[connection] = self._create_driver(connection)

    def _default_connection(self) -> Neo4jConnection:
        return Neo4jConnection(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
        )

    def _create_driver(self, connection: Neo4jConnection) -> AsyncDriver:
        return AsyncGraphDatabase.driver(
            connection.uri,
            auth=(connection.user, connection.password),
            max_connection_pool_size=50,
            connection_acquisition_timeout=60,
        )

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

    async def delete_node_relationships(self, label: str, node_id: str) -> None:
        """
        Delete all relationships connected to a node.

        Args:
            label: Node label
            node_id: Unique node identifier

        Raises:
            RuntimeError: If driver is not initialized.
            Exception: If delete operation fails.
        """
        query = f"""
        MATCH (n:{label} {{id: $node_id}})-[r]-()
        DELETE r
        """
        await self.execute_query(query, {"node_id": node_id})


# Global Neo4j manager instance
neo4j_manager = Neo4jManager()


async def get_neo4j(request: Request) -> AsyncGenerator[Neo4jManager, None]:
    """
    Dependency to provide Neo4j manager scoped by project.

    Sets the current Neo4j connection based on the project header.
    """
    try:
        project_id = resolve_project_id(request.headers.get(PROJECT_HEADER))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    config_row = await load_project_config(project_id, request)
    if project_id != DEFAULT_PROJECT_ID and not config_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project Neo4j configuration is missing",
        )

    if config_row and any(
        [
            config_row.get("neo4j_uri"),
            config_row.get("neo4j_user"),
            config_row.get("neo4j_password"),
        ]
    ):
        if not all(
            [
                config_row.get("neo4j_uri"),
                config_row.get("neo4j_user"),
                config_row.get("neo4j_password"),
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Neo4j configuration is incomplete",
            )
        connection = Neo4jConnection(
            uri=str(config_row.get("neo4j_uri")),
            user=str(config_row.get("neo4j_user")),
            password=str(config_row.get("neo4j_password")),
        )
    elif project_id != DEFAULT_PROJECT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Neo4j configuration is incomplete",
        )
    else:
        connection = Neo4jConnection(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
        )
    neo4j_manager.ensure_connection(connection)
    token = CURRENT_NEO4J_CONNECTION.set(connection)
    try:
        yield neo4j_manager
    finally:
        CURRENT_NEO4J_CONNECTION.reset(token)
