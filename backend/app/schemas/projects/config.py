"""
Project configuration schemas.
"""

from pydantic import BaseModel, Field, ConfigDict


class PostgresConfigUpdate(BaseModel):
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    user: str | None = None
    password: str | None = None
    database: str | None = None
    sslmode: str | None = None
    db_schema: str | None = Field(default=None, alias="schema")

    model_config = ConfigDict(populate_by_name=True)


class Neo4jConfigUpdate(BaseModel):
    uri: str | None = None
    user: str | None = None
    password: str | None = None


class ProjectConfigUpdate(BaseModel):
    postgres: PostgresConfigUpdate | None = None
    neo4j: Neo4jConfigUpdate | None = None
    reset_postgres: bool = False
    reset_neo4j: bool = False


class PostgresConfigRead(BaseModel):
    host: str
    port: int
    user: str
    database: str
    sslmode: str | None = None
    db_schema: str | None = Field(default=None, alias="schema")
    has_password: bool = False

    model_config = ConfigDict(populate_by_name=True)


class Neo4jConfigRead(BaseModel):
    uri: str
    user: str
    has_password: bool = False


class ProjectConfigRead(BaseModel):
    project_id: str
    postgres: PostgresConfigRead | None = None
    neo4j: Neo4jConfigRead | None = None

    model_config = ConfigDict(from_attributes=True)
