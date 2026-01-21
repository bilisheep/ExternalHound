"""
Relationship schema definitions.

Defines Pydantic models for relationship API requests and responses,
including validation rules for the 13 relationship types.
"""

from datetime import datetime
from uuid import UUID
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, model_validator


class NodeType(str, Enum):
    """Asset node types in the graph."""

    ORGANIZATION = "Organization"
    DOMAIN = "Domain"
    IP = "IP"
    NETBLOCK = "Netblock"
    SERVICE = "Service"
    CERTIFICATE = "Certificate"
    CLIENT_APPLICATION = "ClientApplication"
    CREDENTIAL = "Credential"


class RelationshipType(str, Enum):
    """
    Relationship types between assets.

    Organized into four categories:
    - Ownership: SUBSIDIARY, OWNS_NETBLOCK, OWNS_ASSET, OWNS_DOMAIN
    - Topology: CONTAINS, SUBDOMAIN
    - Resolution: RESOLVES_TO, HISTORY_RESOLVES_TO, ISSUED_TO
    - Service: HOSTS_SERVICE, ROUTES_TO, UPSTREAM, COMMUNICATES
    """

    # Ownership relationships
    SUBSIDIARY = "SUBSIDIARY"
    OWNS_NETBLOCK = "OWNS_NETBLOCK"
    OWNS_ASSET = "OWNS_ASSET"
    OWNS_DOMAIN = "OWNS_DOMAIN"

    # Topology relationships
    CONTAINS = "CONTAINS"
    SUBDOMAIN = "SUBDOMAIN"

    # Resolution relationships
    RESOLVES_TO = "RESOLVES_TO"
    HISTORY_RESOLVES_TO = "HISTORY_RESOLVES_TO"
    ISSUED_TO = "ISSUED_TO"

    # Service relationships
    HOSTS_SERVICE = "HOSTS_SERVICE"
    ROUTES_TO = "ROUTES_TO"
    UPSTREAM = "UPSTREAM"
    COMMUNICATES = "COMMUNICATES"


# Relationship type validation rules: (source_type, target_type)
RELATIONSHIP_RULES: dict[RelationshipType, tuple[NodeType, NodeType]] = {
    # Ownership
    RelationshipType.SUBSIDIARY: (NodeType.ORGANIZATION, NodeType.ORGANIZATION),
    RelationshipType.OWNS_NETBLOCK: (NodeType.ORGANIZATION, NodeType.NETBLOCK),
    RelationshipType.OWNS_ASSET: (NodeType.ORGANIZATION, NodeType.IP),
    RelationshipType.OWNS_DOMAIN: (NodeType.ORGANIZATION, NodeType.DOMAIN),
    # Topology
    RelationshipType.CONTAINS: (NodeType.NETBLOCK, NodeType.IP),
    RelationshipType.SUBDOMAIN: (NodeType.DOMAIN, NodeType.DOMAIN),
    # Resolution
    RelationshipType.RESOLVES_TO: (NodeType.DOMAIN, NodeType.IP),
    RelationshipType.HISTORY_RESOLVES_TO: (NodeType.IP, NodeType.DOMAIN),
    RelationshipType.ISSUED_TO: (NodeType.CERTIFICATE, NodeType.DOMAIN),
    # Service
    RelationshipType.HOSTS_SERVICE: (NodeType.IP, NodeType.SERVICE),
    RelationshipType.ROUTES_TO: (NodeType.DOMAIN, NodeType.SERVICE),
    RelationshipType.UPSTREAM: (NodeType.SERVICE, NodeType.SERVICE),
    RelationshipType.COMMUNICATES: (
        NodeType.CLIENT_APPLICATION,
        NodeType.SERVICE,
    ),
}


class RelationshipCreate(BaseModel):
    """
    Create relationship payload.

    Validates that source and target types match the relationship type rules.
    """

    source_external_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Source node external id",
        examples=["org:123", "domain:example.com", "ip:1.2.3.4"],
    )
    source_type: NodeType = Field(
        ...,
        description="Source node type",
    )
    target_external_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Target node external id",
        examples=["org:456", "domain:sub.example.com", "ip:5.6.7.8"],
    )
    target_type: NodeType = Field(
        ...,
        description="Target node type",
    )
    relation_type: RelationshipType = Field(
        ...,
        description="Relationship type",
    )
    edge_key: str = Field(
        default="default",
        max_length=255,
        description="Disambiguation key for multiple edges of same type",
        examples=["default", "primary", "2024-01-01"],
    )
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Relationship properties (e.g., percent, record_type, first_seen)",
        examples=[
            {"percent": 100.0, "type": "WhollyOwned"},
            {"record_type": "A", "last_seen": "2024-01-01"},
        ],
    )
    created_by: str | None = Field(
        None,
        max_length=100,
        description="Creator identifier",
    )

    @model_validator(mode="after")
    def validate_relationship(self) -> "RelationshipCreate":
        """
        Validate that source and target types match the relationship type rules.

        Raises:
            ValueError: If source/target types don't match the relationship type.
        """
        expected = RELATIONSHIP_RULES.get(self.relation_type)
        if expected and (self.source_type, self.target_type) != expected:
            raise ValueError(
                f"Invalid source/target types for {self.relation_type}: "
                f"expected {expected[0].value} -> {expected[1].value}, "
                f"got {self.source_type.value} -> {self.target_type.value}"
            )
        return self

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "source_external_id": "org:123",
                "source_type": "Organization",
                "target_external_id": "domain:example.com",
                "target_type": "Domain",
                "relation_type": "OWNS_DOMAIN",
                "edge_key": "default",
                "properties": {"source": "ICP", "confidence": 0.95},
                "created_by": "admin",
            }
        },
    )


