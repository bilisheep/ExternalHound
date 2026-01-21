"""
Import service for parser plugins.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Iterable
from time import monotonic
from uuid import UUID
from uuid import uuid4

from fastapi import UploadFile
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.parsers.base import ParseResult, ParserContext, PluginManifest
from app.parsers.registry import default_registry
from app.repositories.assets.certificate import CertificateRepository
from app.repositories.assets.client_application import ClientApplicationRepository
from app.repositories.assets.credential import CredentialRepository
from app.repositories.assets.domain import DomainRepository
from app.repositories.assets.ip import IPRepository
from app.repositories.assets.netblock import NetblockRepository
from app.repositories.assets.organization import OrganizationRepository
from app.repositories.assets.service import ServiceRepository
from app.repositories.imports.import_log import ImportLogRepository
from app.repositories.relationships.relationship import RelationshipRepository
from app.schemas.assets.certificate import CertificateCreate, CertificateUpdate
from app.schemas.assets.client_application import (
    ClientApplicationCreate,
    ClientApplicationUpdate,
)
from app.schemas.assets.credential import CredentialCreate, CredentialUpdate
from app.schemas.assets.domain import DomainCreate, DomainUpdate
from app.schemas.assets.ip import IPCreate, IPUpdate
from app.schemas.assets.netblock import NetblockCreate, NetblockUpdate
from app.schemas.assets.organization import OrganizationCreate, OrganizationUpdate
from app.schemas.assets.service import ServiceCreate, ServiceUpdate
from app.schemas.relationships.relationship import RelationshipCreate
from app.utils.external_id import (
    generate_certificate_external_id,
    generate_client_application_external_id,
    generate_credential_external_id,
    generate_domain_external_id,
    generate_ip_external_id,
    generate_netblock_external_id,
    generate_organization_external_id,
    generate_service_external_id,
)

logger = logging.getLogger(__name__)


class ImportService:
    """Handle file upload, parsing, and persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.import_repo = ImportLogRepository(db)
        self.relationship_repo = RelationshipRepository(db)
        self.asset_repos = {
            "organizations": (OrganizationRepository(db), OrganizationCreate, OrganizationUpdate),
            "netblocks": (NetblockRepository(db), NetblockCreate, NetblockUpdate),
            "domains": (DomainRepository(db), DomainCreate, DomainUpdate),
            "ips": (IPRepository(db), IPCreate, IPUpdate),
            "certificates": (CertificateRepository(db), CertificateCreate, CertificateUpdate),
            "services": (ServiceRepository(db), ServiceCreate, ServiceUpdate),
            "applications": (
                ClientApplicationRepository(db),
                ClientApplicationCreate,
                ClientApplicationUpdate,
            ),
            "credentials": (CredentialRepository(db), CredentialCreate, CredentialUpdate),
        }

    async def list_plugins(self) -> list[PluginManifest]:
        return default_registry.discover()

    async def list_imports(
        self,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ):
        return await self.import_repo.list_all(
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )

    async def get_import(self, import_id: UUID):
        return await self.import_repo.get_by_id(import_id)

    async def delete_import_file(self, import_id: UUID) -> bool:
        record = await self.import_repo.get_by_id(import_id)
        if not record:
            return False
        if record.file_path:
            path = Path(record.file_path)
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Failed to delete file: %s", path)
        await self.import_repo.update(
            import_id,
            status="DELETED",
            file_path=None,
        )
        return True

    async def import_file(
        self,
        file: UploadFile,
        parser_name: str | None = None,
        created_by: str | None = None,
    ):
        upload_path = await self._save_upload_file(file)
        file_hash = self._hash_file(upload_path)

        log = await self.import_repo.create(
            filename=file.filename or upload_path.name,
            file_size=upload_path.stat().st_size,
            file_hash=file_hash,
            file_path=str(upload_path),
            format=parser_name or "auto",
            status="PROCESSING",
            progress=0,
            created_by=created_by,
        )

        try:
            start_time = monotonic()
            default_registry.discover()
            parser_cls = default_registry.select_parser(upload_path, parser_name=parser_name)
            manifest = parser_cls.manifest
            context = ParserContext(
                import_id=str(log.id),
                created_by=created_by,
                source=manifest.name if manifest else parser_name,
            )
            parser = parser_cls(upload_path, context=context)
            parse_result = parser.parse()
            stats = await self._persist_result(parse_result)
            duration = int(monotonic() - start_time)
            update_payload = {
                "status": "SUCCESS",
                "progress": 100,
                "format": manifest.name if manifest else (parser_name or log.format),
                "parser_version": manifest.version if manifest else None,
                "records_total": parse_result.total_records,
                "records_success": parse_result.success_count,
                "records_failed": parse_result.failed_count,
                "error_details": parse_result.errors or None,
                "assets_created": stats,
                "duration_seconds": duration,
            }
            if parse_result.failed_count == 0 and stats.get("total_failed", 0) == 0:
                try:
                    upload_path.unlink(missing_ok=True)
                    update_payload["file_path"] = None
                except OSError:
                    logger.warning("Failed to auto-delete file: %s", upload_path)

            await self.import_repo.update(
                log.id,
                **update_payload,
            )
            return await self.import_repo.get_by_id(log.id)
        except Exception as exc:
            await self.import_repo.update(
                log.id,
                status="FAILED",
                error_message=str(exc),
            )
            raise

    async def _persist_result(self, result: ParseResult) -> dict[str, Any]:
        stats: dict[str, Any] = {}
        total_created = 0
        total_updated = 0
        total_failed = 0

        for key, config in self.asset_repos.items():
            items = getattr(result, key, [])
            if not items:
                continue
            created, updated, failed = await self._upsert_assets(key, items, config)
            stats[f"{key}_created"] = created
            stats[f"{key}_updated"] = updated
            stats[f"{key}_failed"] = failed
            total_created += created
            total_updated += updated
            total_failed += failed

        rel_created, rel_updated, rel_failed = await self._upsert_relationships(
            result.relationships
        )
        stats["relationships_created"] = rel_created
        stats["relationships_updated"] = rel_updated
        stats["relationships_failed"] = rel_failed

        stats["total_created"] = total_created + rel_created
        stats["total_updated"] = total_updated + rel_updated
        stats["total_failed"] = total_failed + rel_failed
        return stats

    async def _upsert_assets(
        self,
        asset_type: str,
        items: Iterable[dict[str, Any]],
        config: tuple[Any, Any, Any],
    ) -> tuple[int, int, int]:
        repo, create_schema, update_schema = config
        created = updated = failed = 0
        for item in items:
            try:
                payload = dict(item)
                self._ensure_external_id(asset_type, payload)
                create_model = create_schema(**payload)
                data = create_model.model_dump(exclude_none=True)
                external_id = data.get("external_id")
                if not external_id:
                    raise ValueError("external_id missing")
                existing = await repo.get_by_external_id(external_id)
                if existing:
                    update_data = {
                        key: value
                        for key, value in data.items()
                        if key in update_schema.model_fields
                    }
                    if "metadata_" in update_data:
                        update_data["metadata_"] = {
                            **(existing.metadata_ or {}),
                            **update_data["metadata_"],
                        }
                    await repo.update(existing.id, **update_data)
                    updated += 1
                else:
                    await repo.create(**data)
                    created += 1
            except (ValidationError, ValueError, KeyError, TypeError) as exc:
                logger.warning("Failed to upsert %s: %s", asset_type, exc)
                failed += 1
        return created, updated, failed

    async def _upsert_relationships(
        self,
        relationships: Iterable[dict[str, Any]],
    ) -> tuple[int, int, int]:
        created = updated = failed = 0
        for rel in relationships:
            try:
                payload = RelationshipCreate(**rel).model_dump(exclude_none=True, mode="json")
                existing = await self.relationship_repo.get_by_key(
                    source_external_id=payload["source_external_id"],
                    source_type=payload["source_type"],
                    target_external_id=payload["target_external_id"],
                    target_type=payload["target_type"],
                    relation_type=payload["relation_type"],
                    edge_key=payload["edge_key"],
                )
                if existing:
                    merged = {**(existing.properties or {}), **payload.get("properties", {})}
                    await self.relationship_repo.update_properties(existing.id, merged)
                    updated += 1
                else:
                    await self.relationship_repo.create(
                        source_external_id=payload["source_external_id"],
                        source_type=payload["source_type"],
                        target_external_id=payload["target_external_id"],
                        target_type=payload["target_type"],
                        relation_type=payload["relation_type"],
                        edge_key=payload["edge_key"],
                        properties=payload.get("properties", {}),
                        created_by=payload.get("created_by"),
                    )
                    created += 1
            except ValidationError as exc:
                logger.warning("Failed to upsert relationship: %s", exc)
                failed += 1
        return created, updated, failed

    async def _save_upload_file(self, file: UploadFile) -> Path:
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename or "").suffix
        target = upload_dir / f"{uuid4().hex}{suffix}"
        with target.open("wb") as handle:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
        return target

    def _hash_file(self, path: Path) -> str:
        sha256 = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _ensure_external_id(self, asset_type: str, payload: dict[str, Any]) -> None:
        if payload.get("external_id"):
            return
        if asset_type == "ips":
            payload["external_id"] = generate_ip_external_id(payload["address"])
        elif asset_type == "domains":
            payload["external_id"] = generate_domain_external_id(payload["name"])
        elif asset_type == "netblocks":
            payload["external_id"] = generate_netblock_external_id(payload["cidr"])
        elif asset_type == "organizations":
            payload["external_id"] = generate_organization_external_id(
                payload.get("name"),
                payload.get("credit_code"),
            )
        elif asset_type == "services":
            metadata = payload.get("metadata") or payload.get("metadata_")
            payload["external_id"] = generate_service_external_id(
                port=payload["port"],
                protocol=payload.get("protocol"),
                service_name=payload.get("service_name"),
                product=payload.get("product"),
                metadata=metadata,
            )
        elif asset_type == "certificates":
            metadata = payload.get("metadata") or payload.get("metadata_")
            payload["external_id"] = generate_certificate_external_id(
                metadata=metadata,
                subject_cn=payload.get("subject_cn"),
                issuer_cn=payload.get("issuer_cn"),
                issuer_org=payload.get("issuer_org"),
                valid_from=payload.get("valid_from"),
                valid_to=payload.get("valid_to"),
            )
        elif asset_type == "applications":
            payload["external_id"] = generate_client_application_external_id(
                payload["platform"],
                payload["package_name"],
            )
        elif asset_type == "credentials":
            payload["external_id"] = generate_credential_external_id(
                payload["cred_type"],
                payload.get("provider"),
                payload.get("username"),
                payload.get("email"),
                payload.get("phone"),
                payload.get("content"),
            )
