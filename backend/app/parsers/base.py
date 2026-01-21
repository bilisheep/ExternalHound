"""
Parser base classes and shared models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class PluginManifest:
    """Plugin manifest metadata loaded from plugin.toml."""

    name: str
    version: str
    entrypoint: str
    supported_formats: list[str]
    priority: int = 100
    description: str | None = None
    vendor: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any], source: Path) -> "PluginManifest":
        name = str(data.get("name") or "").strip()
        version = str(data.get("version") or "").strip()
        entrypoint = str(data.get("entrypoint") or "").strip()
        supported = data.get("supported_formats") or []
        if isinstance(supported, str):
            supported = [supported]
        supported_formats = [str(item).strip() for item in supported if str(item).strip()]
        if not name or not version or not entrypoint or not supported_formats:
            raise ValueError(f"Invalid plugin manifest in {source}: missing fields")
        priority = int(data.get("priority") or 100)
        description = data.get("description")
        vendor = data.get("vendor")
        return cls(
            name=name,
            version=version,
            entrypoint=entrypoint,
            supported_formats=supported_formats,
            priority=priority,
            description=description,
            vendor=vendor,
        )


class ParserContext(BaseModel):
    """Context information passed to parsers."""

    import_id: str | None = None
    organization_id: str | None = None
    created_by: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParseResult(BaseModel):
    """Unified parser output."""

    organizations: list[dict[str, Any]] = Field(default_factory=list)
    netblocks: list[dict[str, Any]] = Field(default_factory=list)
    domains: list[dict[str, Any]] = Field(default_factory=list)
    ips: list[dict[str, Any]] = Field(default_factory=list)
    certificates: list[dict[str, Any]] = Field(default_factory=list)
    services: list[dict[str, Any]] = Field(default_factory=list)
    applications: list[dict[str, Any]] = Field(default_factory=list)
    credentials: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)

    total_records: int = 0
    success_count: int = 0
    failed_count: int = 0
    errors: list[dict[str, Any]] = Field(default_factory=list)

    def add_error(
        self,
        record_id: str,
        message: str,
        parser: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {"record_id": record_id, "error": message}
        if parser:
            payload["parser"] = parser
        if details:
            payload["details"] = details
        self.errors.append(payload)


class BaseParser(ABC):
    """Base parser interface for plugins."""

    manifest: PluginManifest | None = None

    def __init__(
        self,
        file_path: str | Path,
        context: ParserContext | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self.context = context or ParserContext()

    @classmethod
    def supports_format(cls, format_name: str) -> bool:
        if not cls.manifest:
            return False
        return format_name.lower() in {
            fmt.lower() for fmt in cls.manifest.supported_formats
        }

    @classmethod
    def probe(cls, file_path: Path) -> bool:
        """Lightweight sniffing to decide if parser can handle the input."""
        return False

    @abstractmethod
    def parse(self) -> ParseResult:
        """Parse the input file and return a unified result."""
        raise NotImplementedError