class RelationshipUpdate(BaseModel):
    """
    Update relationship payload.

    Only properties can be updated; source, target, and type are immutable.
    """

    properties: dict[str, Any] | None = Field(
        None,
        description="Relationship properties to update",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "properties": {"confidence": 0.99, "verified_at": "2024-01-15"}
            }
        },
    )


class RelationshipRead(BaseModel):
    """
    Relationship response model.

    Includes all relationship fields plus audit metadata.
    """

    id: UUID = Field(..., description="Relationship UUID")
    source_external_id: str = Field(..., description="Source node external id")
    source_type: NodeType = Field(..., description="Source node type")
    target_external_id: str = Field(..., description="Target node external id")
    target_type: NodeType = Field(..., description="Target node type")
    relation_type: RelationshipType = Field(..., description="Relationship type")
    edge_key: str = Field(..., description="Disambiguation key")
    properties: dict[str, Any] = Field(..., description="Relationship properties")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str | None = Field(None, description="Creator identifier")
    is_deleted: bool = Field(False, description="Soft deleted flag")
    deleted_at: datetime | None = Field(None, description="Deletion timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "source_external_id": "org:123",
                "source_type": "Organization",
                "target_external_id": "domain:example.com",
                "target_type": "Domain",
                "relation_type": "OWNS_DOMAIN",
                "edge_key": "default",
                "properties": {"source": "ICP", "confidence": 0.95},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin",
                "is_deleted": False,
                "deleted_at": None,
            }
        },
    )


class PathDirection(str, Enum):
    """Path traversal direction for graph queries."""

    OUT = "OUT"
    IN = "IN"
    BOTH = "BOTH"


class RelationshipPathQuery(BaseModel):
    """
    Relationship path query request.

    Used to find paths between two nodes in the graph database.
    """

    source_external_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Source node business ID",
    )
    target_external_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Target node business ID",
    )
    source_type: NodeType | None = Field(None, description="Source node type")
    target_type: NodeType | None = Field(None, description="Target node type")
    relation_types: list[RelationshipType] | None = Field(
        None,
        description="Filter by relationship types",
    )
    direction: PathDirection = Field(
        PathDirection.BOTH,
        description="Path traversal direction",
    )
    min_depth: int = Field(1, ge=1, description="Minimum path length")
    max_depth: int = Field(4, ge=1, description="Maximum path length")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of paths")

    @model_validator(mode="after")
    def validate_depth(self) -> "RelationshipPathQuery":
        """Validate that max_depth is >= min_depth."""
        if self.max_depth < self.min_depth:
            raise ValueError("max_depth must be >= min_depth")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_external_id": "org:123",
                "target_external_id": "ip:1.2.3.4",
                "relation_types": ["OWNS_ASSET", "RESOLVES_TO"],
                "direction": "BOTH",
                "min_depth": 1,
                "max_depth": 4,
                "limit": 20,
            }
        },
    )


class GraphNode(BaseModel):
    """Graph node model for path query results."""

    id: str = Field(..., description="Node ID")
    labels: list[str] = Field(default_factory=list, description="Node labels")
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Node properties",
    )


class GraphRelationship(BaseModel):
    """Graph relationship model for path query results."""

    id: str | None = Field(None, description="Relationship ID")
    type: str = Field(..., description="Relationship type")
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Relationship properties",
    )


class RelationshipPathRead(BaseModel):
    """Relationship path response model."""

    nodes: list[GraphNode] = Field(..., description="Path nodes")
    relationships: list[GraphRelationship] = Field(
        ...,
        description="Path relationships",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nodes": [
                    {
                        "id": "org:123",
                        "labels": ["Organization"],
                        "properties": {"name": "Example Corp"},
                    },
                    {
                        "id": "ip:1.2.3.4",
                        "labels": ["IP"],
                        "properties": {"address": "1.2.3.4"},
                    },
                ],
                "relationships": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "type": "OWNS_ASSET",
                        "properties": {"confidence": 0.95},
                    }
                ],
            }
        },
    )
