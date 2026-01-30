"""
Project context utilities.

Provides helpers for resolving project identifiers from headers and mapping
them to PostgreSQL schemas.
"""

from __future__ import annotations

import re

PROJECT_HEADER = "X-Project-Id"
DEFAULT_PROJECT_ID = "default"
DEFAULT_POSTGRES_SCHEMA = "public"

_PROJECT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def normalize_project_id(value: str) -> str:
    return value.strip().lower()


def resolve_project_id(value: str | None) -> str:
    if not value:
        return DEFAULT_PROJECT_ID
    project_id = normalize_project_id(value)
    if not project_id:
        return DEFAULT_PROJECT_ID
    if not _PROJECT_ID_PATTERN.match(project_id):
        raise ValueError("Invalid project id")
    return project_id


def postgres_schema_for(project_id: str) -> str:
    if project_id == DEFAULT_PROJECT_ID:
        return DEFAULT_POSTGRES_SCHEMA
    return f"project_{project_id}"


def quote_postgres_identifier(identifier: str) -> str:
    escaped = identifier.replace('"', '""')
    return f"\"{escaped}\""
